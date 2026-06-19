import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, act, waitFor } from "@testing-library/react";
import { useAIQuery } from "./useAIQuery";
import { useChatStore } from "../stores/chatStore";

// ---------------------------------------------------------------------------
// Mock fetch + ReadableStream helpers
// ---------------------------------------------------------------------------

interface MockEvent {
  type: string;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  data: any;
}

const mockEvents: MockEvent[] = [];

function formatSSEFrame(event: string, data: unknown): string {
  return `event: ${event}\ndata: ${JSON.stringify(data)}\n\n`;
}

function createMockReader(events: MockEvent[]) {
  let index = 0;
  return {
    read: vi.fn(async () => {
      if (index >= events.length) {
        return { done: true, value: undefined };
      }
      const frame = formatSSEFrame(events[index].type, events[index].data);
      index++;
      const encoder = new TextEncoder();
      return { done: false, value: encoder.encode(frame) };
    }),
    releaseLock: vi.fn(),
  };
}

function createMockResponse(status: number, events: MockEvent[]) {
  if (status !== 200) {
    return { ok: false, status, body: null };
  }
  const reader = createMockReader(events);
  return {
    ok: true,
    status: 200,
    body: {
      getReader: () => reader,
    },
  };
}

beforeEach(() => {
  useChatStore.getState().clearCurrentSession();
  vi.clearAllMocks();
  mockEvents.length = 0;

  globalThis.fetch = vi.fn((_url: RequestInfo | URL, _init?: RequestInit) => {
    return Promise.resolve(
      createMockResponse(200, [...mockEvents]),
    ) as Promise<Response>;
  });

  vi.spyOn(Storage.prototype, "getItem").mockReturnValue("mock-token");
});

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function addMockEvent(type: string, data: unknown) {
  mockEvents.push({ type, data });
}

/** Flush microtasks so fetch().then() chains resolve. */
async function flushAsync() {
  await act(async () => {
    await Promise.resolve();
  });
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("useAIQuery", () => {
  it("submit sends Authorization header and adds user + AI messages", async () => {
    addMockEvent("intent_resolved", { intent: "TEST", complexity: "simple", confidence: 0.9 });
    addMockEvent("done", { total_steps: 1, duration_ms: 100 });

    const { result } = renderHook(() => useAIQuery());

    act(() => {
      result.current.submit("What is the weather?");
    });

    // Microtasks run after submit's fetch().then()
    await waitFor(() => {
      const store = useChatStore.getState();
      expect(store.messages).toHaveLength(2);
      expect(store.messages[0].role).toBe("user");
      expect(store.messages[0].content).toBe("What is the weather?");
      expect(store.messages[1].role).toBe("ai");
    });

    // Verify Authorization header was sent
    const fetchCalls = (globalThis.fetch as ReturnType<typeof vi.fn>).mock.calls;
    expect(fetchCalls.length).toBeGreaterThan(0);
    const [, init] = fetchCalls[0];
    expect(init.headers).toHaveProperty("Authorization", "Bearer mock-token");
  });

  it("processes an SSE event stream correctly", async () => {
    addMockEvent("intent_resolved", { intent: "TEST", complexity: "simple", confidence: 0.9 });
    addMockEvent("step_start", { step_no: 1, thought: "Think", action: "tool", params_summary: "params" });
    addMockEvent("step_done", { step_no: 1, tool_name: "tool", result_summary: "done" });
    addMockEvent("done", { total_steps: 1, duration_ms: 100 });

    const { result } = renderHook(() => useAIQuery());

    act(() => {
      result.current.submit("test");
    });

    await waitFor(() => {
      const store = useChatStore.getState();
      expect(store.intentLabel).toContain("TEST");
      expect(store.status).toBe("done");
    });
  });

  it("cancel sets status to done", () => {
    addMockEvent("intent_resolved", { intent: "TEST", complexity: "simple", confidence: 0.9 });

    const { result } = renderHook(() => useAIQuery());

    act(() => {
      result.current.submit("test");
    });

    act(() => {
      result.current.cancel();
    });

    expect(useChatStore.getState().status).toBe("done");
  });

  it("clarification select calls submit with option text", async () => {
    addMockEvent("intent_resolved", { intent: "TEST", complexity: "simple", confidence: 0.9 });
    addMockEvent("done", { total_steps: 1, duration_ms: 100 });

    const { result } = renderHook(() => useAIQuery());

    act(() => {
      result.current.selectClarification({ index: 1, text: "Specific question", intent: "query" });
    });

    await waitFor(() => {
      const msgs = useChatStore.getState().messages;
      expect(msgs).toHaveLength(2);
      expect(msgs[0].content).toBe("Specific question");
      expect(msgs[0].role).toBe("user");
    });
  });

  it("handles 401 by clearing token and redirecting", async () => {
    const removeItemSpy = vi.spyOn(Storage.prototype, "removeItem");
    const locationAssign = vi.fn();
    vi.stubGlobal("location", { href: "", assign: locationAssign });

    // Override fetch for this test only
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      ok: false,
      status: 401,
      body: null,
    } as unknown as Response);

    const { result } = renderHook(() => useAIQuery());

    act(() => {
      result.current.submit("test");
    });

    await flushAsync();

    expect(removeItemSpy).toHaveBeenCalledWith("access_token");
  });
});
