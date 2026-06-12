import { PanelRight } from "lucide-react";
import { useChatStore } from "../../stores/chatStore";
import { ChatPanel } from "./ChatPanel";
import { ReasoningPanel } from "./ReasoningPanel";

export function ChatInterface() {
  const { reasoningPanelVisible, toggleReasoningPanel } = useChatStore();

  return (
    <div className="flex h-screen bg-bg-deepest">
      {/* Left: Chat */}
      <div className={`${reasoningPanelVisible ? "w-1/2" : "flex-1"} transition-all duration-300`}>
        <ChatPanel />
      </div>
      {/* Right: Reasoning */}
      <ReasoningPanel />
      {/* Mobile toggle button when panel is hidden */}
      {!reasoningPanelVisible && (
        <button
          onClick={toggleReasoningPanel}
          className="fixed right-4 top-4 bg-bg-card border border-border rounded-full p-2 text-text-secondary hover:text-[#1ed760] z-10"
        >
          <PanelRight size={20} />
        </button>
      )}
    </div>
  );
}
