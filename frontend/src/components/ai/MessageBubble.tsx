import type { Message, ClarificationOption } from "../../types/chat";
import { ClarificationOptions } from "./ClarificationOptions";
import { MessageActions } from "./MessageActions";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface MessageBubbleProps {
  message: Message;
  onClarificationSelect?: (option: ClarificationOption) => void;
  onClarificationNone?: () => void;
  onFeedback?: (type: "like" | "dislike" | "wrong") => void;
  showFeedback?: boolean;
}

/**
 * Replace chart placeholder markdown with a styled text reference.
 * ![数据图表](chart_xxx) → 📊 数据图表（请查看右侧面板）
 * Charts are rendered in the ReasoningPanel instead.
 */
const CHART_PLACEHOLDER_RE = /^\s*!\[([^\]]*)\]\(chart_[a-zA-Z][a-zA-Z0-9_]*\)\s*$/gm;

/** Strip ReAct format artifacts and truncate at "Final Answer:" boundary. */
function cleanReactArtifacts(content: string): string {
  // Truncate everything from "Final Answer:" onward — the LLM already
  // streamed the natural-language answer before the ReAct marker.
  const faIdx = content.search(/(?:^|\n)\s*Final Answer:\s*/im);
  if (faIdx !== -1) {
    content = content.slice(0, faIdx);
  }
  return content
    .replace(/^\s*(Thought|Action|Observation):\s*$/gm, "")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}

function replaceChartPlaceholders(content: string): string {
  return content
    .replace(CHART_PLACEHOLDER_RE, (_match, alt: string) => {
      const label = alt || "数据图表";
      // Trailing newline terminates the blockquote so following text stays outside
      return `> 📊 **${label}**（请在右侧思考面板查看）\n`;
    })
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}

/** Render AI response markdown as HTML, with chart placeholders replaced by text references. */
function renderMarkdownContent(content: string): React.ReactNode {
  const processed = cleanReactArtifacts(replaceChartPlaceholders(content));
  return (
    <div className="markdown-body text-sm">
      <ReactMarkdown remarkPlugins={[remarkGfm]}>
        {processed}
      </ReactMarkdown>
    </div>
  );
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
            renderMarkdownContent(message.content)
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

        {/* Message actions (copy + feedback) */}
        {showFeedback && onFeedback && (
          <div className="mt-1 ml-1">
            <MessageActions
              content={message.content}
              onFeedback={onFeedback}
            />
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