import { useEffect, useRef } from "react";
import type { Message, ClarificationOption, FeedbackType } from "../../types/chat";
import { MessageBubble } from "./MessageBubble";

interface MessageListProps {
  messages: Message[];
  onClarificationSelect?: (option: ClarificationOption) => void;
  onClarificationNone?: () => void;
  onFeedback?: (messageId: string, question: string, answer: string, type: FeedbackType) => void;
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
            在下方输入问题开始对话。
          </p>
        </div>
      )}
      {messages.map((msg) => {
        // Find the preceding user message for this AI message
        const msgIndex = messages.indexOf(msg);
        const prevUser = messages
          .slice(0, msgIndex)
          .reverse()
          .find((m) => m.role === "user");
        return (
          <MessageBubble
            key={msg.id}
            message={msg}
            onClarificationSelect={onClarificationSelect}
            onClarificationNone={onClarificationNone}
            onFeedback={
              onFeedback && prevUser
                ? (type: FeedbackType) => onFeedback(msg.id, prevUser.content, msg.content, type)
                : undefined
            }
            showFeedback={msg.role === "ai" && msg.content.length > 0}
          />
        );
      })}
      <div ref={bottomRef} />
    </div>
  );
}
