import type { ClarificationOption } from "../../types/chat";

interface ClarificationOptionsProps {
  options: ClarificationOption[];
  onSelect: (option: ClarificationOption) => void;
  onNone?: () => void;
}

export function ClarificationOptions({
  options,
  onSelect,
  onNone,
}: ClarificationOptionsProps) {
  if (options.length === 0) return null;

  return (
    <div className="rounded-lg bg-bg-card border border-border p-3">
      <p className="text-text-secondary text-xs mb-2">
        Sorry, I didn&apos;t fully understand. Did you mean:
      </p>
      <div className="space-y-2">
        {options.map((opt) => (
          <button
            key={opt.index}
            type="button"
            onClick={() => onSelect(opt)}
            className="w-full text-left px-3 py-2 rounded-md bg-bg-surface border-l-2 border-[#1ed760] text-text-primary text-sm hover:bg-bg-hover transition-colors cursor-pointer"
          >
            <span className="font-mono text-xs text-[#1ed760] mr-2">
              [{opt.index}]
            </span>
            {opt.text}
          </button>
        ))}
      </div>
      <button
        type="button"
        onClick={onNone}
        className="mt-2 text-xs text-error hover:text-[#ff8a95] transition-colors cursor-pointer"
      >
        None of these &rarr;
      </button>
    </div>
  );
}
