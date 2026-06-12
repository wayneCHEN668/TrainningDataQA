import { useEffect, useRef } from "react";
import type { Message, ClarificationOption } from "../../types/chat";
import { MessageBubble } from "./MessageBubble";

interface MessageListProps {
  messages: Message[];
  onClarificationSelect?: (option: ClarificationOption) => void;
  onClarificationNone?: () => void;
  onFeedback?: (positive: boolean) => void;
}

export function MessageList({
  messages,
  onClarificationSelect,
  onClarificationNone,
  onFeedback,
}: MessageListProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div className="flex-1 overflow-y-auto px-4 py-4 space-y-0">
      {messages.length === 0 && (
        <div className="flex items-center justify-center h-full">
          <p className="text-text-secondary text-sm">
            Start a conversation by asking a question below.
          </p>
        </div>
      )}
      {messages.map((msg) => (
        <MessageBubble
          key={msg.id}
          message={msg}
          onClarificationSelect={onClarificationSelect}
          onClarificationNone={onClarificationNone}
          onFeedback={onFeedback}
          showFeedback={msg.role === "ai" && msg.content.length > 0}
        />
      ))}
      <div ref={bottomRef} />
    </div>
  );
}
