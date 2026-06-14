# AI 回复反馈按钮 — 设计文档

**日期**: 2026-06-14
**状态**: 待实现

## 概述

在 AI 回复气泡下方添加 4 个操作按钮：复制、喜欢、不喜欢、完全错误，替代当前仅有的 👍👎 两个按钮。按钮采用纯图标风格，hover 显示 tooltip，并连接后端反馈 API。

## 需求摘要

| 按钮 | 图标 | Tooltip | 行为 |
|------|------|---------|------|
| 复制 | `Copy` | "复制" | 复制渲染后纯文本到剪贴板，成功后图标变 ✓ 1.5s |
| 喜欢 | `ThumbsUp` | "有帮助" | 提交正面反馈，选中态变 Spotify 绿 |
| 不喜欢 | `ThumbsDown` | "不够好" | 提交负面反馈，选中态变红色 |
| 完全错误 | `XCircle` | "完全错误" | 提交严重负面反馈（事实错误），选中态变红色 |

### 交互规则

- **喜欢/不喜欢/完全错误** 三者互斥：选中一个会自动取消其他两个，再次点击已选中的按钮取消选择
- **复制** 独立：不受反馈选择影响，也不影响反馈选择
- 不需要用户填写原因，点击即提交

## 组件架构

```
MessageBubble.tsx
  └── MessageActions.tsx   ← 新组件，替代 FeedbackButtons.tsx
        ├── 复制按钮 (lucide: Copy → Check on success)
        ├── 喜欢按钮 (lucide: ThumbsUp)
        ├── 不喜欢按钮 (lucide: ThumbsDown)
        └── 完全错误按钮 (lucide: XCircle)
```

### 新建文件

- `frontend/src/components/ai/MessageActions.tsx` — 4 按钮组件

### 修改文件

- `frontend/src/components/ai/MessageBubble.tsx` — 用 `MessageActions` 替换 `FeedbackButtons`
- `frontend/src/components/ai/MessageList.tsx` — 更新 `onFeedback` 签名
- `frontend/src/components/ai/ChatPanel.tsx` — 实现 `onFeedback` 处理函数
- `frontend/src/stores/chatStore.ts` — 新增 `sendFeedback` 方法（或用 hook 处理）
- `frontend/src/types/chat.ts` — 新增 `FeedbackType` 类型
- `backend/app/api/v1/ai_query.py` — 新增 `POST /feedback` 端点

### 删除文件

- `frontend/src/components/ai/FeedbackButtons.tsx` — 被 MessageActions 替代

## 视觉设计

延续 Spotify dark theme：

| 属性 | 值 |
|------|-----|
| 按钮间距 | `gap: 2px` |
| 图标尺寸 | `w-3.5 h-3.5` (14px) |
| 按钮 padding | `p-1` |
| 默认颜色 | `text-text-subdued` (#888) |
| Hover 颜色 | `text-text-secondary` (#b0b0b0) |
| 喜欢选中色 | `text-[#1ed760]` (Spotify Green) |
| 不喜欢选中色 | `text-error` (#f3727f) |
| 完全错误选中色 | `text-error` (#f3727f) |
| 复制成功色 | `text-[#1ed760]` (#1ed760) |
| 位置 | AI 气泡左下方，时间戳上方 |

## 数据流

```
ChatPanel.handleFeedback(messageId, feedbackType)
  → useAIQuery.sendFeedback(messageId, feedbackType)
    → POST /api/v1/ai-query/feedback { session_id, question, answer, feedback_type }
      → backend 写入 qa_session_log.user_feedback (1=like, -1=dislike, -2=wrong)
```

## 后端 API

### `POST /api/v1/ai-query/feedback`

Request:
```json
{
  "session_id": "msg-1718400000-1",
  "question": "本月完成率如何？",
  "answer": "根据数据，本月总体完成率为 87.3%...",
  "feedback_type": "like"
}
```

`feedback_type` 枚举: `"like"` | `"dislike"` | `"wrong"`

Response:
```json
{
  "status": "ok"
}
```

对应的数据库写入：
- `like` → `user_feedback = 1`
- `dislike` → `user_feedback = -1`
- `wrong` → `user_feedback = -2`

## 测试要点

- 三个反馈按钮互斥选择
- 再次点击已选中按钮取消选择
- 复制按钮独立工作
- 复制成功后图标变为 ✓ 并在 1.5s 后恢复
- 反馈 API 调用成功/失败处理
- 多个 AI 消息各自的反馈状态独立
