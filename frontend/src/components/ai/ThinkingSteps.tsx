import type { ThinkingStep } from "../../types/chat";
import { Check, Loader2 } from "lucide-react";

interface ThinkingStepsProps {
  steps: ThinkingStep[];
}

function StepIcon({ status }: { status: "running" | "done" }) {
  if (status === "done") {
    return (
      <div className="w-5 h-5 rounded-full bg-[#1ed760] flex items-center justify-center flex-shrink-0">
        <Check className="w-3 h-3 text-black" strokeWidth={3} />
      </div>
    );
  }
  return (
    <div className="w-5 h-5 rounded-full bg-[#1e88e5] flex items-center justify-center flex-shrink-0">
      <Loader2 className="w-3 h-3 text-white animate-spin" strokeWidth={3} />
    </div>
  );
}

export function ThinkingSteps({ steps }: ThinkingStepsProps) {
  if (steps.length === 0) {
    return (
      <div className="text-text-subdued text-sm px-4 py-6 text-center">
        No thinking steps yet.
      </div>
    );
  }

  return (
    <div className="px-4 py-3">
      <h3 className="text-text-secondary text-xs font-semibold uppercase tracking-wider mb-3">
        Reasoning
      </h3>
      <div className="relative">
        {/* Vertical line */}
        <div className="absolute left-2.5 top-0 bottom-0 w-px bg-border" />

        <div className="space-y-4">
          {steps.map((step) => (
            <div key={step.stepNo} className="relative flex gap-3 pl-7">
              {/* Dot */}
              <div className="absolute left-0 top-0.5">
                <StepIcon status={step.status} />
              </div>

              {/* Content */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-xs font-semibold text-text-primary">
                    Step {step.stepNo}
                  </span>
                  <span className="inline-block px-2 py-0.5 rounded-full text-xs font-medium bg-bg-card text-[#1ed760]">
                    {step.action}
                  </span>
                </div>
                <p className="text-xs text-text-secondary mb-1">
                  {step.paramsSummary}
                </p>
                {step.resultSummary && (
                  <p className="text-xs text-text-subdued italic">
                    {step.resultSummary}
                  </p>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
