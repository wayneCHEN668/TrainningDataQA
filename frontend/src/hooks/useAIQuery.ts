import { useCallback, useRef } from "react";
import { useChatStore } from "../stores/chatStore";
import { loadHistory, saveHistory } from "../utils/chatStorage";
import type { ClarificationOption } from "../types/chat";

let _msgIdCounter = 0;
function uid(): string {
  return `msg-${Date.now()}-${++_msgIdCounter}`;
}

// ---------------------------------------------------------------------------
// SSE parsing
// ---------------------------------------------------------------------------

interface ParsedSSEEvent {
  event: string;
  data: Record<string, unknown>;
}

function parseSSEEvent(raw: string): ParsedSSEEvent | null {
  const lines = raw.split("\n");
  let event = "";
  let dataStr = "";
  for (const line of lines) {
    if (line.startsWith("event: ")) {
      event = line.slice(7);
    } else if (line.startsWith("data: ")) {
      dataStr = line.slice(6);
    }
  }
  if (!event || !dataStr) return null;
  try {
    return { event, data: JSON.parse(dataStr) };
  } catch {
    return null;
  }
}

// ---------------------------------------------------------------------------
// Hook
// ---------------------------------------------------------------------------

export function useAIQuery() {
  const store = useChatStore();
  const abortRef = useRef<AbortController | null>(null);
  const questionRef = useRef<string>("");  // captured for saveHistory on done

  // ---- Event dispatch map ------------------------------------------------

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  function dispatch(event: string, data: any) {
    switch (event) {
      case "intent_resolved":
        store.setIntentLabel(`${data.intent}（${data.complexity}）`);
        store.setStatus("thinking");
        break;

      case "clarification_options":
        store.updateLastAiMessage((msg) => ({
          ...msg,
          clarificationOptions: data.options,
        }));
        store.setStatus("done");
        abortRef.current?.abort();
        break;

      case "step_start":
        store.addStep({
          stepNo: data.step_no,
          thought: data.thought,
          action: data.action,
          paramsSummary: data.params_summary,
          status: "running",
        });
        break;

      case "step_done":
        store.updateStep(data.step_no, {
          status: "done",
          resultSummary: data.result_summary,
        });
        break;

      case "answer_chunk":
        store.setStatus("streaming");
        store.updateLastAiMessage((msg) => ({
          ...msg,
          content: msg.content + data.text_delta,
        }));
        break;

      case "chart_ready":
        store.addChart(data);
        break;

      case "evidence":
        // Steps are already populated via step_start/step_done events
        // with correct camelCase field mapping. Skip overwriting with
        // raw snake_case backend data.
        break;

      case "done":
        store.setStatus("done");
        abortRef.current?.abort();
        // Capture the backend-generated session_id for feedback
        if (data.session_id) {
          store.setLastSessionId(data.session_id);
        }
        // Finalize the round: save steps/charts to message and archive
        store.finalizeRound();
        // Persist to localStorage for next turn
        {
          const msgs = useChatStore.getState().messages;
          const lastAi = [...msgs].reverse().find((m) => m.role === "ai");
          if (lastAi?.content) {
            saveHistory(questionRef.current, lastAi.content);
          }
        }
        break;

      case "error":
        store.setError(data.message || "未知错误");
        abortRef.current?.abort();
        break;
    }
  }

  // ---- submit ------------------------------------------------------------

  const submit = useCallback(
    (question: string) => {
      const t0 = performance.now();
      console.log("[AI Query] ===== 开始提问 =====");
      console.log("[AI Query] 问题:", question);

      // Abort any in-flight request
      abortRef.current?.abort();

      // Archive previous round and prepare for new question (keep messages)
      store.prepareNewRound(question);

      // Add user message
      store.addMessage({
        id: uid(),
        role: "user",
        content: question,
        timestamp: Date.now(),
      });

      // Add AI placeholder message
      store.addMessage({
        id: uid(),
        role: "ai",
        content: "",
        timestamp: Date.now(),
      });

      // Capture question for saveHistory on done
      questionRef.current = question;

      // Build POST body with history from localStorage
      const token = localStorage.getItem("access_token") || "";
      const baseUrl = import.meta.env.VITE_API_BASE_URL || "/api/v1";
      const url = `${baseUrl}/ai-query`;
      const history = loadHistory();
      console.log("[AI Query] 历史条数:", history.length);

      const body = JSON.stringify({ question, history });
      console.log("[AI Query] 请求 URL:", url, "(POST)");
      console.log("[AI Query] Token 存在:", !!token, "长度:", token.length);

      const controller = new AbortController();
      abortRef.current = controller;

      // Start the SSE stream
      console.log("[AI Query] 发起 fetch...");
      const tFetch = performance.now();

      fetch(url, {
        method: "POST",
        signal: controller.signal,
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body,
      })
        .then(async (response) => {
          console.log("[AI Query] fetch 响应到达, 耗时:", (performance.now() - tFetch).toFixed(0), "ms");
          console.log("[AI Query] 响应状态:", response.status, response.statusText);
          console.log("[AI Query] Content-Type:", response.headers.get("content-type"));

          // Handle HTTP errors before entering stream
          if (!response.ok) {
            console.log("[AI Query] !! 响应非 OK, status:", response.status);
            if (response.status === 401) {
              console.log("[AI Query] !! 401 未授权, 跳转登录页");
              localStorage.removeItem("access_token");
              window.location.href = "/login";
              return;
            }
            store.setError(`服务器错误（${response.status}）`);
            return;
          }

          const reader = response.body?.getReader();
          if (!reader) {
            console.log("[AI Query] !! response.body 为空, 无法获取 reader");
            store.setError("无响应内容");
            return;
          }
          console.log("[AI Query] Reader 已获取, 开始读取 SSE 流...");

          const decoder = new TextDecoder();
          let buffer = "";
          let chunkCount = 0;

          try {
            while (true) {
              const { done, value } = await reader.read();
              chunkCount++;
              if (done) {
                console.log("[AI Query] SSE 流结束, 共读取", chunkCount, "个 chunk");
                break;
              }

              buffer += decoder.decode(value, { stream: true });

              // Split on double-newline (SSE event boundary)
              const parts = buffer.split("\n\n");
              // Last part may be incomplete — keep in buffer
              buffer = parts.pop() || "";

              for (const raw of parts) {
                const trimmed = raw.trim();
                if (!trimmed) continue;
                console.log("[AI Query] ← SSE 原始事件:", trimmed.substring(0, 200));
                const parsed = parseSSEEvent(trimmed);
                if (parsed) {
                  console.log("[AI Query] ← SSE 解析事件:", parsed.event, JSON.stringify(parsed.data).substring(0, 150));
                  dispatch(parsed.event, parsed.data);
                } else {
                  console.log("[AI Query] !! SSE 解析失败, raw:", trimmed.substring(0, 100));
                }
              }
            }
            console.log("[AI Query] 总耗时:", (performance.now() - t0).toFixed(0), "ms");
          } catch (err: unknown) {
            if (err instanceof DOMException && err.name === "AbortError") {
              console.log("[AI Query] 请求被取消 (AbortError)");
              return;
            }
            console.log("[AI Query] !! 流读取异常:", err);
            if (store.status !== "done" && store.status !== "error") {
              store.setError("连接已断开");
            }
          } finally {
            reader.releaseLock();
          }
        })
        .catch((err: unknown) => {
          if (err instanceof DOMException && err.name === "AbortError") {
            console.log("[AI Query] fetch 被取消 (AbortError)");
            return; // intentional cancel
          }
          console.log("[AI Query] !! fetch 失败:", err);
          if (store.status !== "done" && store.status !== "error") {
            store.setError("网络错误");
          }
        });
    },
    [store],
  );

  // ---- cancel ------------------------------------------------------------

  const cancel = useCallback(() => {
    abortRef.current?.abort();
    store.setStatus("done");
  }, [store]);

  // ---- clarification handlers -------------------------------------------

  const selectClarification = useCallback(
    (option: ClarificationOption) => {
      submit(option.text);
    },
    [submit],
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
        },
      );
      store.updateLastAiMessage((msg) => ({
        ...msg,
        content:
          "您的问题已记录。我们将尽快改进系统。",
      }));
      store.setStatus("done");
    },
    [store],
  );

  const sendFeedback = useCallback(
    async (_messageId: string, question: string, answer: string, feedbackType: string) => {
      const token = localStorage.getItem("access_token") || "";
      const baseUrl = import.meta.env.VITE_API_BASE_URL || "/api/v1";
      const sessionId = useChatStore.getState().lastSessionId;
      try {
        await fetch(`${baseUrl}/ai-query/feedback`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
          },
          body: JSON.stringify({
            session_id: sessionId,
            question,
            answer,
            feedback_type: feedbackType,
          }),
        });
      } catch {
        // Feedback is fire-and-forget — don't interrupt the user
        console.warn("[AI Query] Failed to send feedback");
      }
    },
    [],
  );

  return { submit, cancel, selectClarification, selectNoneOfThese, sendFeedback };
}
