# Phase 6 — 前端 React Chat UI 设计文档

**项目**: SkillCloudHS AI 数据问答系统
**日期**: 2026-06-12
**状态**: 已确认

---

## 1. 概述

Phase 6 实现 React Chat UI，通过 SSE (EventSource) 接收后端 Phase 5 的流式数据，渲染双栏对话界面。

### 1.1 技术栈

React 18 + TypeScript 5 + Tailwind CSS v4 + shadcn/ui + Zustand + Recharts 2.x

### 1.2 视觉决策

| 选项 | 结果 |
|------|------|
| 布局 | 50/50 双栏，可切换推理面板 |
| 推理步骤 | Timeline 风格 |
| 消息气泡 | Card Bubbles + AI 头像 |
| 图表位置 | 推理面板中 |
| 输入区 | 固定底部栏 + 推荐问题 Pills |
| 追问交互 | 内嵌在 AI 消息气泡中 |

---

## 2. 组件树

```
ChatInterface (50/50 双栏)
  ChatPanel (左侧)
    MessageList
      MessageBubble (用户, 右对齐 card)
      MessageBubble (AI, 左对齐 card + avatar)
        ClarificationOptions (追问时内嵌)
        FeedbackButtons
    SuggestedQuestions (输入框上方 pills)
    InputArea (固定底部, textarea + 发送按钮)
  ReasoningPanel (右侧, w-1/2, 可切换)
    ThinkingSteps (Timeline)
    ChartRenderer (Recharts)
```

---

## 3. 数据流

```
User types question → submit(question)
  → EventSource GET /api/v1/ai-query?q=...
  → SSE events:
    intent_resolved → store.setIntentLabel()
    step_start → store.addStep({status:"running"})
    step_done → store.updateStep({status:"done"})
    answer_chunk → store.updateLastAiMessage(content += delta)
    chart_ready → store.addChart()
    evidence → store.updateLastAiMessage(steps=...)
    done → store.setStatus("done")
    clarification_options → store.updateLastAiMessage(clarificationOptions=...)
```

---

## 4. Zustand Store

```
chatStore:
  messages[], status, currentSteps[], currentCharts[],
  intentLabel, reasoningPanelVisible, error
  → addMessage, updateLastAiMessage, addStep, updateStep,
    addChart, setStatus, toggleReasoningPanel
```

### 状态转换: idle → thinking → streaming → done/error

---

## 5. useAIQuery Hook

- 创建 EventSource 连接 SSE 端点
- 监听 8 种事件类型 → 更新 Zustand store
- cancel(): 关闭连接
- selectClarification(): 用转述问题重新提交
- selectNoneOfThese(): 保存到 unmatched_queries.md

### SSE 认证: URL query param ?token=xxx（Phase 6 方案）

---

## 6. 暗色主题 (Spotify-inspired)

- 背景: #121212 / #181818 / #1f1f1f
- 主色: #1ed760 (Spotify Green)
- 文字: #ffffff (主) / #b3b3b3 (副)
- 错误: #f3727f
- 按钮: 500px+ pill radius, 大写 + letter-spacing

---

## 7. 测试策略

### 组件测试 (8+)
- MessageBubble, ThinkingSteps, StreamingAnswer, ClarificationOptions, ReasoningPanel 切换

### Store 测试 (5+)
- addMessage, updateStep, setStatus 状态转换

### Hook 测试 (3+)
- Mock EventSource SSE 事件解析, cancel, clarification 选择

### 验收标准

| 指标 | 要求 |
|------|------|
| 测试通过 | 16+ |
| 暗色主题 | Spotify 风格 |
| 响应式 | <768px 单栏 |
| 流式渲染 | 逐字无闪烁 |
