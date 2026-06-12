import { useCallback, useRef } from "react";
import { useChatStore } from "../stores/chatStore";
import type { ClarificationOption } from "../types/chat";

let _msgIdCounter = 0;
function uid(): string {
  return `msg-${Date.now()}-${++_msgIdCounter}`;
}

export function useAIQuery() {
  const store = useChatStore();
  const esRef = useRef<EventSource | null>(null);

  const submit = useCallback(
    (question: string) => {
      // 1. Close any existing EventSource connection
      esRef.current?.close();

      // 2. Add user message
      store.addMessage({
        id: uid(),
        role: "user",
        content: question,
        timestamp: Date.now(),
      });

      // 3. Add AI placeholder message
      store.addMessage({
        id: uid(),
        role: "ai",
        content: "",
        timestamp: Date.now(),
      });

      // 4. Reset session state (clears steps, charts, status, and error)
      store.clearCurrentSession();
      store.setStatus("idle");

      // 5. Build URL with token for auth
      const token = localStorage.getItem("access_token") || "";
      const encoded = encodeURIComponent(question);
      const baseUrl = import.meta.env.VITE_API_BASE_URL || "/api/v1";
      const url = `${baseUrl}/ai-query?q=${encoded}&token=${token}`;
      const es = new EventSource(url);
      esRef.current = es;

      // 6. Event listeners
      es.addEventListener("intent_resolved", (e) => {
        const d = JSON.parse((e as MessageEvent).data);
        store.setIntentLabel(`${d.intent} (${d.complexity})`);
        store.setStatus("thinking");
      });

      es.addEventListener("clarification_options", (e) => {
        const d = JSON.parse((e as MessageEvent).data);
        store.updateLastAiMessage((msg) => ({
          ...msg,
          clarificationOptions: d.options,
        }));
        store.setStatus("done");
        es.close();
      });

      es.addEventListener("step_start", (e) => {
        const d = JSON.parse((e as MessageEvent).data);
        store.addStep({ ...d, status: "running" });
      });

      es.addEventListener("step_done", (e) => {
        const d = JSON.parse((e as MessageEvent).data);
        store.updateStep(d.step_no, {
          status: "done",
          resultSummary: d.result_summary,
        });
      });

      es.addEventListener("answer_chunk", (e) => {
        const d = JSON.parse((e as MessageEvent).data);
        store.setStatus("streaming");
        store.updateLastAiMessage((msg) => ({
          ...msg,
          content: msg.content + d.text_delta,
        }));
      });

      es.addEventListener("chart_ready", (e) => {
        store.addChart(JSON.parse((e as MessageEvent).data));
      });

      es.addEventListener("evidence", (e) => {
        const d = JSON.parse((e as MessageEvent).data);
        store.updateLastAiMessage((msg) => ({
          ...msg,
          steps: d.steps,
        }));
      });

      es.addEventListener("done", () => {
        store.setStatus("done");
        es.close();
      });

      es.addEventListener("error", (e) => {
        const d = JSON.parse((e as MessageEvent).data);
        store.setError(d.message || "Unknown error");
        es.close();
      });

      es.onerror = () => {
        if (store.status !== "done" && store.status !== "error") {
          store.setError("Connection lost");
        }
        es.close();
      };
    },
    [store]
  );

  const cancel = useCallback(() => {
    esRef.current?.close();
    store.setStatus("done");
  }, [store]);

  const selectClarification = useCallback(
    (option: ClarificationOption) => {
      submit(option.text);
    },
    [submit]
  );

  const selectNoneOfThese = useCallback(
    async (originalQuestion: string) => {
      const token = localStorage.getItem("access_token") || "";
      await fetch(
        `${import.meta.env.VITE_API_BASE_URL || "/api/v1"}/ai-query/clarify/select`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            question_index: -1,
            original_question: originalQuestion,
          }),
        }
      );
      store.updateLastAiMessage((msg) => ({
        ...msg,
        content:
          "Your question has been recorded. We will improve the system soon.",
      }));
      store.setStatus("done");
    },
    [store]
  );

  return { submit, cancel, selectClarification, selectNoneOfThese };
}
