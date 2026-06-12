import type { Message, ClarificationOption } from "../../types/chat";
import { ClarificationOptions } from "./ClarificationOptions";
import { FeedbackButtons } from "./FeedbackButtons";

interface MessageBubbleProps {
  message: Message;
  onClarificationSelect?: (option: ClarificationOption) => void;
  onClarificationNone?: () => void;
  onFeedback?: (positive: boolean) => void;
  showFeedback?: boolean;
}

export function MessageBubble({
  message,
  onClarificationSelect,
  onClarificationNone,
  onFeedback,
  showFeedback,
}: MessageBubbleProps) {
  if (message.role === "system") {
    return (
      <div className="flex justify-center py-2">
        <div className="text-text-secondary text-sm italic px-4 py-1 rounded-md bg-bg-surface">
          {message.content}
        </div>
      </div>
    );
  }

  const isUser = message.role === "user";
  const hasContent = message.content.length > 0;
  const hasClarifications =
    message.clarificationOptions && message.clarificationOptions.length > 0;

  return (
    <div
      className={`flex gap-3 mb-4 ${isUser ? "justify-end" : "justify-start"}`}
    >
      {/* AI Avatar */}
      {!isUser && (
        <div className="flex-shrink-0 w-7 h-7 rounded-full bg-[#1ed760] flex items-center justify-center text-xs font-bold text-black">
          AI
        </div>
      )}

      {/* Bubble content area */}
      <div className={`max-w-[75%] ${isUser ? "order-first" : ""}`}>
        <div
          className={`rounded-xl px-4 py-3 ${
            isUser
              ? "bg-bg-card text-text-primary rounded-br-sm"
              : "bg-bg-surface text-text-primary rounded-bl-sm"
          }`}
        >
          {hasContent ? (
            <p className="whitespace-pre-wrap break-words text-sm leading-relaxed">
              {message.content}
            </p>
          ) : (
            !hasClarifications && (
              <div className="flex items-center gap-1">
                <span className="w-1.5 h-1.5 bg-[#1ed760] rounded-full animate-pulse" />
                <span className="w-1.5 h-1.5 bg-[#1ed760] rounded-full animate-pulse [animation-delay:0.2s]" />
                <span className="w-1.5 h-1.5 bg-[#1ed760] rounded-full animate-pulse [animation-delay:0.4s]" />
              </div>
            )
          )}
        </div>

        {/* Clarification options */}
        {hasClarifications && onClarificationSelect && (
          <div className="mt-3">
            <ClarificationOptions
              options={message.clarificationOptions!}
              onSelect={onClarificationSelect}
              onNone={onClarificationNone}
            />
          </div>
        )}

        {/* Feedback buttons */}
        {showFeedback && onFeedback && (
          <div className="mt-1 ml-1">
            <FeedbackButtons onFeedback={onFeedback} />
          </div>
        )}

        {/* Timestamp */}
        <div
          className={`text-text-subdued text-xs mt-1 ${
            isUser ? "text-right mr-1" : "ml-1"
          }`}
        >
          {new Date(message.timestamp).toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit",
          })}
        </div>
      </div>
    </div>
  );
}
