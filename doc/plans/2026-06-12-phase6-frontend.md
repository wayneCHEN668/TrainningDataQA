# Phase 6 前端 React Chat UI 实施计划

> **For agentic workers:** Use superpowers:subagent-driven-development to implement.

**Goal:** 实现 React Chat UI — 双栏布局 + SSE 流式渲染 + Spotify 暗色主题。

**Architecture:** Zustand chatStore 管理状态，useAIQuery Hook 处理 SSE 事件流，组件树从 ChatInterface 向下分发。

**Tech Stack:** React 18, TypeScript 5, Tailwind CSS v4, shadcn/ui, Zustand, Recharts

---

### Task 1: 前端项目脚手架

**Files:**
- Create: `frontend/` (Vite + React + TypeScript)

- [ ] **Step 1: Initialize with Vite**

```bash
cd D:\MyPrograms\wuzi\QATraining
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install
```

- [ ] **Step 2: Install dependencies**

```bash
npm install zustand recharts lucide-react
npm install -D tailwindcss @tailwindcss/vite
```

- [ ] **Step 3: Configure Tailwind CSS v4 + shadcn/ui init**

Configure tailwind with Spotify theme colors: #121212 background, #1ed760 accent, #181818/#1f1f1f surfaces.

- [ ] **Step 4: Setup project structure**

Create directories: `src/components/ai/`, `src/hooks/`, `src/stores/`, `src/types/`, `src/lib/`

- [ ] **Step 5: Commit**

---

### Task 2: TypeScript types + Zustand Store

**Files:**
- Create: `frontend/src/types/chat.ts`
- Create: `frontend/src/stores/chatStore.ts`

- [ ] **Step 1: Write types/chat.ts**

All types: ThinkingStep, ChartSpec, ClarificationOption, Message, ChatStatus

- [ ] **Step 2: Write stores/chatStore.ts**

Zustand store with state + actions (addMessage, updateLastAiMessage, addStep, updateStep, addChart, setStatus, setIntentLabel, toggleReasoningPanel, clearCurrentSession)

- [ ] **Step 3: Verify imports + commit**

---

### Task 3: SSE Hook + API library

**Files:**
- Create: `frontend/src/lib/api.ts`
- Create: `frontend/src/hooks/useAIQuery.ts`

- [ ] **Step 1: Write lib/api.ts** — Axios instance with JWT token interceptor

- [ ] **Step 2: Write hooks/useAIQuery.ts** — EventSource SSE listener, all 8 event types handled, cancel/selectClarification/selectNoneOfThese

- [ ] **Step 3: Commit**

---

### Task 4: Core UI Components

**Files:**
- Create: `frontend/src/components/ai/MessageBubble.tsx`
- Create: `frontend/src/components/ai/MessageList.tsx`
- Create: `frontend/src/components/ai/ThinkingSteps.tsx`
- Create: `frontend/src/components/ai/StreamingAnswer.tsx`
- Create: `frontend/src/components/ai/SuggestedQuestions.tsx`
- Create: `frontend/src/components/ai/ClarificationOptions.tsx`
- Create: `frontend/src/components/ai/FeedbackButtons.tsx`
- Create: `frontend/src/components/ai/ChartRenderer.tsx`

Each component follows the visual design specs from the design doc.

- [ ] **Step 1: Write all 8 components** with Tailwind dark theme styling

- [ ] **Step 2: Commit**

---

### Task 5: Layout + Integration

**Files:**
- Create: `frontend/src/components/ai/ChatPanel.tsx`
- Create: `frontend/src/components/ai/ReasoningPanel.tsx`
- Create: `frontend/src/components/ai/ChatInterface.tsx`
- Modify: `frontend/src/app/page.tsx`

- [ ] **Step 1: Write ChatPanel** — left side: MessageList + SuggestedQuestions + InputArea

- [ ] **Step 2: Write ReasoningPanel** — right side: ThinkingSteps + ChartRenderer, togglable

- [ ] **Step 3: Write ChatInterface** — 50/50 flex container, toggle button, mobile responsive (<768px single column)

- [ ] **Step 4: Update page.tsx** — render ChatInterface

- [ ] **Step 5: Commit**

---

### Task 6: Unit Tests

**Files:**
- Create: `frontend/src/stores/chatStore.test.ts`
- Create: `frontend/src/components/ai/MessageBubble.test.tsx`
- Create: `frontend/src/components/ai/ThinkingSteps.test.tsx`
- Create: `frontend/src/components/ai/ClarificationOptions.test.tsx`
- Create: `frontend/src/hooks/useAIQuery.test.ts`

- [ ] **Step 1: Write store tests** (5+ tests)
- [ ] **Step 2: Write component tests** (8+ tests)
- [ ] **Step 3: Write hook tests** (3+ tests)
- [ ] **Step 4: Run all tests** → 16+ pass
- [ ] **Step 5: Commit**

---

### Task 7: Verification

- [ ] **Step 1: Run full test suite** `npm test`
- [ ] **Step 2: Verify build** `npm run build`
- [ ] **Step 3: Git log review**
- [ ] **Step 4: Commit**

---

## Task Dependencies

```
Task 1 (scaffold) → Task 2 (types+store) → Task 3 (hook+api)
                                               ↓
                                          Task 4 (components) + Task 5 (layout)
                                               ↓
                                          Task 6 (tests) → Task 7 (verify)
```

## Time Estimate: ~2.5 hours
