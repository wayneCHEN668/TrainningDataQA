import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useAIQuery } from "./useAIQuery";
import { useChatStore } from "../stores/chatStore";

// Store mock EventSource instances
const mockInstances: MockEventSource[] = [];

class MockEventSource {
  url: string;
  onerror: ((this: EventSource, ev: Event) => unknown) | null = null;
  readyState: number = 0;
  withCredentials: boolean = false;
  private listeners: Map<string, Array<(e: MessageEvent) => void>> = new Map();

  static readonly CONNECTING = 0;
  static readonly OPEN = 1;
  static readonly CLOSED = 2;

  constructor(url: string) {
    this.url = url;
    mockInstances.push(this);
  }

  addEventListener(type: string, listener: (e: MessageEvent) => void) {
    if (!this.listeners.has(type)) this.listeners.set(type, []);
    this.listeners.get(type)!.push(listener);
  }

  close() {
    this.readyState = MockEventSource.CLOSED;
  }

  // Helper to simulate server events in tests
  _dispatch(type: string, data: unknown) {
    const evt = new MessageEvent(type, { data: JSON.stringify(data) });
    this.listeners.get(type)?.forEach((fn) => fn(evt));
  }
}

vi.stubGlobal("EventSource", MockEventSource);

describe("useAIQuery", () => {
  beforeEach(() => {
    useChatStore.getState().clearCurrentSession();
    vi.clearAllMocks();
    mockInstances.length = 0;
  });

  afterEach(() => {
    mockInstances.forEach((es) => {
      try { es.close(); } catch { /* already closed */ }
    });
    mockInstances.length = 0;
  });

  it("submit creates EventSource and adds user + AI messages", () => {
    const { result } = renderHook(() => useAIQuery());

    act(() => {
      result.current.submit("What is the weather?");
    });

    const store = useChatStore.getState();
    expect(store.messages).toHaveLength(2);
    expect(store.messages[0].role).toBe("user");
    expect(store.messages[0].content).toBe("What is the weather?");
    expect(store.messages[1].role).toBe("ai");
    expect(mockInstances.length).toBeGreaterThan(0);
  });

  it("cancel closes the EventSource and sets status to done", () => {
    const { result } = renderHook(() => useAIQuery());

    act(() => {
      result.current.submit("test");
    });

    act(() => {
      result.current.cancel();
    });

    expect(useChatStore.getState().status).toBe("done");
    expect(mockInstances[0].readyState).toBe(MockEventSource.CLOSED);
  });

  it("clarification select calls submit with option text", () => {
    const { result } = renderHook(() => useAIQuery());

    act(() => {
      result.current.selectClarification({ index: 1, text: "Specific question", intent: "query" });
    });

    const msgs = useChatStore.getState().messages;
    expect(msgs[0].content).toBe("Specific question");
    expect(msgs[0].role).toBe("user");
  });
});
