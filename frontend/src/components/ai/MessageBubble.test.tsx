import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { MessageBubble } from "./MessageBubble";
import type { Message } from "../../types/chat";

const userMessage: Message = {
  id: "1",
  role: "user",
  content: "Hello, AI!",
  timestamp: Date.now(),
};

const aiMessage: Message = {
  id: "2",
  role: "ai",
  content: "Hello, human!",
  timestamp: Date.now(),
};

const aiMessageWithClarifications: Message = {
  id: "3",
  role: "ai",
  content: "",
  timestamp: Date.now(),
  clarificationOptions: [
    { index: 1, text: "Option A", intent: "intent_a" },
    { index: 2, text: "Option B", intent: "intent_b" },
  ],
};

describe("MessageBubble", () => {
  it("renders user message right-aligned", () => {
    const { container } = render(<MessageBubble message={userMessage} />);
    const bubbleWrapper = container.querySelector(".justify-end");
    expect(bubbleWrapper).toBeInTheDocument();
    expect(screen.getByText("Hello, AI!")).toBeInTheDocument();
  });

  it("renders AI message with avatar", () => {
    render(<MessageBubble message={aiMessage} />);
    expect(screen.getByText("Hello, human!")).toBeInTheDocument();
    expect(screen.getByText("AI")).toBeInTheDocument();
  });

  it("renders clarification options when present", () => {
    render(
      <MessageBubble
        message={aiMessageWithClarifications}
        onClarificationSelect={() => {}}
      />
    );
    expect(screen.getByText("Option A")).toBeInTheDocument();
    expect(screen.getByText("Option B")).toBeInTheDocument();
  });
});
