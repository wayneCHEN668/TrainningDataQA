import { Copy, ThumbsUp, ThumbsDown, XCircle, Check } from "lucide-react";
import { useState, useCallback, useEffect } from "react";
import type { FeedbackType } from "../../types/chat";

interface MessageActionsProps {
  content: string;
  onFeedback: (type: FeedbackType) => void;
}

export function MessageActions({ content, onFeedback }: MessageActionsProps) {
  const [selectedFeedback, setSelectedFeedback] = useState<FeedbackType | null>(null);
  const [copied, setCopied] = useState(false);

  const handleCopy = useCallback(async () => {
    try {
      // Strip common markdown syntax to get plain text
      const plainText = content
        .replace(/\*\*(.+?)\*\*/g, "$1")        // bold
        .replace(/\*(.+?)\*/g, "$1")             // italic
        .replace(/`(.+?)`/g, "$1")               // inline code
        .replace(/\[([^\]]+)\]\([^)]+\)/g, "$1") // links: [text](url)
        .replace(/^#{1,6}\s+/gm, "")             // headings
        .replace(/^>\s?/gm, "")                  // blockquotes
        .replace(/^---+\s*$/gm, "")              // horizontal rules
        .replace(/^\s*[\-*+]\s+/gm, "• ")        // unordered lists
        .replace(/\n{3,}/g, "\n\n")              // collapse extra blank lines
        .trim();
      await navigator.clipboard.writeText(plainText);
      setCopied(true);
    } catch {
      // Fallback: copy raw content
      await navigator.clipboard.writeText(content);
      setCopied(true);
    }
  }, [content]);

  // Reset copied icon after 1.5s
  useEffect(() => {
    if (!copied) return;
    const timer = setTimeout(() => setCopied(false), 1500);
    return () => clearTimeout(timer);
  }, [copied]);

  const handleFeedback = (type: FeedbackType) => {
    if (selectedFeedback === type) {
      // Toggle off — don't fire callback (no new feedback)
      setSelectedFeedback(null);
    } else {
      setSelectedFeedback(type);
      onFeedback(type);
    }
  };

  const btnBase =
    "p-1 rounded-md transition-colors cursor-pointer";

  return (
    <div className="flex items-center gap-0.5">
      {/* Copy */}
      <button
        type="button"
        onClick={handleCopy}
        className={`${btnBase} ${
          copied ? "text-[#1ed760]" : "text-text-subdued hover:text-text-secondary"
        }`}
        title="复制"
        aria-label="复制回答"
      >
        {copied ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
      </button>

      {/* Like */}
      <button
        type="button"
        onClick={() => handleFeedback("like")}
        className={`${btnBase} ${
          selectedFeedback === "like"
            ? "text-[#1ed760]"
            : "text-text-subdued hover:text-text-secondary"
        }`}
        title="有帮助"
        aria-label="有帮助"
      >
        <ThumbsUp className="w-3.5 h-3.5" />
      </button>

      {/* Dislike */}
      <button
        type="button"
        onClick={() => handleFeedback("dislike")}
        className={`${btnBase} ${
          selectedFeedback === "dislike"
            ? "text-error"
            : "text-text-subdued hover:text-text-secondary"
        }`}
        title="不够好"
        aria-label="不够好"
      >
        <ThumbsDown className="w-3.5 h-3.5" />
      </button>

      {/* Wrong */}
      <button
        type="button"
        onClick={() => handleFeedback("wrong")}
        className={`${btnBase} ${
          selectedFeedback === "wrong"
            ? "text-error"
            : "text-text-subdued hover:text-text-secondary"
        }`}
        title="完全错误"
        aria-label="完全错误"
      >
        <XCircle className="w-3.5 h-3.5" />
      </button>
    </div>
  );
}
