export interface ThinkingStep {
  stepNo: number;
  thought: string;
  action: string;
  paramsSummary: string;
  status: "running" | "done";
  resultSummary?: string;
}

export interface ChartSpec {
  chartId: string;
  chartType: "bar" | "line" | "pie";
  rechartsSpec: Record<string, unknown>;
}

export interface ClarificationOption {
  index: number;        // 1 | 2 | 3
  text: string;
  intent: string;
}

export interface Message {
  id: string;
  role: "user" | "ai" | "system";
  content: string;
  timestamp: number;
  steps?: ThinkingStep[];
  charts?: ChartSpec[];
  clarificationOptions?: ClarificationOption[];
}

export type ChatStatus = "idle" | "thinking" | "streaming" | "done" | "error";
