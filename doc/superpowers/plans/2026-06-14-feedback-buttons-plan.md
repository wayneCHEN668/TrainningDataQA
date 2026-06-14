# AI 回复反馈按钮 — 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 AI 回复气泡下方添加 4 个纯图标操作按钮（复制/喜欢/不喜欢/完全错误），替换现有 FeedbackButtons，连接后端反馈 API。

**Architecture:** 新建 `MessageActions.tsx` 组件替代 `FeedbackButtons.tsx`，4 个按钮（复制独立，喜欢/不喜欢/完全错误三者互斥）。通过 `useAIQuery` hook 新增 `sendFeedback` 方法调用后端 `POST /api/v1/ai-query/feedback` 端点。后端写入 `qa_session_log.user_feedback` 字段（1=like, -1=dislike, -2=wrong）。

**Tech Stack:** React 18 + TypeScript 5 + Zustand + lucide-react + FastAPI + SQLAlchemy

**Spec:** `doc/superpowers/specs/2026-06-14-feedback-buttons-design.md`

---

### Task 1: 添加 FeedbackType 类型定义

**Files:**
- Modify: `frontend/src/types/chat.ts`

- [ ] **Step 1: 添加 FeedbackType 类型**

在 `chat.ts` 末尾添加：

```typescript
export type FeedbackType = "like" | "dislike" | "wrong";
```

- [ ] **Step 2: 验证 TypeScript 编译**

Run: `cd frontend && npx tsc --noEmit`
Expected: No errors related to the new type.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/types/chat.ts
git commit -m "feat: add FeedbackType to chat types"
```

---

### Task 2: 创建 MessageActions 组件

**Files:**
- Create: `frontend/src/components/ai/MessageActions.tsx`

- [ ] **Step 1: 创建组件文件及完整实现**

```typescript
import { Copy, ThumbsUp, ThumbsDown, XCircle, Check } from "lucide-react";
import { useState, useCallback, useEffect } from "react";
import type { FeedbackType } from "../../types/chat";

interface MessageActionsProps {
  content: string;
  onFeedback: (type: FeedbackType) => void;
}

export function MessageActions({ content, onFeedback }: MessageActionsProps) {
  const [selectedFeedback, setSelectedFeedback] = useState<FeedbackType | null>(null);
  const [copied, setCopied] = useState(false);

  const handleCopy = useCallback(async () => {
    try {
      // Strip common markdown syntax to get plain text
      const plainText = content
        .replace(/\*\*(.+?)\*\*/g, "$1")        // bold
        .replace(/\*(.+?)\*/g, "$1")             // italic
        .replace(/`(.+?)`/g, "$1")               // inline code
        .replace(/\[([^\]]+)\]\([^)]+\)/g, "$1") // links: [text](url)
        .replace(/^#{1,6}\s+/gm, "")             // headings
        .replace(/^>\s?/gm, "")                  // blockquotes
        .replace(/^---+\s*$/gm, "")              // horizontal rules
        .replace(/^\s*[\-*+]\s+/gm, "• ")        // unordered lists
        .replace(/\n{3,}/g, "\n\n")              // collapse extra blank lines
        .trim();
      await navigator.clipboard.writeText(plainText);
      setCopied(true);
    } catch {
      // Fallback: copy raw content
      await navigator.clipboard.writeText(content);
      setCopied(true);
    }
  }, [content]);

  // Reset copied icon after 1.5s
  useEffect(() => {
    if (!copied) return;
    const timer = setTimeout(() => setCopied(false), 1500);
    return () => clearTimeout(timer);
  }, [copied]);

  const handleFeedback = (type: FeedbackType) => {
    if (selectedFeedback === type) {
      // Toggle off — don't fire callback (no new feedback)
      setSelectedFeedback(null);
    } else {
      setSelectedFeedback(type);
      onFeedback(type);
    }
  };

  const btnBase =
    "p-1 rounded-md transition-colors cursor-pointer";

  return (
    <div className="flex items-center gap-0.5">
      {/* Copy */}
      <button
        type="button"
        onClick={handleCopy}
        className={`${btnBase} ${
          copied ? "text-[#1ed760]" : "text-text-subdued hover:text-text-secondary"
        }`}
        title="复制"
        aria-label="复制回答"
      >
        {copied ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
      </button>

      {/* Like */}
      <button
        type="button"
        onClick={() => handleFeedback("like")}
        className={`${btnBase} ${
          selectedFeedback === "like"
            ? "text-[#1ed760]"
            : "text-text-subdued hover:text-text-secondary"
        }`}
        title="有帮助"
        aria-label="有帮助"
      >
        <ThumbsUp className="w-3.5 h-3.5" />
      </button>

      {/* Dislike */}
      <button
        type="button"
        onClick={() => handleFeedback("dislike")}
        className={`${btnBase} ${
          selectedFeedback === "dislike"
            ? "text-error"
            : "text-text-subdued hover:text-text-secondary"
        }`}
        title="不够好"
        aria-label="不够好"
      >
        <ThumbsDown className="w-3.5 h-3.5" />
      </button>

      {/* Wrong */}
      <button
        type="button"
        onClick={() => handleFeedback("wrong")}
        className={`${btnBase} ${
          selectedFeedback === "wrong"
            ? "text-error"
            : "text-text-subdued hover:text-text-secondary"
        }`}
        title="完全错误"
        aria-label="完全错误"
      >
        <XCircle className="w-3.5 h-3.5" />
      </button>
    </div>
  );
}
```

- [ ] **Step 2: 验证 TypeScript 编译**

Run: `cd frontend && npx tsc --noEmit`
Expected: No errors.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/ai/MessageActions.tsx
git commit -m "feat: add MessageActions component with copy/like/dislike/wrong buttons"
```

---

### Task 3: 更新 MessageBubble 使用 MessageActions

**Files:**
- Modify: `frontend/src/components/ai/MessageBubble.tsx`

- [ ] **Step 1: 替换 FeedbackButtons 为 MessageActions**

在 `MessageBubble.tsx` 中：

1. 删除第 3 行的 `import { FeedbackButtons } from "./FeedbackButtons";`
2. 添加 `import { MessageActions } from "./MessageActions";`
3. 修改 `onFeedback` prop 类型：`onFeedback?: (positive: boolean) => void;` → `onFeedback?: (type: import("../../types/chat").FeedbackType) => void;`
4. 删除 `showFeedback` prop（新组件通过 content 长度自动判断）
5. 将第 127-129 行的 `FeedbackButtons` 替换为 `MessageActions`，传入 `content` 和 `onFeedback`

具体修改如下：

**Line 3 — 替换 import:**
```typescript
import { MessageActions } from "./MessageActions";
```

**Lines 7-13 — 更新 Props 接口:**
```typescript
interface MessageBubbleProps {
  message: Message;
  onClarificationSelect?: (option: ClarificationOption) => void;
  onClarificationNone?: () => void;
  onFeedback?: (type: "like" | "dislike" | "wrong") => void;
  showFeedback?: boolean;
}
```

**Lines 125-130 — 替换按钮区域:**
```typescript
        {/* Message actions (copy + feedback) */}
        {showFeedback && onFeedback && (
          <div className="mt-1 ml-1">
            <MessageActions
              content={message.content}
              onFeedback={onFeedback}
            />
          </div>
        )}
```

- [ ] **Step 2: 验证 TypeScript 编译**

Run: `cd frontend && npx tsc --noEmit`
Expected: No errors.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/ai/MessageBubble.tsx
git commit -m "feat: replace FeedbackButtons with MessageActions in MessageBubble"
```

---

### Task 4: 更新 MessageList 传递正确的 onFeedback 签名

**Files:**
- Modify: `frontend/src/components/ai/MessageList.tsx`

- [ ] **Step 1: 更新 onFeedback 类型签名**

修改 `MessageList` 的 `onFeedback` prop 类型：

```typescript
import type { Message, ClarificationOption, FeedbackType } from "../../types/chat";

interface MessageListProps {
  messages: Message[];
  onClarificationSelect?: (option: ClarificationOption) => void;
  onClarificationNone?: () => void;
  onFeedback?: (messageId: string, question: string, answer: string, type: FeedbackType) => void;
}
```

修改传递给 `MessageBubble` 的 `onFeedback` — 由于 MessageBubble 仍然只接收简单的 `(type) => void`，需要在 MessageList 中做适配：

```typescript
      {messages.map((msg) => {
        // Find the preceding user message for this AI message
        const msgIndex = messages.indexOf(msg);
        const prevUser = messages
          .slice(0, msgIndex)
          .reverse()
          .find((m) => m.role === "user");
        return (
          <MessageBubble
            key={msg.id}
            message={msg}
            onClarificationSelect={onClarificationSelect}
            onClarificationNone={onClarificationNone}
            onFeedback={
              onFeedback && prevUser
                ? (type: FeedbackType) => onFeedback(msg.id, prevUser.content, msg.content, type)
                : undefined
            }
            showFeedback={msg.role === "ai" && msg.content.length > 0}
          />
        );
      })}
```

- [ ] **Step 2: 验证 TypeScript 编译**

Run: `cd frontend && npx tsc --noEmit`
Expected: No errors.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/ai/MessageList.tsx
git commit -m "feat: update MessageList onFeedback to pass message context"
```

---

### Task 5: ChatPanel 实现 onFeedback 并连接 useAIQuery

**Files:**
- Modify: `frontend/src/components/ai/ChatPanel.tsx`
- Modify: `frontend/src/hooks/useAIQuery.ts`

- [ ] **Step 1: 在 useAIQuery 添加 sendFeedback 方法**

在 `useAIQuery.ts` 的 return 语句前添加：

```typescript
  const sendFeedback = useCallback(
    async (messageId: string, question: string, answer: string, feedbackType: string) => {
      const token = localStorage.getItem("access_token") || "";
      const baseUrl = import.meta.env.VITE_API_BASE_URL || "/api/v1";
      try {
        await fetch(`${baseUrl}/ai-query/feedback`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
          },
          body: JSON.stringify({
            session_id: messageId,
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
```

在 return 语句中添加 `sendFeedback`:

```typescript
  return { submit, cancel, selectClarification, selectNoneOfThese, sendFeedback };
```

- [ ] **Step 2: 在 ChatPanel 中连接 onFeedback**

在 `ChatPanel.tsx` 中：

修改 hook 解构为包含 `sendFeedback`：
```typescript
  const { submit, cancel, selectClarification, selectNoneOfThese, sendFeedback } = useAIQuery();
```

在 `MessageList` 上添加 `onFeedback`：
```typescript
          <MessageList
            messages={messages}
            onClarificationSelect={selectClarification}
            onClarificationNone={() => {
              const lastUser = [...messages].reverse().find((m) => m.role === "user");
              selectNoneOfThese(lastUser?.content ?? "");
            }}
            onFeedback={(messageId, question, answer, type) => {
              sendFeedback(messageId, question, answer, type);
            }}
          />
```

- [ ] **Step 3: 验证 TypeScript 编译**

Run: `cd frontend && npx tsc --noEmit`
Expected: No errors.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/hooks/useAIQuery.ts frontend/src/components/ai/ChatPanel.tsx
git commit -m "feat: connect feedback buttons to backend API via useAIQuery"
```

---

### Task 6: 删除旧的 FeedbackButtons 组件

**Files:**
- Delete: `frontend/src/components/ai/FeedbackButtons.tsx`

- [ ] **Step 1: 删除文件**

```bash
git rm frontend/src/components/ai/FeedbackButtons.tsx
```

- [ ] **Step 2: 确保没有残留引用**

Run: `cd frontend && grep -r "FeedbackButtons" src/ --include="*.tsx" --include="*.ts"`
Expected: No matches.

- [ ] **Step 3: Commit**

```bash
git commit -m "refactor: remove deprecated FeedbackButtons component"
```

---

### Task 7: 后端新增反馈 API 端点

**Files:**
- Modify: `backend/app/api/v1/ai_query.py`

- [ ] **Step 1: 添加 FeedbackRequest schema 和 endpoint**

在 `ai_query.py` 中，在 `AIQueryRequest` 类定义之后、`router` 定义之后添加：

```python
class FeedbackRequest(BaseModel):
    session_id: str = Field(..., min_length=1, description="AI 消息 ID")
    question: str = Field(..., min_length=1, description="用户问题")
    answer: str = Field(default="", description="AI 回答内容")
    feedback_type: str = Field(..., pattern=r"^(like|dislike|wrong)$", description="反馈类型")


@router.post("/ai-query/feedback")
async def submit_feedback(
    req: FeedbackRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserContext = Depends(get_current_user),
):
    """Submit user feedback for an AI answer.

    Stores feedback in qa_session_log.user_feedback:
    - like → 1 (有帮助)
    - dislike → -1 (不够好)
    - wrong → -2 (完全错误)
    """
    feedback_map = {"like": 1, "dislike": -1, "wrong": -2}
    feedback_value = feedback_map[req.feedback_type]

    try:
        await db.execute(
            text("""
                UPDATE qa_session_log
                SET user_feedback = :feedback
                WHERE session_id = :sid AND user_id = :uid
            """),
            {
                "feedback": feedback_value,
                "sid": req.session_id,
                "uid": current_user.user_id,
            },
        )
        await db.commit()
    except Exception:
        # Fire-and-forget — don't fail if logging fails
        pass

    return {"status": "ok"}
```

需要确保文件顶部已有 `text` 导入（from sqlalchemy import text），检查现有 imports 是否包含。

- [ ] **Step 2: 验证 Python 语法**

Run: `cd backend && python -c "from app.api.v1.ai_query import router; print('OK')"`
Expected: `OK` (no ImportError or SyntaxError)

- [ ] **Step 3: Commit**

```bash
git add backend/app/api/v1/ai_query.py
git commit -m "feat: add POST /api/v1/ai-query/feedback endpoint"
```

---

### Task 8: 端到端验证

**Files:**
- No file changes — verification only

- [ ] **Step 1: 启动后端验证 API 可访问**

Run: `cd backend && python -c "
from app.api.v1.ai_query import FeedbackRequest
req = FeedbackRequest(session_id='test', question='q', answer='a', feedback_type='like')
print('FeedbackRequest OK:', req.feedback_type)
req2 = FeedbackRequest(session_id='test', question='q', answer='a', feedback_type='wrong')
print('Wrong feedback OK:', req2.feedback_type)
"`
Expected: Both print without error.

- [ ] **Step 2: 前端构建验证**

Run: `cd frontend && npm run build`
Expected: Build succeeds without errors.

- [ ] **Step 3: 手动 UI 验证清单**

启动前后端后验证：
1. 发送一个问题，AI 回复后下方出现 4 个图标按钮（复制/👍/👎/✕）
2. hover 每个按钮显示对应 tooltip
3. 点击"喜欢"→ 图标变绿，再次点击取消
4. 点击"不喜欢"→ 图标变红，"喜欢"取消
5. 点击"完全错误"→ 图标变红，"不喜欢"取消
6. 点击"复制"→ 图标变 ✓ 绿色，1.5s 后恢复
7. 多条 AI 消息各自反馈状态独立

- [ ] **Step 4: Final commit (if any fixes needed)**

```bash
git add -A
git commit -m "chore: verification fixes for feedback buttons"
```
