import { ThumbsUp, ThumbsDown } from "lucide-react";
import { useState } from "react";

interface FeedbackButtonsProps {
  onFeedback: (positive: boolean) => void;
}

export function FeedbackButtons({ onFeedback }: FeedbackButtonsProps) {
  const [selected, setSelected] = useState<"up" | "down" | null>(null);

  const handleFeedback = (positive: boolean) => {
    const value = positive ? "up" : "down";
    setSelected((prev) => (prev === value ? null : value));
    onFeedback(positive);
  };

  return (
    <div className="flex items-center gap-1">
      <button
        type="button"
        onClick={() => handleFeedback(true)}
        className={`p-1 rounded-md transition-colors cursor-pointer ${
          selected === "up"
            ? "text-[#1ed760]"
            : "text-text-subdued hover:text-text-secondary"
        }`}
        aria-label="Thumbs up"
      >
        <ThumbsUp className="w-3.5 h-3.5" />
      </button>
      <button
        type="button"
        onClick={() => handleFeedback(false)}
        className={`p-1 rounded-md transition-colors cursor-pointer ${
          selected === "down"
            ? "text-error"
            : "text-text-subdued hover:text-text-secondary"
        }`}
        aria-label="Thumbs down"
      >
        <ThumbsDown className="w-3.5 h-3.5" />
      </button>
    </div>
  );
}
