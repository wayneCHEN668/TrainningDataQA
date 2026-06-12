interface SuggestedQuestionsProps {
  onSelect: (q: string) => void;
}

const DEFAULT_QUESTIONS = [
  "What is the pass rate for ISTQB CTFL in 2025?",
  "How does page object model improve test automation?",
  "Compare risk-based vs requirements-based testing",
  "Generate a sample test plan for a login feature",
];

export function SuggestedQuestions({ onSelect }: SuggestedQuestionsProps) {
  return (
    <div className="flex items-center gap-2 overflow-x-auto px-4 py-2 scrollbar-none">
      {DEFAULT_QUESTIONS.map((q) => (
        <button
          key={q}
          type="button"
          onClick={() => onSelect(q)}
          className="flex-shrink-0 px-4 py-1.5 rounded-full bg-bg-card text-text-secondary text-xs hover:bg-bg-hover hover:text-text-primary transition-colors cursor-pointer"
        >
          {q}
        </button>
      ))}
    </div>
  );
}
