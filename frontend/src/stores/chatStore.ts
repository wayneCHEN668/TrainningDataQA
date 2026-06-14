import { create } from "zustand";
import type { Message, ThinkingStep, ChartSpec, ChatStatus } from "../types/chat";

export interface Round {
  question: string;
  steps: ThinkingStep[];
  charts: ChartSpec[];
  intentLabel: string;
}

interface ChatState {
  messages: Message[];
  status: ChatStatus;
  currentSteps: ThinkingStep[];
  currentCharts: ChartSpec[];
  intentLabel: string;
  reasoningPanelVisible: boolean;
  error: string | null;
  rounds: Round[];
  lastSessionId: string;

  addMessage: (msg: Message) => void;
  updateLastAiMessage: (updater: (msg: Message) => Message) => void;
  addStep: (step: ThinkingStep) => void;
  updateStep: (stepNo: number, updater: Partial<ThinkingStep>) => void;
  addChart: (chart: ChartSpec) => void;
  setStatus: (status: ChatStatus) => void;
  setIntentLabel: (label: string) => void;
  setError: (error: string) => void;
  toggleReasoningPanel: () => void;
  clearCurrentSession: () => void;
  setLastSessionId: (id: string) => void;
  prepareNewRound: (question: string) => void;
  finalizeRound: () => void;
}

export const useChatStore = create<ChatState>((set, get) => ({
  messages: [],
  status: "idle",
  currentSteps: [],
  currentCharts: [],
  intentLabel: "",
  reasoningPanelVisible: true,
  error: null,
  rounds: [],
  lastSessionId: "",

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

  setError: (error) => set({ error, status: "error" }),

  setLastSessionId: (id) => set({ lastSessionId: id }),

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
      rounds: [],
    }),

  prepareNewRound: (_question: string) => {
    const state = get();
    // Archive the previous round if there are steps
    if (state.currentSteps.length > 0) {
      const lastUser = [...state.messages].reverse().find((m) => m.role === "user");
      const archivedRound: Round = {
        question: lastUser?.content ?? "",
        steps: state.currentSteps,
        charts: state.currentCharts,
        intentLabel: state.intentLabel,
      };
      set({
        rounds: [...state.rounds, archivedRound],
        currentSteps: [],
        currentCharts: [],
        intentLabel: "",
        status: "idle",
        error: null,
      });
    } else {
      set({
        currentSteps: [],
        currentCharts: [],
        intentLabel: "",
        status: "idle",
        error: null,
      });
    }
  },

  finalizeRound: () => {
    const state = get();
    const lastUser = [...state.messages].reverse().find((m) => m.role === "user");
    const round: Round = {
      question: lastUser?.content ?? "",
      steps: state.currentSteps,
      charts: state.currentCharts,
      intentLabel: state.intentLabel,
    };
    // Also save steps to the last AI message
    const messages = [...state.messages];
    const lastAiIdx = messages.length - 1;
    if (lastAiIdx >= 0 && messages[lastAiIdx].role === "ai") {
      messages[lastAiIdx] = {
        ...messages[lastAiIdx],
        steps: state.currentSteps,
        charts: state.currentCharts,
      };
    }
    set({
      messages,
      rounds: [...state.rounds, round],
      // Clear current round data to avoid duplicate display in ReasoningPanel
      currentSteps: [],
      currentCharts: [],
      intentLabel: "",
    });
  },
}));
