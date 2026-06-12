import { useMemo } from "react";

interface StreamingAnswerProps {
  content: string;
  isStreaming: boolean;
}

/**
 * Converts **bold** markers into <strong> tags.
 */
function parseBoldMarkers(text: string): (string | { bold: string })[] {
  const parts: (string | { bold: string })[] = [];
  const regex = /\*\*(.+?)\*\*/g;
  let lastIndex = 0;
  let match: RegExpExecArray | null;

  while ((match = regex.exec(text)) !== null) {
    if (match.index > lastIndex) {
      parts.push(text.slice(lastIndex, match.index));
    }
    parts.push({ bold: match[1] });
    lastIndex = match.index + match[0].length;
  }

  if (lastIndex < text.length) {
    parts.push(text.slice(lastIndex));
  }

  return parts;
}

export function StreamingAnswer({ content, isStreaming }: StreamingAnswerProps) {
  const parsed = useMemo(() => parseBoldMarkers(content), [content]);

  if (!content && !isStreaming) {
    return null;
  }

  return (
    <div className="text-sm leading-relaxed whitespace-pre-wrap break-words">
      {parsed.map((part, i) =>
        typeof part === "string" ? (
          <span key={i}>{part}</span>
        ) : (
          <strong key={i} className="font-semibold text-white">
            {part.bold}
          </strong>
        )
      )}
      {isStreaming && (
        <span className="inline-block w-2 h-4 bg-[#1ed760] ml-0.5 align-middle animate-pulse" />
      )}
    </div>
  );
}
