import { create } from "zustand";
import type { Message, ThinkingStep, ChartSpec, ChatStatus } from "../types/chat";

interface ChatState {
  messages: Message[];
  status: ChatStatus;
  currentSteps: ThinkingStep[];
  currentCharts: ChartSpec[];
  intentLabel: string;
  reasoningPanelVisible: boolean;
  error: string | null;

  addMessage: (msg: Message) => void;
  updateLastAiMessage: (updater: (msg: Message) => Message) => void;
  addStep: (step: ThinkingStep) => void;
  updateStep: (stepNo: number, updater: Partial<ThinkingStep>) => void;
  addChart: (chart: ChartSpec) => void;
  setStatus: (status: ChatStatus) => void;
  setIntentLabel: (label: string) => void;
  toggleReasoningPanel: () => void;
  clearCurrentSession: () => void;
}

export const useChatStore = create<ChatState>((set) => ({
  messages: [],
  status: "idle",
  currentSteps: [],
  currentCharts: [],
  intentLabel: "",
  reasoningPanelVisible: true,
  error: null,

  addMessage: (msg) =>
    set((state) => ({ messages: [...state.messages, msg] })),

  updateLastAiMessage: (updater) =>
    set((state) => {
      const messages = [...state.messages];
      const lastIdx = messages.length - 1;
      if (lastIdx >= 0 && messages[lastIdx].role === "ai") {
        messages[lastIdx] = updater(messages[lastIdx]);
      }
      return { messages };
    }),

  addStep: (step) =>
    set((state) => ({
      currentSteps: [...state.currentSteps, step],
    })),

  updateStep: (stepNo, updater) =>
    set((state) => ({
      currentSteps: state.currentSteps.map((s) =>
        s.stepNo === stepNo ? { ...s, ...updater } : s
      ),
    })),

  addChart: (chart) =>
    set((state) => ({
      currentCharts: [...state.currentCharts, chart],
    })),

  setStatus: (status) => set({ status }),

  setIntentLabel: (label) => set({ intentLabel: label }),

  toggleReasoningPanel: () =>
    set((state) => ({ reasoningPanelVisible: !state.reasoningPanelVisible })),

  clearCurrentSession: () =>
    set({
      messages: [],
      currentSteps: [],
      currentCharts: [],
      intentLabel: "",
      status: "idle",
      error: null,
    }),
}));
