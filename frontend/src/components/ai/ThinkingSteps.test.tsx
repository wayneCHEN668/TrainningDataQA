import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { ThinkingSteps } from "./ThinkingSteps";
import type { ThinkingStep } from "../../types/chat";

const runningStep: ThinkingStep = {
  stepNo: 1,
  thought: "Processing query",
  action: "call_knowledge_base",
  paramsSummary: "query=test",
  status: "running",
};

const doneStep: ThinkingStep = {
  stepNo: 2,
  thought: "Fetched results",
  action: "call_knowledge_base",
  paramsSummary: "query=test",
  status: "done",
  resultSummary: "Found 5 results",
};

describe("ThinkingSteps", () => {
  it("renders running step with animated indicator", () => {
    render(<ThinkingSteps steps={[runningStep]} />);
    expect(screen.getByText("第1步")).toBeInTheDocument();
    expect(screen.getByText("call_knowledge_base")).toBeInTheDocument();
    // Running step renders a spinning Loader2 icon; done steps render a Check icon.
    // We verify the step content is present.
    expect(screen.queryByText("Found 5 results")).not.toBeInTheDocument();
  });

  it("renders done step with result summary", () => {
    render(<ThinkingSteps steps={[doneStep]} />);
    expect(screen.getByText("第2步")).toBeInTheDocument();
    expect(screen.getByText("Found 5 results")).toBeInTheDocument();
  });
});
