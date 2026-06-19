/**
 * localStorage-based chat history for multi-turn conversations.
 *
 * Data lifecycle:
 *   1. loadHistory() — read on each question submit, filter expired (>24h), trim to 6
 *   2. saveHistory() — append user+AI pair after done, trim to 6
 *   3. clearHistory() — explicit reset (new chat button)
 *
 * Format stored in localStorage key "skillcloud_chat_history":
 *   [{ "role": "user"|"ai", "content": "...", "ts": 1718250000000 }, ...]
 */

const STORAGE_KEY = "skillcloud_chat_history";
const MAX_ENTRIES = 6; // 3 rounds of Q&A
const TTL_MS = 24 * 3600 * 1000; // 24 hours

export interface HistoryItem {
  role: "user" | "ai";
  content: string;
  ts: number;
}

/** Shape returned to the backend (no `ts`). */
export interface HistoryPayload {
  role: "user" | "ai";
  content: string;
}

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------

/** Load recent (≤24h, ≤6 entries) history, strip timestamps for the backend. */
export function loadHistory(): HistoryPayload[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];

    const items: HistoryItem[] = JSON.parse(raw);
    if (!Array.isArray(items)) return [];

    const now = Date.now();
    const valid = items.filter(
      (item) => item && item.role && item.content && now - item.ts < TTL_MS,
    );

    // Keep last MAX_ENTRIES only; return without ts field
    const recent = valid.slice(-MAX_ENTRIES);
    return recent.map(({ role, content }) => ({ role, content }));
  } catch {
    return [];
  }
}

/** Append a Q&A pair to existing history, trim, write back. */
export function saveHistory(userMsg: string, aiMsg: string): void {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    const items: HistoryItem[] = raw ? JSON.parse(raw) : [];
    if (!Array.isArray(items)) return;

    const now = Date.now();
    items.push({ role: "user", content: userMsg, ts: now });
    items.push({ role: "ai", content: aiMsg, ts: now });

    // Keep last MAX_ENTRIES
    const trimmed = items.slice(-MAX_ENTRIES);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(trimmed));
  } catch {
    // localStorage full or unavailable — silently skip
  }
}

/** Clear all history (e.g., "New Chat" button). */
export function clearHistory(): void {
  try {
    localStorage.removeItem(STORAGE_KEY);
  } catch {
    // ignore
  }
}
