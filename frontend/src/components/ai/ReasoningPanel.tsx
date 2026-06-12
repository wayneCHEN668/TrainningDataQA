import { X } from "lucide-react";
import { useChatStore } from "../../stores/chatStore";
import { ThinkingSteps } from "./ThinkingSteps";
import { ChartRenderer } from "./ChartRenderer";

export function ReasoningPanel() {
  const { currentSteps, currentCharts, intentLabel, reasoningPanelVisible, toggleReasoningPanel } = useChatStore();

  if (!reasoningPanelVisible) return null;

  return (
    <div className="w-1/2 h-full bg-bg-surface border-l border-border flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-border">
        <div>
          <h2 className="text-text-primary font-semibold text-sm">Reasoning</h2>
          {intentLabel && (
            <p className="text-text-subdued text-xs mt-0.5">{intentLabel}</p>
          )}
        </div>
        <button onClick={toggleReasoningPanel} className="text-text-secondary hover:text-text-primary">
          <X size={18} />
        </button>
      </div>
      {/* Steps */}
      <div className="flex-1 overflow-y-auto p-4 space-y-6">
        {currentSteps.length > 0 && <ThinkingSteps steps={currentSteps} />}
        {/* Charts */}
        {currentCharts.map((chart) => (
          <ChartRenderer key={chart.chartId} spec={chart} />
        ))}
        {currentSteps.length === 0 && currentCharts.length === 0 && (
          <div className="flex items-center justify-center h-full">
            <p className="text-text-subdued text-sm">
              Thinking steps and charts will appear here as the AI works.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
