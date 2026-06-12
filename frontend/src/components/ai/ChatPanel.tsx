import { useState } from "react";
import { Send } from "lucide-react";
import { useChatStore } from "../../stores/chatStore";
import { useAIQuery } from "../../hooks/useAIQuery";
import { MessageList } from "./MessageList";
import { SuggestedQuestions } from "./SuggestedQuestions";

export function ChatPanel() {
  const [input, setInput] = useState("");
  const { messages, status } = useChatStore();
  const { submit, cancel, selectClarification, selectNoneOfThese } = useAIQuery();
  const isRunning = status === "thinking" || status === "streaming";

  const handleSend = () => {
    if (!input.trim() || isRunning) return;
    submit(input.trim());
    setInput("");
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex flex-col h-full bg-bg-deepest">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4">
        {messages.length === 0 ? (
          <div className="flex items-center justify-center h-full">
            <p className="text-text-subdued text-lg">
              Ask a question about your training data
            </p>
          </div>
        ) : (
          <MessageList
            messages={messages}
            onClarificationSelect={selectClarification}
            onClarificationNone={selectNoneOfThese}
          />
        )}
      </div>
      {/* Suggested questions */}
      {status === "idle" && messages.length === 0 && (
        <SuggestedQuestions onSelect={(q) => { setInput(q); submit(q); }} />
      )}
      {/* Input area */}
      <div className="sticky bottom-0 p-4 bg-bg-deepest border-t border-border">
        <div className="flex gap-2 items-end max-w-3xl mx-auto">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Enter your question..."
            rows={1}
            className="flex-1 resize-none bg-bg-card text-text-primary rounded-xl px-4 py-3
                       border border-border focus:outline-none focus:border-[#1ed760]
                       placeholder:text-text-subdued text-sm"
            style={{ maxHeight: "120px" }}
          />
          {isRunning ? (
            <button
              onClick={cancel}
              className="bg-[#f3727f] text-white rounded-full w-10 h-10 flex items-center justify-center flex-shrink-0"
            >
              ■
            </button>
          ) : (
            <button
              onClick={handleSend}
              disabled={!input.trim()}
              className="bg-[#1ed760] text-black rounded-full w-10 h-10 flex items-center justify-center flex-shrink-0 disabled:opacity-40"
            >
              <Send size={16} />
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
