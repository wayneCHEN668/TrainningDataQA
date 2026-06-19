import { PanelRight, LogOut } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useChatStore } from "../../stores/chatStore";
import { useAuthStore } from "../../stores/authStore";
import { ChatPanel } from "./ChatPanel";
import { ReasoningPanel } from "./ReasoningPanel";

export function ChatInterface() {
  const { reasoningPanelVisible, toggleReasoningPanel } = useChatStore();
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login", { replace: true });
  };

  return (
    <div className="flex flex-col h-screen bg-bg-deepest">
      {/* Top bar — user info + logout */}
      <header className="flex items-center justify-between px-4 py-2 bg-[#1f1f1f] border-b border-border flex-shrink-0">
        <span className="text-text-primary text-sm font-semibold">
          SkillCloudHS
        </span>
        <div className="flex items-center gap-3">
          {user && (
            <span className="text-text-secondary text-xs">
              {user.user_name}
              <span className="text-text-subdued ml-1">
                ({user.role_level === 0 ? "超级管理员" : user.role_level === 1 ? "管理员" : user.role_level === 2 ? "教师" : "学生"})
              </span>
            </span>
          )}
          <button
            onClick={handleLogout}
            className="text-text-subdued hover:text-error transition-colors p-1 cursor-pointer"
            title="退出登录"
          >
            <LogOut size={16} />
          </button>
        </div>
      </header>

      {/* Main content */}
      <div className="flex flex-1 overflow-hidden">
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
            className="fixed right-4 top-12 bg-bg-card border border-border rounded-full p-2 text-text-secondary hover:text-[#1ed760] z-10 cursor-pointer"
          >
            <PanelRight size={20} />
          </button>
        )}
      </div>
    </div>
  );
}
