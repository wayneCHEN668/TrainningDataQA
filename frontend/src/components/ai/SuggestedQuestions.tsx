interface SuggestedQuestionsProps {
  onSelect: (q: string) => void;
}

const DEFAULT_QUESTIONS = [
  "2025年ISTQB CTFL的通过率是多少？",
  "页面对象模型如何改进测试自动化？",
  "比较基于风险的测试与基于需求的测试",
  "为登录功能生成一个示例测试计划",
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
