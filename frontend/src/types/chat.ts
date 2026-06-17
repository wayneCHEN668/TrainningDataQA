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
  title?: string;
  rechartsSpec: Record<string, unknown>;
}

export interface ClarificationOption {
  index: number;        // 1 | 2 | 3
  text: string;
  intent: string;
}

export interface SheetMeta {
  name: string;
  rows: number;
  columns: number;
}

export interface DownloadInfo {
  fileName: string;
  fileUrl: string;
  fileSize: number;
  sheets: SheetMeta[];
  totalRows: number;
  totalColumns: number;
}

export interface Message {
  id: string;
  role: "user" | "ai" | "system";
  content: string;
  timestamp: number;
  steps?: ThinkingStep[];
  charts?: ChartSpec[];
  downloads?: DownloadInfo[];       // 报表下载信息
  clarificationOptions?: ClarificationOption[];
}

export type ChatStatus = "idle" | "thinking" | "streaming" | "done" | "error";

export type FeedbackType = "like" | "dislike" | "wrong";
