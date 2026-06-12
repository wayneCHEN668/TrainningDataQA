# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**SkillCloudHS AI 数据问答系统** — an AI-powered natural-language data query system for a training/education platform. Administrators and teachers ask questions in plain Chinese about learning data (completion rates, exam scores, skill errors, trends, etc.) and get data-backed answers with charts and recommendations.

**Current phase**: Design and documentation. No implementation code exists yet. All specs live in `doc/`.

## Tech Stack (from PRD v2.1)

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11 + FastAPI + SQLAlchemy 2.0 (async) + LangChain 0.3+ |
| AI | OpenAI-Compatible API (Qwen3.5 / DeepSeek-V4, private deployment) |
| Frontend | React 18 + TypeScript 5 + Tailwind CSS v4 + shadcn/ui |
| State | Zustand + TanStack Query v5 |
| Charts | Recharts 2.x |
| Database | MySQL 8.0 + Redis 7 |
| Stream | Server-Sent Events (FastAPI StreamingResponse) |

## Key Documents

- `doc/SkillCloudHS_AI问答系统_PRD_v2.1.md` — Complete PRD with architecture, component specs, API design, and code examples
- `doc/db_table_index.yaml` — Database table index with 3-layer on-demand schema loading (the core optimization)
- `doc/skillcloud_v2_schema.sql` — Full MySQL schema (~60 tables)
- `doc/DESIGN-spotify.md` — Spotify-inspired dark theme design system

## Architecture (Request Flow)

```
User Question
  → IntentClassifier (LLM Call #1, ~400 tokens: SECTION1 module index)
  → Code Router (SECTION4 intent→module mapping, 0 tokens)
  → SchemaIndexService loads only relevant table summaries (SECTION2, ~800 tokens)
  → LangChain ReAct Agent (max 8 Thought→Action→Observation cycles)
    → 16 StructuredTools query the DB via SQLAlchemy async
    → QueryExecutor injects row-level permissions (hard enforcement)
  → SSE stream: intent → thinking steps → answer chunks → charts → done
```

## Core Design Decisions

### Three-Layer Schema Loading (`db_table_index.yaml`)
The key innovation. Instead of injecting the full DB schema (~8000 tokens) into every LLM call:
- **Layer 1 (always)**: Module index — 11 modules with what they answer (~400 tokens)
- **Layer 2 (on-demand)**: Table summaries — only tables in matched modules (~800 tokens)
- **Layer 3 (code-enforced)**: Forbidden table blacklist (0 tokens, checked in QueryExecutor)
- **Layer 4 (code-routed)**: Intent→module mapping (SECTION4, 0 tokens, pure lookup)

### Pre-Aggregated Stats Strategy
Never aggregate raw tables (`study_session_log`) for trend queries. Use pre-computed stats tables:
- `org_daily_stats`, `org_monthly_stats` — institutional daily/monthly aggregates
- `org_course_stats`, `courseware_study_stats` — per-course/per-courseware stats
- `learning_progress`, `course_grade` — learner progress snapshots and composite grades

### Three-Layer Permission Enforcement
1. **Prompt layer (soft)**: System prompt declares user's scope — not security, just LLM guidance
2. **QueryExecutor (hard)**: Automatically appends WHERE clauses based on role_level
3. **Blacklist validation (hard)**: Rejects SQL touching forbidden tables (Laravel system tables, etc.)

### 16 Tools (ToolRegistry)
Each tool is a LangChain `StructuredTool` with Pydantic v2 input schemas. Permission params are injected server-side — the LLM cannot pass them. Tools cover: completion rates, incomplete learners, exam performance, skill errors, trends, at-risk identification, individual profiles, org overviews, compliance, period comparison, anomaly detection, benchmarks, metric evaluation, recommendations, chart specs, and course/exam name resolution.

### Intent Classification
22 intent types mapped to `simple`/`moderate`/`complex` complexity levels. The intent result controls which modules' table summaries are loaded into the ReAct prompt and influences the tool selection strategy.

### SSE Streaming Events
8 event types: `intent_resolved`, `step_start`, `step_done`, `answer_chunk`, `chart_ready`, `evidence`, `done`, `error`. Frontend uses `EventSource` with Zustand for real-time UI updates.

## Database Conventions

- **Role levels**: 0=SuperAdmin, 1=Admin, 2=Teacher, 3=Student
- **Soft deletes**: Most tables use `deleted_at` timestamp (Laravel SoftDeletes pattern)
- **Org isolation**: `org_code` on most tables for multi-tenant separation
- **Forbidden tables for AI**: `cache`, `cache_locks`, `failed_jobs`, `job_batches`, `jobs`, `migrations`, `password_reset_tokens`, `personal_access_tokens`, `sessions`, `users` (use `user_info` instead)

## Design System

Spotify-inspired dark theme (`#121212`–`#1f1f1f`) with Spotify Green (`#1ed760`) as the sole accent color. Pill-shaped buttons (500px–9999px radius), compact typography (10px–24px), heavy shadows for elevation on dark backgrounds. Full spec in `doc/DESIGN-spotify.md`.

## Self-Evolution Mechanism

`qa_session_log` table captures every Q&A session (intent, modules used, tools called, tokens, feedback). A daily APScheduler job clusters questions, identifies low-quality answers, and auto-generates improved templates — tested before deployment. See PRD §11.

## Using Superpower wwriting-plan skill to Write Long Files

**Do NOT use default approach to write the plan, it always return Error 'writing file'

**Do NOT use Bash heredoc to write long markdown/plan files.** Heredocs with embedded code (Python, SQL, JS) fail due to quote conflicts and special character escaping. The `Write` tool is unreliable for long content (parameter-stripping bug).

**Reliable approach:** Write a Python generator script (using the `Write` tool since `.py` files are short) that constructs the content as a triple-quoted Python string and writes it to disk, then execute it with `python gen_script.py`. This avoids all escaping issues because Python triple-quoted raw strings (`r'''...'''`) handle quotes, backticks, and special characters natively. After execution, delete the generator script.
