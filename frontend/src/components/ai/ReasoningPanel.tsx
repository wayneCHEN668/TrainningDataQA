import { useState } from "react";
import { X, ChevronDown, ChevronRight } from "lucide-react";
import { useChatStore } from "../../stores/chatStore";
import type { ThinkingStep } from "../../types/chat";
import { ThinkingSteps } from "./ThinkingSteps";
import { ChartRenderer } from "./ChartRenderer";
import { formatBytes } from "../../utils/format";

/** Collapsible wrapper for thinking steps — folded by default. */
function CollapsibleSteps({ steps }: { steps: ThinkingStep[] }) {
  const [open, setOpen] = useState(false);
  const doneCount = steps.filter((s) => s.status === "done").length;

  return (
    <div className="mb-3">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-1.5 w-full text-left text-xs text-text-secondary hover:text-text-primary transition-colors py-1"
      >
        {open ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
        <span>思考过程</span>
        <span className="text-text-subdued">
          ({doneCount}/{steps.length} 步)
        </span>
      </button>
      {open && <ThinkingSteps steps={steps} />}
    </div>
  );
}

export function ReasoningPanel() {
  const { currentSteps, currentCharts, currentDownloads, intentLabel, reasoningPanelVisible, toggleReasoningPanel, rounds } = useChatStore();

  if (!reasoningPanelVisible) return null;

  const hasCurrentRound = currentSteps.length > 0 || currentCharts.length > 0;
  const hasAnyContent = rounds.length > 0 || hasCurrentRound;

  return (
    <div className="w-1/2 h-full bg-bg-surface border-l border-border flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-border">
        <div>
          <h2 className="text-text-primary font-semibold text-sm">辅助信息</h2>
          {intentLabel && (
            <p className="text-text-subdued text-xs mt-0.5">{intentLabel}</p>
          )}
        </div>
        <button onClick={toggleReasoningPanel} className="text-text-secondary hover:text-text-primary">
          <X size={18} />
        </button>
      </div>
      {/* All rounds */}
      <div className="flex-1 overflow-y-auto p-4 space-y-0">
        {!hasAnyContent && (
          <div className="flex items-center justify-center h-full">
            <p className="text-text-subdued text-sm">
              AI 工作时，思考步骤和图表将显示在此处。
            </p>
          </div>
        )}

        {/* Historical rounds */}
        {rounds.map((round, idx) => (
          <div key={idx}>
            {/* Round header */}
            <div className="flex items-center gap-2 mb-3">
              <div className="flex-1 h-px bg-border" />
              <span className="text-text-subdued text-xs font-medium whitespace-nowrap">
                问题 {idx + 1}: {round.question.length > 20 ? round.question.slice(0, 20) + "…" : round.question}
              </span>
              <div className="flex-1 h-px bg-border" />
            </div>
            {round.intentLabel && (
              <p className="text-text-subdued text-xs mb-2 px-2">{round.intentLabel}</p>
            )}
            {round.steps.length > 0 && <CollapsibleSteps steps={round.steps} />}
            {round.charts.map((chart) => (
              <div key={chart.chartId} className="mt-4 first:mt-0">
                {chart.title && (
                  <h4 className="text-sm font-medium text-text-primary mb-2">
                    {chart.title}
                  </h4>
                )}
                <ChartRenderer spec={chart} />
              </div>
            ))}
          </div>
        ))}

        {/* Current round (in progress) */}
        {hasCurrentRound && (
          <div>
            {rounds.length > 0 && (
              <div className="flex items-center gap-2 mb-3">
                <div className="flex-1 h-px bg-border" />
                <span className="text-text-subdued text-xs font-medium whitespace-nowrap">
                  当前问题
                </span>
                <div className="flex-1 h-px bg-border" />
              </div>
            )}
            {intentLabel && rounds.length === 0 && (
              <p className="text-text-subdued text-xs mb-2 px-2">{intentLabel}</p>
            )}
            {currentSteps.length > 0 && <CollapsibleSteps steps={currentSteps} />}
            {currentCharts.map((chart) => (
              <div key={chart.chartId} className="mt-4 first:mt-0">
                {chart.title && (
                  <h4 className="text-sm font-medium text-text-primary mb-2">
                    {chart.title}
                  </h4>
                )}
                <ChartRenderer spec={chart} />
              </div>
            ))}

            {/* 报表下载区域 */}
            {currentDownloads.length > 0 && (
              <div className="mt-4">
                <h4 className="text-xs font-medium text-text-subdued uppercase tracking-wider mb-2">
                  📥 报表下载
                </h4>
                {currentDownloads.map((dl, i) => (
                  <div
                    key={i}
                    className="p-3 bg-bg-card rounded-lg border border-border mb-2"
                  >
                    <div className="text-sm font-medium text-text-primary">
                      {dl.fileName}
                    </div>
                    <div className="text-xs text-text-subdued mt-1">
                      {dl.sheets.length}个Sheet · {dl.totalRows.toLocaleString()}行 · {formatBytes(dl.fileSize)}
                    </div>
                    <a
                      href={`${dl.fileUrl}?display_name=${encodeURIComponent(dl.fileName)}`}
                      download={dl.fileName}
                      className="inline-block mt-2 px-4 py-1.5 bg-accent text-black text-xs font-medium rounded-full hover:opacity-90 transition-opacity"
                    >
                      下载 Excel
                    </a>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
