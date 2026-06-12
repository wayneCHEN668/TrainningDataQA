import { describe, it, expect, beforeEach } from "vitest";
import { useChatStore } from "./chatStore";

describe("chatStore", () => {
  beforeEach(() => {
    useChatStore.getState().clearCurrentSession();
  });

  it("starts with empty state", () => {
    const state = useChatStore.getState();
    expect(state.messages).toHaveLength(0);
    expect(state.status).toBe("idle");
    expect(state.currentSteps).toHaveLength(0);
  });

  it("adds messages correctly", () => {
    const store = useChatStore.getState();
    store.addMessage({ id: "1", role: "user", content: "hello", timestamp: 1000 });
    store.addMessage({ id: "2", role: "ai", content: "", timestamp: 2000 });
    expect(useChatStore.getState().messages).toHaveLength(2);
  });

  it("updates last AI message", () => {
    const store = useChatStore.getState();
    store.addMessage({ id: "1", role: "user", content: "q", timestamp: 1000 });
    store.addMessage({ id: "2", role: "ai", content: "", timestamp: 2000 });
    store.updateLastAiMessage((msg) => ({ ...msg, content: "answer" }));
    const msgs = useChatStore.getState().messages;
    expect(msgs[1].content).toBe("answer");
  });

  it("tracks thinking steps", () => {
    const store = useChatStore.getState();
    store.addStep({ stepNo: 1, thought: "", action: "test", paramsSummary: "", status: "running" });
    store.updateStep(1, { status: "done", resultSummary: "ok" });
    const steps = useChatStore.getState().currentSteps;
    expect(steps[0].status).toBe("done");
  });

  it("toggles reasoning panel", () => {
    const store = useChatStore.getState();
    expect(store.reasoningPanelVisible).toBe(true);
    store.toggleReasoningPanel();
    expect(useChatStore.getState().reasoningPanelVisible).toBe(false);
  });

  it("clears session", () => {
    const store = useChatStore.getState();
    store.addMessage({ id: "1", role: "user", content: "test", timestamp: 1000 });
    store.clearCurrentSession();
    expect(useChatStore.getState().messages).toHaveLength(0);
  });
});
