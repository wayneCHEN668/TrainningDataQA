**SkillCloudHS**

**AI 数据问答系统**

产品需求文档 v2.1  ·  Python \+ React \+ TypeScript \+ Tailwind

| 属性 | 内容 |
| ----- | ----- |
| 文档版本 | v2.1（在 v2.0 基础上更新技术栈，整合 DB Schema Index） |
| 更新日期 | 2026-06-10 |
| 后端 | Python 3.11 \+ FastAPI \+ SQLAlchemy 2.0 \+ LangChain |
| 前端 | React 18 \+ TypeScript 5 \+ Tailwind CSS v4 \+ shadcn/ui |
| 数据库 | MySQL 8.0 \+ Redis 7 |
| AI 接入 | OpenAI-Compatible LLM API（私有化部署优先,开发阶段使用云服务） |
| Schema 索引 | db\_table\_index.yaml \+ SchemaIndexService |
| 流式输出 | Server-Sent Events（FastAPI StreamingResponse） |

# **1\. 产品概述**

## **1.1 产品定位**

AI 数据问答系统是 SkillCloudHS 平台的核心智能分析层，允许管理员、教师通过自然语言直接查询平台学习数据，获得有理有据的分析结论、图表和行动建议，无需专业的数据分析能力。

## **1.2 v2.1 相对 v2.0 的变更**

| 维度 | v2.0 | v2.1（本版本） |
| ----- | ----- | ----- |
| 后端框架 | Laravel 12 / PHP 8.3 | FastAPI / Python 3.11（AI 生态更完整） |
| 前端框架 | Vue 3 \+ shadcn-vue | React 18 \+ shadcn/ui（组件生态更丰富） |
| Schema 管理 | 直接加载全量 SQL | db\_table\_index.yaml 三层按需加载（新增） |
| ReAct 实现 | 自定义循环 | LangChain AgentExecutor \+ 自定义工具（新增） |
| ORM | Eloquent | SQLAlchemy 2.0 async（新增） |
| 状态管理 | Pinia | Zustand（轻量，适合对话组件） |
| 数据查询 | 直接查业务表 | 优先查分析宽表和统计预聚合表（新增） |
| Schema 注入 | 每次全量 | 意图→模块→按需加载，上下文降低 80%（新增） |

# **2\. 技术栈**

## **2.1 完整技术栈总览**

| 分层 | 技术 | 版本 | 职责 |
| ----- | ----- | ----- | ----- |
| 后端框架 | FastAPI | 0.115+ | 异步 API 框架，SSE 原生支持，Pydantic 集成 |
| AI 推理 | LangChain | 0.3+ | ReAct Agent、Tool 管理、LLM 抽象层 |
| AI 模型 | OpenAI-Compatible API | — | Qwen3.5 / DeepSeek-V4 私有化部署 |
| ORM | SQLAlchemy | 2.0（async） | 异步数据库访问，Analysis View 查询 |
| 数据验证 | Pydantic | v2 | 请求/响应数据模型，LLM 输出结构化解析 |
| 缓存/队列 | Redis \+ aioredis | 7.x | Schema 索引缓存、会话状态、异步任务队列 |
| 任务调度 | APScheduler / Celery | — | 每日统计聚合、Schema 进化任务 |
| 前端框架 | React | 18 | Hooks \+ 函数组件，TypeScript 严格模式 |
| UI 组件 | shadcn/ui | latest | 基于 Radix UI，无样式基础，高度可定制 |
| 样式 | Tailwind CSS | v4 | 原子化 CSS，CSS 变量主题系统 |
| 状态管理 | Zustand | 4.x | 轻量对话状态，比 Redux 简洁 80% |
| 数据请求 | TanStack Query | v5 | API 请求缓存、乐观更新、自动重试 |
| 图表 | Recharts | 2.x | React 原生图表，Tree-shaking 友好 |
| Schema 索引 | PyYAML \+ 自研 SchemaIndexService | — | db\_table\_index.yaml 解析与按需注入 |

## **2.2 后端项目结构**

| \# 目录结构 backend/ ├── app/ │   ├── main.py                    \# FastAPI 应用入口 │   ├── api/v1/ │   │   ├── ai\_query.py            \# SSE 问答主接口 │   │   ├── history.py             \# 历史记录接口 │   │   └── feedback.py            \# 用户反馈接口 │   ├── services/ai/ │   │   ├── schema\_index.py        \# SchemaIndexService（YAML 按需加载） │   │   ├── intent\_classifier.py   \# 意图识别（LLM Call \#1） │   │   ├── react\_engine.py        \# ReAct 推理引擎（LangChain） │   │   ├── tool\_registry.py       \# 16 个工具函数注册 │   │   └── answer\_generator.py    \# 最终答案生成 │   ├── services/query/ │   │   ├── query\_executor.py      \# SQL 执行 \+ 权限注入 │   │   └── permission\_scope.py    \# 用户权限范围解析 │   ├── models/                    \# SQLAlchemy ORM 模型 │   ├── schemas/                   \# Pydantic 请求/响应模型 │   └── core/ │       ├── config.py              \# 环境变量配置 │       ├── database.py            \# async SQLAlchemy 引擎 │       └── redis.py               \# Redis 连接池 ├── resources/ai/ │   └── db\_table\_index.yaml        \# 数据库表索引文件 └── requirements.txt |
| :---- |

## **2.3 前端项目结构**

| \# 目录结构 frontend/src/ ├── app/ │   └── ai-query/                  \# 问答页面路由 │       └── page.tsx ├── components/ai/ │   ├── ChatInterface.tsx          \# 主对话界面容器 │   ├── MessageList.tsx            \# 消息列表（用户+AI） │   ├── MessageBubble.tsx          \# 单条消息气泡 │   ├── ThinkingSteps.tsx          \# 推理步骤展示（可折叠） │   ├── StreamingAnswer.tsx        \# 流式文字渲染 │   ├── ChartRenderer.tsx          \# Recharts 图表渲染 │   ├── EvidencePanel.tsx          \# 数据依据展开面板 │   ├── SuggestedQuestions.tsx     \# 推荐问题列表 │   └── FeedbackButtons.tsx        \# 点赞/反馈按钮 ├── hooks/ │   ├── useAIQuery.ts              \# SSE 请求 Hook（核心） │   └── useSuggestedQuestions.ts   \# 推荐问题 Hook ├── stores/ │   └── chatStore.ts               \# Zustand 对话状态 ├── types/ │   └── ai.ts                      \# TypeScript 类型定义 └── lib/     └── api.ts                     \# Axios 封装 \+ Token 注入 |
| :---- |

# **3\. 系统架构**

## **3.1 整体请求流程**

| 层次 | 组件 | 技术实现 |
| ----- | ----- | ----- |
| 用户层 | React Chat UI | SSE EventSource \+ Zustand 实时状态更新 |
| API 网关 | FastAPI \+ Nginx | Bearer Token 鉴权，限流 20 次/分钟/用户 |
| Schema 索引层 | SchemaIndexService | 解析 db\_table\_index.yaml，Redis 缓存，三层按需注入 |
| 意图识别层 | IntentClassifier | LLM Call \#1，Pydantic 解析结构化输出 |
| 推理引擎层 | LangChain ReAct Agent | 多轮 Thought→Action→Observation 循环 |
| 工具执行层 | ToolRegistry | 16 个工具函数，SQLAlchemy async 查询，权限注入 |
| 数据基础层 | Analysis Views | 分析宽表 \+ 权限过滤视图，禁止直接访问业务原始表 |
| 流式输出层 | FastAPI StreamingResponse | SSE 事件流，前端 EventSource 接收 |

## **3.2 db\_table\_index.yaml 在请求中的作用点**

| Schema 按需加载策略（v2.1 核心改进） 旧方式：每次 LLM 调用都注入完整 Schema（\~8000 tokens，噪音多、成本高） 新方式：db\_table\_index.yaml 三层按需加载，单次问答 context 降至 \~1500 tokens 具体注入点：   \[注入点1\] 意图识别 prompt  ← SECTION1 模块索引（始终，\~400 tokens）   \[注入点2\] 代码路由         ← SECTION4 意图→模块映射（纯代码查表，0 tokens）   \[注入点3\] ReAct prompt     ← SECTION2 选中模块表摘要（按需，\~800 tokens）   \[注入点4\] SQL 执行前       ← SECTION3 禁止表黑名单（代码校验，0 tokens） |
| :---- |

## **3.3 完整请求生命周期**

| \# Python \# app/api/v1/ai\_query.py  (核心 SSE 端点) @router.get("/ai-query") async def ai\_query(     q: str,     session\_id: str | None \= None,     current\_user: UserContext \= Depends(get\_current\_user),     schema\_svc: SchemaIndexService \= Depends(get\_schema\_service),     db: AsyncSession \= Depends(get\_db), )-\> StreamingResponse:     async def event\_stream():         \# \[1\] 意图识别 ── 注入 SECTION1 模块索引         module\_index \= schema\_svc.get\_module\_index\_text()         classifier \= IntentClassifier(module\_index\_context=module\_index)         intent\_result \= await classifier.classify(q, current\_user)         yield format\_sse("intent\_resolved", intent\_result.model\_dump())         \# \[2\] 代码路由 ── 查 SECTION4，纯代码，0 token 消耗         modules \= schema\_svc.get\_modules\_for\_intent(intent\_result.intent)         \# \[3\] 加载表摘要 ── 仅命中模块的 SECTION2         schema\_context \= schema\_svc.get\_table\_summaries\_text(             modules=modules,             compact=(intent\_result.complexity \== "simple")         )         \# \[4\] ReAct 推理引擎         engine \= ReactEngine(             schema\_context=schema\_context,             user\_context=current\_user,             db=db,             schema\_svc=schema\_svc,   \# 工具执行时用于 SQL 校验         )         async for event in engine.run(q, intent\_result):             yield format\_sse(event.type, event.data)     return StreamingResponse(event\_stream(), media\_type="text/event-stream") |
| :---- |

# **4\. SchemaIndexService（Python 实现）**

与 Laravel 版本功能完全相同，Python 实现利用 PyYAML \+ aioredis，天然适配 FastAPI async 架构。

| \# Python \# app/services/ai/schema\_index.py import yaml, json from functools import lru\_cache from typing import Optional import aioredis class SchemaIndexService:     """     db\_table\_index.yaml 三层按需加载服务     四个核心方法对应 AI 问答请求的四个注入点     """     CACHE\_KEY \= "schema\_index\_v1"     def \_\_init\_\_(self, yaml\_path: str, redis: aioredis.Redis):         self.\_path \= yaml\_path         self.\_redis \= redis         self.\_index: dict | None \= None   \# 内存一级缓存     async def load(self):         """启动时调用，解析 YAML 并缓存到 Redis"""         cached \= await self.\_redis.get(self.CACHE\_KEY)         if cached:             self.\_index \= json.loads(cached)             return         with open(self.\_path, encoding="utf-8") as f:             self.\_index \= yaml.safe\_load(f)         await self.\_redis.set(             self.CACHE\_KEY,             json.dumps(self.\_index, ensure\_ascii=False),             ex=86400   \# 24 小时，更新 YAML 后手动调用 refresh()         )     \# ── 注入点 1：意图识别 prompt（始终注入，\~400 tokens）──────     def get\_module\_index\_text(self) \-\> str:         lines \= \["\#\# 系统数据模块（意图识别参考）"\]         for name, info in self.\_index\["MODULE\_INDEX"\].items():             lines.append(f"- {name}：{info\['answers'\]}")         return "".join(lines)     \# ── 注入点 2：意图→模块路由（纯代码查表，0 token）──────────     def get\_modules\_for\_intent(self, intent: str) \-\> list\[str\]:         routing \= self.\_index.get("INTENT\_MODULE\_ROUTING", {})         return routing.get(intent, \["M10\_进度成绩", "M9\_统计数据"\])     \# ── 注入点 3：ReAct prompt（按模块加载，\~800 tokens）────────     def get\_table\_summaries\_text(         self, modules: list\[str\], compact: bool \= False     ) \-\> str:         summaries \= self.\_index\["TABLE\_SUMMARIES"\]         lines \= \["\#\# 可用数据表（仅允许查询以下表）"\]         for table, info in summaries.items():             if info.get("module") not in modules:                 continue             if compact:                 lines.append(f"- {table}（{info\['label'\]}）：{info\['row\_meaning'\]}")             else:                 lines \+= \[                     f"",                     f"\#\#\# {table}（{info\['label'\]}）",                     f"一行含义：{info\['row\_meaning'\]}",                 \]                 if answers := info.get("answers"):                     a \= answers if isinstance(answers, str) else " | ".join(answers)                     lines.append(f"用于回答：{a}")                 if fields := info.get("key\_fields"):                     f\_str \= "、".join(f"{k}（{v}）" for k, v in fields.items())                     lines.append(f"关键字段：{f\_str}")                 for field, meaning in (info.get("null\_meaning") or {}).items():                     lines.append(f"注意：{field} 为 NULL 时 \= {meaning}")                 if caution := info.get("caution"):                     lines.append(f"警告：{caution.strip()}")         return "".join(lines)     \# ── 注入点 4：SQL 执行前黑名单校验（代码层，0 token）────────     def validate\_query\_tables(self, sql: str) \-\> tuple\[bool, str\]:         import re         forbidden \= set(self.\_index.get("AI\_FORBIDDEN\_TABLES", \[\]))         found \= \[t for t in forbidden if re.search(r"\\b"+t+r"\\b", sql, re.I)\]         if found:             return False, f"查询包含禁止访问的系统表：{found}"         return True, "OK"     async def refresh(self):         """部署新 YAML 后调用"""         await self.\_redis.delete(self.CACHE\_KEY)         self.\_index \= None         await self.load() |
| :---- |

# **5\. 意图识别层**

## **5.1 IntentClassifier 实现**

| \# Python \# app/services/ai/intent\_classifier.py from pydantic import BaseModel, Field from openai import AsyncOpenAI import json class SlotValues(BaseModel):     time\_range: dict \= Field(default\_factory=lambda: {"type": "this\_month"})     scope\_type: str \= "all"     scope\_name: str | None \= None     course\_name: str | None \= None     exam\_name: str | None \= None     metric: str | None \= None     compare\_with\_previous: bool \= False     top\_n: int \= 10     granularity: str \= "week" class IntentResult(BaseModel):     intent: str     confidence: float     complexity: str   \# simple | moderate | complex     slots: SlotValues     need\_clarification: bool \= False     clarification\_question: str | None \= None class IntentClassifier:     def \_\_init\_\_(self, module\_index\_context: str):         self.\_client \= AsyncOpenAI()   \# 指向私有化部署端点         self.\_module\_ctx \= module\_index\_context     async def classify(         self, question: str, user\_ctx: UserContext     ) \-\> IntentResult:         system \= INTENT\_SYSTEM\_PROMPT.format(             module\_index=self.\_module\_ctx,             user\_name=user\_ctx.name,             role\_label=user\_ctx.role\_label,             permission\_scope=user\_ctx.permission\_desc,             current\_datetime=datetime.now().strftime("%Y-%m-%d %H:%M"),         )         resp \= await self.\_client.chat.completions.create(             model="qwen3.5-plus",             messages=\[                 {"role": "system",  "content": system},                 {"role": "user",    "content": question},             \],             response\_format={"type": "json\_object"},             temperature=0.1,         )         raw \= json.loads(resp.choices\[0\].message.content)         return IntentResult(\*\*raw) |
| :---- |

## **5.2 意图识别完整系统提示词**

| \# 意图识别 System Prompt 你是 SkillCloudHS 培训数据分析系统的意图识别引擎。 只做分类和参数提取，不尝试回答问题。 \#\# 当前用户（运行时注入） 姓名：{user\_name}  角色：{role\_label}  权限范围：{permission\_scope} 当前时间：{current\_datetime} \#\# 数据模块概览（帮助意图分类） {module\_index} \#\# 支持的意图类别（22个） COMPLETION\_RATE\_QUERY     | 完成率查询     | simple   | 关键词：完成率/完成情况/没完成 INCOMPLETE\_LEARNER\_QUERY  | 未完成学员查询 | simple   | 关键词：谁没学完/未提交/逾期 LEARNING\_PROGRESS\_QUERY   | 学习进度查询   | simple   | 关键词：进度/学到哪/完成了几个 LEARNING\_DURATION\_QUERY   | 学习时长查询   | simple   | 关键词：学了多久/时长/花多少时间 EXAM\_SCORE\_QUERY          | 考试成绩查询   | simple   | 关键词：成绩/分数/平均分/得了多少 EXAM\_PASS\_RATE\_QUERY      | 考试通过率查询 | simple   | 关键词：通过率/及格率/过了多少人 SKILL\_ERROR\_QUERY         | 技能点错误分析 | moderate | 关键词：操作错误/哪步出错/错误率 COMPREHENSIVE\_GRADE\_QUERY | 综合成绩查询   | simple   | 关键词：综合成绩/总分/结业 PERFORMANCE\_RANKING\_QUERY | 成绩排名       | simple   | 关键词：排名/前几名/最好最差/倒数 LEARNING\_TREND\_QUERY      | 学习趋势分析   | moderate | 关键词：趋势/变化/走势/这几个月 ORG\_OVERVIEW\_QUERY        | 机构概览       | moderate | 关键词：整体情况/概览/汇总/总结 ORG\_COMPARISON\_QUERY      | 机构对比       | moderate | 关键词：对比/哪个最好/差距/比较 AT\_RISK\_LEARNER\_QUERY     | 风险学员识别   | moderate | 关键词：风险/需要关注/有问题的 COMPLIANCE\_RISK\_QUERY     | 合规风险查询   | moderate | 关键词：合规/监管/达标/未达标 INDIVIDUAL\_PROFILE\_QUERY  | 个人学习画像   | moderate | 关键词：某个人的情况/\[人名\]怎么样 ROOT\_CAUSE\_ANALYSIS       | 根因分析       | complex  | 关键词：为什么/原因/怎么解释 ANOMALY\_INVESTIGATION     | 异常调查       | complex  | 关键词：异常/突然/为什么这时候 COMPARATIVE\_DIAGNOSIS     | 对比诊断       | complex  | 关键词：差距从哪来/为什么A比B好 COMPLETION\_PREDICTION     | 完成情况预测   | moderate | 关键词：预测/按现在进度/能完成吗 RISK\_PREDICTION           | 风险预测       | moderate | 关键词：可能不及格/有没有风险 IMPROVEMENT\_SUGGESTION    | 改进建议       | complex  | 关键词：建议/怎么提升/如何改善 TRAINING\_PLANNING         | 培训规划       | complex  | 关键词：规划/下一步/重点培训什么 \#\# 槽位提取规则 time\_range: 今天→today | 本周→this\_week | 本月→this\_month | 上月→last\_month             本季→this\_quarter | 上季→last\_quarter | 今年→this\_year             最近N天/周/月 → custom（基于当前时间计算） scope\_type: 未指定→all | 提到具体机构/支行→org | 提到班级→class | 提到人名→individual 注意：问题包含"为什么/原因"等归因词时，强制设 complexity=complex \#\# 输出（只返回 JSON，不带其他文字） {"intent":"INTENT\_CODE","confidence":0.95,"complexity":"simple|moderate|complex",  "slots":{"time\_range":{"type":"..."},"scope\_type":"all","scope\_name":null,           "course\_name":null,"exam\_name":null,"metric":null,           "compare\_with\_previous":false,"top\_n":10,"granularity":"week"},  "need\_clarification":false,"clarification\_question":null} |
| :---- |

# **6\. ReAct 推理引擎**

## **6.1 LangChain 实现架构**

| \# Python \# app/services/ai/react\_engine.py from langchain.agents import AgentExecutor, create\_react\_agent from langchain\_openai import ChatOpenAI from langchain.tools import StructuredTool from langchain\_core.prompts import ChatPromptTemplate from typing import AsyncGenerator import asyncio class ReactEngine:     MAX\_STEPS \= 8     def \_\_init\_\_(         self,         schema\_context: str,      \# 来自 SchemaIndexService         user\_context: UserContext,         db: AsyncSession,         schema\_svc: SchemaIndexService,     ):         self.\_user\_ctx \= user\_context         self.\_db \= db         self.\_schema\_svc \= schema\_svc         \# 初始化 LLM         self.\_llm \= ChatOpenAI(             model="qwen3.5-plus",             base\_url="http://llm-server:8000/v1",             temperature=0.2,             streaming=True,         )         \# 注册工具         registry \= ToolRegistry(db=db, user\_ctx=user\_context, schema\_svc=schema\_svc)         self.\_tools \= registry.get\_all\_tools()         \# 构建 ReAct Prompt（注入 schema\_context）         self.\_prompt \= build\_react\_prompt(             schema\_context=schema\_context,             user\_context=user\_context,         )         \# 创建 LangChain ReAct Agent         agent \= create\_react\_agent(self.\_llm, self.\_tools, self.\_prompt)         self.\_executor \= AgentExecutor(             agent=agent,             tools=self.\_tools,             max\_iterations=self.MAX\_STEPS,             verbose=False,             return\_intermediate\_steps=True,         )     async def run(         self,         question: str,         intent\_result: IntentResult,     ) \-\> AsyncGenerator\[SSEEvent, None\]:         """运行 ReAct 循环，每步通过 async generator 推送 SSE 事件"""         steps\_so\_far \= \[\]         \# 使用 LangChain callbacks 捕获每步事件         async for chunk in self.\_executor.astream\_events(             {"input": question, "intent": intent\_result.model\_dump\_json()},             version="v2",         ):             event\_type \= chunk.get("event", "")             \# 推理步骤开始             if event\_type \== "on\_tool\_start":                 step\_no \= len(steps\_so\_far) \+ 1                 yield SSEEvent(                     type="step\_start",                     data={                         "step\_no": step\_no,                         "thought": chunk\["data"\].get("input", {}).get("\_\_thought\_\_", ""),                         "action": chunk\["name"\],                         "params\_summary": \_summarize\_params(chunk\["data"\]\["input"\]),                     }                 )             \# 推理步骤完成             elif event\_type \== "on\_tool\_end":                 result \= chunk\["data"\].get("output", {})                 steps\_so\_far.append(result)                 yield SSEEvent(                     type="step\_done",                     data={                         "step\_no": len(steps\_so\_far),                         "tool\_name": chunk\["name"\],                         "result\_summary": \_summarize\_result(result),                     }                 )             \# 最终答案流式输出             elif event\_type \== "on\_chat\_model\_stream":                 delta \= chunk\["data"\]\["chunk"\].content                 if delta:                     yield SSEEvent(type="answer\_chunk", data={"text\_delta": delta})         \# 推送图表和依据         charts \= \_extract\_charts(steps\_so\_far)         for chart in charts:             yield SSEEvent(type="chart\_ready", data=chart)         yield SSEEvent(type="done", data={"total\_steps": len(steps\_so\_far)}) |
| :---- |

## **6.2 ReAct System Prompt**

| \# ReAct System Prompt 你是 SkillCloudHS 培训数据分析系统的智能分析引擎。 通过 Thought → Action → Observation 循环回答用户的培训数据问题。 \#\# 当前用户 姓名：{user\_name}  角色：{role\_label}  权限范围：{permission\_scope} 当前时间：{current\_datetime} \#\# 用户问题 {input} \#\# 意图识别结果 {intent} \#\# 可查询的数据表 {schema\_context}   ↑ 来自 db\_table\_index.yaml，已按意图过滤，只包含相关模块的表 \#\# 可用工具（16个） {tools} \#\# 工具名称列表 {tool\_names} \#\# ReAct 格式（严格遵守） Thought: \[分析当前已知什么/还缺什么/下一步做什么\] Action: \[工具名称\] Action Input: \[JSON 格式的工具参数\] Observation: \[工具返回的结果\] ...（循环，最多 {max\_steps} 步） Thought: \[确认信息已足够回答问题\] Final Answer: \[最终回答——直接给用户看的自然语言，含数据依据和建议\] \#\# 约束 1\. 只查询 "可查询的数据表" 中列出的表，禁止访问其他表 2\. 不生成任何没有工具返回的数字，所有数据必须来自工具 3\. 用户提到课程名/考试名时，先调用 search\_course\_or\_exam 解析编号 4\. 发现数据异常时，调用 detect\_anomalies 定位具体节点 5\. 回答中的重要数字用 \*\*数字\*\* 标记 6\. 每次只声明一个 Action {agent\_scratchpad} |
| :---- |

# **7\. 工具集（16 个）**

所有工具基于 LangChain StructuredTool，通过 Pydantic v2 模型定义输入，权限参数在执行层自动注入，LLM 无法传入越权参数。

| 工具名 | 功能 | 主要数据源 | 输出核心字段 |
| ----- | ----- | ----- | ----- |
| query\_completion\_rate | 查询学习完成率（支持多维度分组） | learning\_progress \+ v\_learner\_overview | completion\_rate, breakdown\[\] |
| query\_incomplete\_learners | 查询未完成学员名单（含紧迫度） | learning\_progress | count, learners\[{urgency}\] |
| query\_exam\_performance | 查询考试成绩/通过率/题目分析 | exam\_enrollment \+ exam\_answer | pass\_rate, avg\_score, distribution |
| query\_skill\_error\_analysis | 技能点步骤错误率分析 | skill\_error\_log \+ skill\_point | top\_error\_steps\[\], error\_rate |
| query\_learning\_trend | 指标趋势数据（按天/周/月） | org\_daily\_stats / study\_session\_log | data\_points\[\], trend\_direction |
| query\_at\_risk\_learners | 识别风险学员（多类型预警） | learning\_progress \+ exam\_enrollment | learners\[{risk\_type, urgency}\] |
| query\_individual\_profile | 查询个人学习画像 | learner\_profile \+ course\_grade | courses\[\], weak\_areas\[\], pattern |
| query\_org\_overview | 机构/部门概览汇总 | org\_daily\_stats \+ course\_grade | overview{}, highlights{best/worst} |
| query\_compliance\_status | 合规达标情况与预测 | learning\_progress \+ course | compliance\_rate, projection{} |
| compute\_period\_comparison | 计算环比/同比变化 | （接收其他工具数据） | comparisons\[{delta, delta\_pct}\] |
| detect\_anomalies | 检测时间序列异常节点 | （接收趋势数据） | anomalies\[{period, deviation\_sigma}\] |
| get\_benchmark | 获取院系/机构脱敏基准均值 | dept\_benchmark\_stats / org\_benchmark\_stats | benchmark\_value, percentile\_bands |
| evaluate\_metric\_level | 评估指标水平（好/中/差） | （接收指标值+基准） | level, percentile, gap\_to\_average |
| generate\_recommendation | 生成改进建议 | （接收 findings 列表） | recommendations\[{priority, action}\] |
| generate\_chart\_spec | 生成 Recharts 图表规格 | （接收数据） | chart\_id, recharts\_spec{} |
| search\_course\_or\_exam | 课程/考试名称模糊解析为编号 | course \+ exam\_session | matches\[{code, name, score}\] |

### **核心工具实现示例**

| \# Python \# app/services/ai/tool\_registry.py from langchain.tools import StructuredTool from pydantic import BaseModel, Field class CompletionRateInput(BaseModel):     scope\_type: str \= Field(description="all|org|dept|class|individual")     scope\_codes: list\[str\] \= Field(default=\[\], description="机构/班级/院系编号列表")     time\_start: str \= Field(description="YYYY-MM-DD")     time\_end: str \= Field(description="YYYY-MM-DD")     course\_code: str | None \= Field(default=None, description="指定课程编号")     group\_by: str \= Field(default="none", description="none|dept|class|course") class ToolRegistry:     def \_\_init\_\_(self, db: AsyncSession, user\_ctx: UserContext,                  schema\_svc: SchemaIndexService):         self.\_db \= db         self.\_user \= user\_ctx         self.\_schema \= schema\_svc         self.\_executor \= QueryExecutor(db, user\_ctx, schema\_svc)     def \_make\_completion\_rate\_tool(self) \-\> StructuredTool:         async def \_run(scope\_type, scope\_codes, time\_start,                        time\_end, course\_code=None, group\_by="none"):             \# 权限在 QueryExecutor 内自动注入，LLM 无法绕过             return await self.\_executor.query\_completion\_rate(                 scope\_type=scope\_type,                 scope\_codes=scope\_codes,                 time\_range=(time\_start, time\_end),                 course\_code=course\_code,                 group\_by=group\_by,             )         return StructuredTool.from\_function(             coroutine=\_run,             name="query\_completion\_rate",             description=(                 "查询学习完成率。用于回答：完成率是多少/哪些机构完成率低/"                 "各班级完成情况对比。group\_by 设为 dept 可按院系分组。"             ),             args\_schema=CompletionRateInput,         )     def get\_all\_tools(self) \-\> list\[StructuredTool\]:         return \[             self.\_make\_completion\_rate\_tool(),             \# ... 其余 15 个工具同样模式         \] |
| :---- |

# **8\. 流式输出（SSE）**

## **8.1 FastAPI SSE 实现**

| \# Python \# app/api/v1/ai\_query.py  ── SSE 工具函数 import json from fastapi.responses import StreamingResponse def format\_sse(event\_type: str, data: dict) \-\> str:     """将事件格式化为标准 SSE 格式"""     payload \= json.dumps(data, ensure\_ascii=False)     return f"event: {event\_type}\\ndata: {payload}\\n\\n" \# SSE 事件类型定义 SSE\_EVENTS \= {     "intent\_resolved":  "意图识别完成，推送意图和复杂度",     "step\_start":       "推理步骤开始，推送 thought 和工具名",     "step\_done":        "推理步骤完成，推送结果摘要",     "answer\_start":     "开始生成最终答案",     "answer\_chunk":     "答案文字流（每次约 10-50 字）",     "chart\_ready":      "图表规格生成完成（Recharts spec）",     "evidence":         "数据依据汇总",     "done":             "全部完成",     "error":            "错误信息", } \# 响应头（Nginx 配置配合） SSE\_HEADERS \= {     "Content-Type": "text/event-stream",     "Cache-Control": "no-cache",     "X-Accel-Buffering": "no",   \# 关闭 Nginx 缓冲，确保实时推送     "Access-Control-Allow-Origin": "\*", } |
| :---- |

## **8.2 前端 SSE Hook（React \+ TypeScript）**

| \# TypeScript/React // src/hooks/useAIQuery.ts import { useState, useCallback, useRef } from "react" import { useChatStore } from "@/stores/chatStore" export interface ThinkingStep {   stepNo: number   thought: string   action: string   paramsSummary: string   status: "running" | "done"   resultSummary?: string } export interface ChartSpec {   chartId: string   chartType: "bar" | "line" | "pie" | "scatter"   rechartsSpec: object   // 直接传入 Recharts 组件 } export function useAIQuery() {   const \[steps, setSteps\] \= useState\<ThinkingStep\[\]\>(\[\])   const \[answer, setAnswer\] \= useState("")   const \[charts, setCharts\] \= useState\<ChartSpec\[\]\>(\[\])   const \[isThinking, setIsThinking\] \= useState(false)   const \[intentLabel, setIntentLabel\] \= useState("")   const esRef \= useRef\<EventSource | null\>(null)   const submit \= useCallback(async (question: string) \=\> {     // 重置状态     setSteps(\[\]); setAnswer(""); setCharts(\[\])     setIsThinking(true)     const token \= localStorage.getItem("access\_token")     const url \= \`/api/v1/ai-query?q=${encodeURIComponent(question)}\`     const es \= new EventSource(url)     esRef.current \= es     // 意图识别完成     es.addEventListener("intent\_resolved", (e) \=\> {       const d \= JSON.parse(e.data)       setIntentLabel(\`${d.intent}（${d.complexity}）\`)     })     // 推理步骤开始     es.addEventListener("step\_start", (e) \=\> {       const d \= JSON.parse(e.data)       setSteps(prev \=\> \[...prev, {         stepNo: d.step\_no,         thought: d.thought,         action: d.action,         paramsSummary: d.params\_summary,         status: "running"       }\])     })     // 推理步骤完成     es.addEventListener("step\_done", (e) \=\> {       const d \= JSON.parse(e.data)       setSteps(prev \=\> prev.map(s \=\>         s.stepNo \=== d.step\_no           ? { ...s, status: "done", resultSummary: d.result\_summary }           : s       ))     })     // 答案流式追加     es.addEventListener("answer\_chunk", (e) \=\> {       const d \= JSON.parse(e.data)       setAnswer(prev \=\> prev \+ d.text\_delta)     })     // 图表就绪     es.addEventListener("chart\_ready", (e) \=\> {       setCharts(prev \=\> \[...prev, JSON.parse(e.data)\])     })     // 完成     es.addEventListener("done", () \=\> {       setIsThinking(false)       es.close()     })     es.onerror \= () \=\> {       setIsThinking(false)       es.close()     }   }, \[\])   const cancel \= useCallback(() \=\> {     esRef.current?.close()     setIsThinking(false)   }, \[\])   return { steps, answer, charts, isThinking, intentLabel, submit, cancel } } |
| :---- |

# **9\. 前端 React 组件架构**

## **9.1 主界面 ChatInterface.tsx**

| \# TypeScript/React // src/components/ai/ChatInterface.tsx import { useState } from "react" import { useAIQuery } from "@/hooks/useAIQuery" import { ThinkingSteps } from "./ThinkingSteps" import { StreamingAnswer } from "./StreamingAnswer" import { ChartRenderer } from "./ChartRenderer" import { SuggestedQuestions } from "./SuggestedQuestions" import { Button } from "@/components/ui/button" import { Textarea } from "@/components/ui/textarea" import { Send, Square } from "lucide-react" export function ChatInterface() {   const \[input, setInput\] \= useState("")   const { steps, answer, charts, isThinking, submit, cancel } \= useAIQuery()   const handleSubmit \= () \=\> {     if (\!input.trim() || isThinking) return     submit(input.trim())     setInput("")   }   return (     \<div className="flex flex-col h-full max-w-4xl mx-auto gap-4 p-4"\>       {/\* 推荐问题 \*/}       {\!isThinking && \!answer && (         \<SuggestedQuestions onSelect={(q) \=\> { setInput(q); submit(q) }} /\>       )}       {/\* 推理步骤面板 \*/}       {steps.length \> 0 && (         \<ThinkingSteps steps={steps} isRunning={isThinking} /\>       )}       {/\* 流式答案 \*/}       {answer && \<StreamingAnswer text={answer} isStreaming={isThinking} /\>}       {/\* 图表区 \*/}       {charts.map(chart \=\> (         \<ChartRenderer key={chart.chartId} spec={chart} /\>       ))}       {/\* 输入区 \*/}       \<div className="flex gap-2 items-end border rounded-xl p-3 bg-background"\>         \<Textarea           value={input}           onChange={e \=\> setInput(e.target.value)}           onKeyDown={e \=\> e.key \=== "Enter" && \!e.shiftKey && handleSubmit()}           placeholder="输入你的问题，例如：为什么上季度反洗钱培训通过率下降了？"           className="flex-1 resize-none border-0 focus-visible:ring-0"           rows={2}         /\>         {isThinking           ? \<Button variant="destructive" size="icon" onClick={cancel}\>\<Square /\>\</Button\>           : \<Button size="icon" onClick={handleSubmit}\>\<Send /\>\</Button\>         }       \</div\>     \</div\>   ) } |
| :---- |

## **9.2 推理步骤面板 ThinkingSteps.tsx**

| \# TypeScript/React // src/components/ai/ThinkingSteps.tsx import { useState } from "react" import { ChevronDown, ChevronUp, Loader2, CheckCircle } from "lucide-react" import type { ThinkingStep } from "@/hooks/useAIQuery" interface Props {   steps: ThinkingStep\[\]   isRunning: boolean } export function ThinkingSteps({ steps, isRunning }: Props) {   const \[expanded, setExpanded\] \= useState(true)   return (     \<div className="rounded-xl border bg-muted/30 overflow-hidden"\>       {/\* 折叠头部 \*/}       \<button         onClick={() \=\> setExpanded(\!expanded)}         className="w-full flex items-center justify-between p-3                    text-sm font-medium text-muted-foreground hover:bg-muted/50"       \>         \<span\>           {isRunning ? "AI 正在分析..." : \`分析完成（共 ${steps.length} 步）\`}         \</span\>         {expanded ? \<ChevronUp size={16} /\> : \<ChevronDown size={16} /\>}       \</button\>       {/\* 步骤列表 \*/}       {expanded && (         \<div className="divide-y"\>           {steps.map(step \=\> (             \<div key={step.stepNo} className="p-3 space-y-1"\>               \<div className="flex items-center gap-2"\>                 {step.status \=== "running"                   ? \<Loader2 size={14} className="animate-spin text-blue-500" /\>                   : \<CheckCircle size={14} className="text-green-500" /\>                 }                 \<span className="text-xs font-mono bg-primary/10 text-primary                               px-2 py-0.5 rounded"\>                   {step.action}                 \</span\>                 \<span className="text-xs text-muted-foreground"\>                   {step.paramsSummary}                 \</span\>               \</div\>               {/\* 推理思考 \*/}               \<p className="text-xs text-muted-foreground pl-5"\>{step.thought}\</p\>               {/\* 结果摘要 \*/}               {step.resultSummary && (                 \<p className="text-xs text-foreground pl-5 font-medium"\>                   → {step.resultSummary}                 \</p\>               )}             \</div\>           ))}         \</div\>       )}     \</div\>   ) } |
| :---- |

## **9.3 图表渲染组件 ChartRenderer.tsx**

| \# TypeScript/React // src/components/ai/ChartRenderer.tsx // 接收 Python 工具 generate\_chart\_spec 生成的规格，直接渲染 import {   BarChart, Bar, LineChart, Line, PieChart, Pie,   XAxis, YAxis, CartesianGrid, Tooltip, Legend,   ReferenceLine, ResponsiveContainer, } from "recharts" import type { ChartSpec } from "@/hooks/useAIQuery" export function ChartRenderer({ spec }: { spec: ChartSpec }) {   const { chartType, rechartsSpec: s } \= spec   return (     \<div className="rounded-xl border p-4 bg-background"\>       \<h3 className="text-sm font-semibold mb-1"\>{s.title}\</h3\>       {s.subtitle && \<p className="text-xs text-muted-foreground mb-3"\>{s.subtitle}\</p\>}       \<ResponsiveContainer width="100%" height={280}\>         {chartType \=== "bar" ? (           \<BarChart data={s.data}\>             \<CartesianGrid strokeDasharray="3 3" /\>             \<XAxis dataKey={s.xKey} tick={{ fontSize: 12 }} /\>             \<YAxis tick={{ fontSize: 12 }} /\>             \<Tooltip /\>             \<Legend /\>             {s.bars.map((b: any) \=\> \<Bar key={b.key} dataKey={b.key} fill={b.color} name={b.label} /\>)}             {s.referenceLines?.map((r: any) \=\> (               \<ReferenceLine key={r.label} y={r.value} stroke={r.color}                             strokeDasharray="5 5" label={r.label} /\>             ))}           \</BarChart\>         ) : chartType \=== "line" ? (           \<LineChart data={s.data}\>             \<CartesianGrid strokeDasharray="3 3" /\>             \<XAxis dataKey={s.xKey} tick={{ fontSize: 12 }} /\>             \<YAxis tick={{ fontSize: 12 }} /\>             \<Tooltip /\>             \<Legend /\>             {s.lines.map((l: any) \=\> (               \<Line key={l.key} type="monotone" dataKey={l.key}                     stroke={l.color} name={l.label} dot={false} /\>             ))}           \</LineChart\>         ) : (           \<PieChart\>             \<Pie data={s.data} dataKey="value" nameKey="name" label /\>             \<Tooltip /\>           \</PieChart\>         )}       \</ResponsiveContainer\>     \</div\>   ) } |
| :---- |

# **10\. 权限控制机制**

## **10.1 三层防护**

| 层次 | 实现 | 保障内容 |
| ----- | ----- | ----- |
| Prompt 层（软） | System Prompt 声明用户权限范围 | LLM 理解不能越权，但此层不可信赖做安全保障 |
| 工具执行层（硬） | QueryExecutor 自动追加 WHERE 权限条件 | LLM 的参数无论传什么，执行时都被约束 |
| 结果过滤层（硬） | Schema 黑名单校验 \+ Policy 行级校验 | 工具执行前校验表名；返回前行级权限二次验证 |

| \# Python \# app/services/query/query\_executor.py class QueryExecutor:     """所有工具函数的 SQL 执行层，权限在此硬性注入"""     def \_\_init\_\_(self, db: AsyncSession, user\_ctx: UserContext,                  schema\_svc: SchemaIndexService):         self.\_db \= db         self.\_user \= user\_ctx         self.\_schema \= schema\_svc     def \_inject\_permission\_where(self, query: Select) \-\> Select:         """根据用户角色自动追加权限过滤条件"""         if self.\_user.role\_level \== 0:             return query   \# 超管不限制         elif self.\_user.role\_level \== 1:             return query.where(col("dept\_code") \== self.\_user.dept\_code)         elif self.\_user.role\_level \== 2:             return query.where(col("class\_code").in\_(self.\_user.class\_codes))         else:   \# 学生             return query.where(col("user\_id") \== self.\_user.user\_id)     async def execute\_safe(self, sql: str, params: dict) \-\> list\[dict\]:         """执行 SQL 前先过黑名单校验，再执行"""         ok, msg \= self.\_schema.validate\_query\_tables(sql)         if not ok:             raise PermissionError(msg)         result \= await self.\_db.execute(text(sql), params)         return \[dict(row) for row in result.mappings()\] |
| :---- |

# **11\. 自我进化机制**

## **11.1 qa\_session\_log 表**

| \# SQL CREATE TABLE \`qa\_session\_log\` (   \`id\`               BIGINT UNSIGNED  NOT NULL AUTO\_INCREMENT,   \`session\_id\`       VARCHAR(50)      NOT NULL  COMMENT "会话唯一ID",   \`user\_id\`          VARCHAR(50)      NOT NULL,   \`org\_code\`         VARCHAR(30)      NOT NULL,   \`question\`         TEXT             NOT NULL  COMMENT "用户原始问题",   \`intent\`           VARCHAR(50)      NULL,   \`complexity\`       VARCHAR(10)      NULL,   \`modules\_used\`     VARCHAR(300)     NULL      COMMENT "加载的模块列表JSON",   \`steps\_count\`      INT              DEFAULT 0,   \`tools\_used\`       VARCHAR(300)     NULL      COMMENT "调用工具列表JSON",   \`duration\_ms\`      INT              NULL,   \`total\_tokens\`     INT              NULL,   \`user\_feedback\`    TINYINT          NULL      COMMENT "1=有帮助 \-1=不准确",   \`fallback\_used\`    TINYINT(1)       DEFAULT 0,   \`asked\_at\`         DATETIME         NOT NULL DEFAULT CURRENT\_TIMESTAMP,   PRIMARY KEY (\`id\`),   INDEX \`idx\_qsl\_asked\`   (\`asked\_at\`),   INDEX \`idx\_qsl\_intent\`  (\`intent\`),   INDEX \`idx\_qsl\_feedback\`(\`user\_feedback\`) ); |
| :---- |

## **11.2 每日进化 Python 任务**

| \# Python \# app/jobs/evolution\_job.py  （APScheduler 每天凌晨 2:00 执行） async def run\_daily\_evolution():     """     第一层：自动进化（全自动）     \- 聚类高频问题     \- 识别低质量回答     \- 自动生成新模板并测试     \- 测试通过自动上线，通知用户     """     logs \= await fetch\_recent\_qa\_logs(days=7)     \# 1\. 语义聚类     clusters \= await semantic\_cluster(logs)  \# 调用 embedding API     \# 2\. 识别低质量（用户反馈 \-1 / fallback\_used=1 / steps\>=7）     low\_quality \= \[         l for l in logs         if l.user\_feedback \== \-1 or l.fallback\_used or l.steps\_count \>= 7     \]     \# 3\. 高频且当前回答质量低的问题 → 生成新模板     for cluster in clusters:         if cluster.frequency \>= 15 and cluster.avg\_quality \< 0.6:             template \= await generate\_template(cluster.representative\_question)             test\_result \= await test\_template(template)             if test\_result.passed:                 await save\_template(template)                 await notify\_users(template.summary)     \# 第二层：人工审核推送     complex\_needs \= \[c for c in clusters if c.needs\_new\_data\]     if complex\_needs:         await push\_to\_product\_team(complex\_needs) |
| :---- |

# **12\. API 接口规范**

| 方法 | 路径 | 说明 | 认证 |
| ----- | ----- | ----- | ----- |
| GET | /api/v1/ai-query | 主问答接口，返回 text/event-stream（SSE） | Bearer |
| GET | /api/v1/ai-query/history | 获取当前用户历史问答 | Bearer |
| POST | /api/v1/ai-query/{session\_id}/feedback | 提交反馈（+1/-1） | Bearer |
| GET | /api/v1/ai-query/suggestions | 获取推荐问题（按角色和近期数据） | Bearer |
| GET | /api/v1/ai-admin/evolution-report | 进化任务报告 | Bearer+Admin |
| POST | /api/v1/ai-admin/schema-refresh | 刷新 db\_table\_index.yaml 缓存 | Bearer+SuperAdmin |

## **SSE 事件类型完整定义**

| 事件类型 | 触发时机 | Payload 示例 |
| ----- | ----- | ----- |
| intent\_resolved | 意图识别完成 | {"intent":"ROOT\_CAUSE\_ANALYSIS","complexity":"complex","confidence":0.94} |
| step\_start | 推理步骤开始 | {"step\_no":1,"thought":"需要先确认通过率下降是否属实","action":"query\_exam\_performance"} |
| step\_done | 推理步骤完成 | {"step\_no":1,"result\_summary":"本季通过率61%，A支行最低34%"} |
| answer\_chunk | 答案文字流式输出 | {"text\_delta":"本季度反洗钱培训通过率为 \*\*61%\*\*，"} |
| chart\_ready | Recharts 图表规格就绪 | {"chart\_id":"c001","chart\_type":"bar","recharts\_spec":{...}} |
| evidence | 数据依据汇总 | {"steps":\[{"step\_no":1,"tool":"query\_exam\_performance","key\_finding":"..."}\]} |
| done | 全部完成 | {"total\_steps":7,"total\_tokens":4820,"duration\_ms":12340} |
| error | 任何错误 | {"code":"PERMISSION\_ERROR","message":"越权访问","recoverable":false} |

# **13\. 非功能需求**

| 指标 | 要求 | 实现方式 |
| ----- | ----- | ----- |
| 意图识别响应 | \< 1.0s | 轻量 LLM（7B级别），Pydantic 强制 JSON 输出 |
| 首步 SSE 推送 | \< 2.0s（用户无感等待） | 意图识别完成后立即推送，ReAct 第一步并发启动 |
| moderate 问题总耗时 | \< 20s（流式输出，无等待感） | 预定义链优先，工具查分析宽表（非原始表） |
| complex 问题总耗时 | \< 35s | ReAct 最多 8 步，超限输出部分结论 |
| Schema 注入 token 数 | \< 1500 tokens/次 | db\_table\_index.yaml 按模块按需加载（vs 全量 8000 tokens） |
| 并发问答 | 50 并发（初期） | FastAPI async \+ uvicorn workers，独立部署不与主服务共享 |
| LLM 调用失败 | 自动重试 2 次 | httpx retry \+ Circuit Breaker（tenacity 库） |
| 数据安全 | 所有查询权限硬注入 | QueryExecutor 层，Prompt 层只作软约束 |
| token 成本控制 | 单次 \< 6000 tokens | 工具只返回摘要数据，不返回完整原始结果集 |

# **14\. 开发里程碑**

| 阶段 | 时长 | 交付内容 | 验收标准 |
| ----- | ----- | ----- | ----- |
| Phase 1 · 数据基础层 | 第1-3周 | 分析宽表建立、权限过滤视图、基准统计表、db\_table\_index.yaml 编写 | 所有宽表数据准确，SchemaIndexService 单测通过 |
| Phase 2 · Python 后端骨架 | 第4-5周 | FastAPI 项目初始化、SQLAlchemy 连接、Redis 缓存、JWT 认证、SchemaIndexService | API 健康检查通过，YAML 加载缓存正确 |
| Phase 3 · 意图识别 | 第6-7周 | IntentClassifier \+ 完整 System Prompt \+ Pydantic 解析 | 22 个意图测试集准确率 \> 92% |
| Phase 4 · 工具集 | 第8-11周 | 16 个工具函数，权限注入，黑名单校验，单测 | 每个工具：正常/越权/空数据三类测试通过 |
| Phase 5 · ReAct 引擎 | 第12-14周 | LangChain Agent \+ 预定义3条推理链 \+ SSE 流式输出 | 复杂问题端到端测试通过，SSE 无卡顿 |
| Phase 6 · React 前端 | 第15-17周 | Chat UI / ThinkingSteps / ChartRenderer / Zustand Store | 非技术用户可独立使用，图表渲染正确 |
| Phase 7 · 进化机制 | 第18-19周 | qa\_session\_log \+ 日志分析 Job \+ 自动模板生成 | 运行2周后自动生成至少3个有效新模板 |
| Phase 8 · 调优上线 | 第20周 | Prompt 调优、性能压测、安全审计、生产部署 | P95 \< 20s，并发50无超时，权限测试通过 |

