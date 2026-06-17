import type { Message, ClarificationOption } from "../../types/chat";
import { ClarificationOptions } from "./ClarificationOptions";
import { FileSpreadsheet } from "lucide-react";
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
const CHART_PLACEHOLDER_RE = /^\s*!\[([^\]]*)\]\(chart_[a-zA-Z0-9][a-zA-Z0-9_]*\)\s*$/gm;

/** Patterns that indicate system error text leaking into the answer. */
const ERROR_PATTERNS = [
  /\d+\s+validation errors?\b/i,
  /\bField required\b/i,
  /\bFor further information visit\b/i,
  /\bError executing tool\b/i,
  /\bError: invalid JSON\b/i,
  /\bError: tool\b/i,
  /\[type=missing/i,
  /input_type=dict/i,
];

/** Patterns that indicate LLM internal reasoning (not meant for users). */
const REASONING_PATTERNS = [
  /首先构造合并数据/,
  /手动合并[:：]/,
  /然后生成图表/,
  /将两个查询结果的data按日期合并/,
];

/** Strip ReAct format artifacts, error messages, and LLM reasoning from content.
 *
 *  The backend should not send ReAct trace (Thought/Action/Action Input/
 *  Observation) as answer_chunk events — only the Final Answer text is
 *  streamed.  This function is a safety net in case any trace slips through.
 */
function cleanReactArtifacts(content: string): string {
  // If "Final Answer:" marker is present, keep only the answer AFTER it.
  const faMatch = content.match(/(?:^|\n)\s*Final Answer:\s*/im);
  if (faMatch && faMatch.index !== undefined) {
    content = content.slice(faMatch.index + faMatch[0].length);
  }
  // Strip ReAct marker lines that have content after them
  // e.g. "Thought: 我需要查询..." → ""
  content = content
    .replace(/^\s*(Thought|Action|Action Input|Observation):[^\n]*/gim, "")
    .replace(/\n{3,}/g, "\n\n")
    .trim();

  // If the remaining content looks like an error message, suppress it entirely
  if (ERROR_PATTERNS.some((p) => p.test(content))) {
    // Try to salvage: remove lines matching error patterns
    const lines = content.split("\n").filter((line) => {
      return !ERROR_PATTERNS.some((p) => p.test(line));
    });
    content = lines.join("\n").trim();
    // If everything was error lines, return empty
    if (content.length < 10) return "";
  }

  // Strip LLM reasoning fragments that leaked through
  for (const p of REASONING_PATTERNS) {
    if (p.test(content)) {
      // Remove the reasoning sentence(s) — typically at the beginning
      content = content.replace(/^[^。\n]*?(?:构造|合并|手动|生成图表)[^。\n]*[。\n]\s*/gm, "");
    }
  }

  return content.replace(/\n{3,}/g, "\n\n").trim();
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

        {/* 报表统计摘要卡片 */}
        {message.role === "ai" && message.downloads && message.downloads.length > 0 && (
          <div className="mt-3 space-y-2">
            {message.downloads.map((dl, i) => (
              <div
                key={i}
                className="p-3 bg-bg-card rounded-lg border border-border"
              >
                <div className="flex items-center gap-2 text-sm">
                  <FileSpreadsheet size={16} className="text-accent" />
                  <span className="font-medium text-text-primary">{dl.fileName}</span>
                </div>
                <div className="mt-2 grid grid-cols-3 gap-2 text-xs text-text-subdued">
                  <div>
                    <span className="block text-text-secondary font-medium">
                      {dl.totalRows.toLocaleString()}
                    </span>
                    <span>总行数</span>
                  </div>
                  <div>
                    <span className="block text-text-secondary font-medium">
                      {dl.totalColumns}
                    </span>
                    <span>总列数</span>
                  </div>
                  <div>
                    <span className="block text-text-secondary font-medium">
                      {dl.fileSize < 1024
                        ? `${dl.fileSize} B`
                        : dl.fileSize < 1048576
                          ? `${(dl.fileSize / 1024).toFixed(1)} KB`
                          : `${(dl.fileSize / 1048576).toFixed(1)} MB`}
                    </span>
                    <span>文件大小</span>
                  </div>
                </div>
                <div className="mt-1.5 text-xs text-text-subdued">
                  {dl.sheets.map((s) => `${s.name}(${s.rows}行×${s.columns}列)`).join(" · ")}
                </div>
              </div>
            ))}
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