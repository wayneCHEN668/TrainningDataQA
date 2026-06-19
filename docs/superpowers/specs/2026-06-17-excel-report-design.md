# Excel报表导出功能 — 设计规格

**日期**: 2026-06-17
**状态**: 设计完成，待实现
**关联文档**: `doc/SkillCloudHS_AI问答系统_PRD_v2.1.md`

---

## 1. 概述

### 1.1 背景

当前系统只支持以自然语言文字和图表形式回答用户的数据查询问题。用户无法将查询结果导出为文件进行离线分析、打印或分享。需要新增Excel报表导出功能。

### 1.2 目标

当用户提出包含"报表"、"导出"、"生成Excel"等关键词的问题时，系统：
- **左侧对话区**：AI仍给出自然语言分析 + 统计摘要卡片（行数、列数、文件大小）
- **右侧辅助面板**：在现有图表下方新增"报表下载"区域，提供Excel文件下载按钮
- **数据查询流程**：与现有分析流程完全一致，复用IntentClassifier → ReAct Agent → 18个工具的全部能力

### 核心原则

> **系统理解用户需求、查询数据的部分和现有分析问题给出回答的部分一致——只有最终表现形式不同。**

---

## 2. 架构设计

### 2.1 整体方案：意图驱动 + 后处理（Intent-Driven Hybrid）

```
用户问题
  → IntentClassifier（检测"报表"关键词 → output_mode="report"）
  → ReAct Agent（系统提示词告知LLM这是报表场景，优先使用表格数据工具）
  → 工具调用（返回值被透明收集到 tool_results[]）
  → Final Answer（LLM概述报表内容，提示用户下载）
  → [新] ExcelGenerator 后处理（用收集到的原始数据生成Excel）
  → [新] download_ready SSE事件（推送文件URL和元信息到前端）
  → done
```

### 2.2 方案选择理由

| 对比维度 | 方案A: 纯后处理 | 方案B: ReAct内工具 | **方案C: 意图驱动+后处理** |
|----------|----------------|-------------------|--------------------------|
| LLM感知场景 | ❌ 不知道在生成报表 | ✅ 完全感知 | ✅ 通过提示词告知 |
| 消耗ReAct步骤 | 0 | 1步 | 0 |
| Excel数据来源 | 工具原始数据 | LLM指定 | 工具原始数据 |
| 实现复杂度 | 低 | 中 | 中 |
| 用户体验 | 一般 | 好 | **最佳** |

---

## 3. 后端设计

### 3.1 意图分类变更

**文件**: `backend/app/services/ai/intent_definitions.py`

新增意图：
```python
"REPORT_GENERATION": {
    "keywords": ["报表", "导出", "生成Excel", "生成excel", "下载", "导出数据", "生成报告"],
    "complexity": "moderate",
    "description": "用户需要将查询结果导出为Excel报表文件"
}
```

**文件**: `backend/app/schemas/intent.py`

`IntentResult` 新增字段：
```python
output_mode: str = "analysis"  # "analysis" | "report"
```

**逻辑**: 当匹配到 REPORT_GENERATION 关键词时，`output_mode="report"`，但 `intent` 字段仍映射到最接近的数据查询意图（如 COMPLETION_RATE_QUERY）。后续的 schema 加载和工具选择逻辑完全不变。

### 3.2 ReactEngine 变更

**文件**: `backend/app/services/ai/react_engine.py`

**a) `run()` 方法新增参数**:
```python
async def run(self, question: str, intent_result: IntentResult, output_mode: str = "analysis"):
```

**b) 新增内部状态**:
```python
self._tool_results: list[dict] = []  # 收集每步工具的返回值
```

在工具执行后（约 line 233）收集结果：
```python
result = await tool.ainvoke(tool_input)
self._tool_results.append({
    "tool_name": tool.name,
    "result": result,  # 原始 dict
})
```

**c) 系统提示词增强**:

在 `REACT_SYSTEM_TEMPLATE` 中追加条件段落（当 `output_mode == "report"` 时）：
```
## 报表模式
用户需要生成可下载的Excel报表。请：
1. 优先使用能返回表格数据的工具（如 query_completion_rate、query_exam_performance 等）
2. 在最终回答中概述报表内容（包含哪些数据、大概行数）
3. 在回答末尾提示用户："报表已生成，请从右侧面板下载Excel文件"
4. 回答保持简洁——详细数据在Excel中，这里只需给出关键统计结论
```

**d) 返回值扩展**:

`run()` 的 yield 循环结束后，将 `tool_results` 附加到最后一个 yield 或通过返回值传出给调用方。

### 3.3 Excel生成服务（新组件）

**文件**: `backend/app/services/export/excel_generator.py`（新建）

**目录结构**: `backend/app/services/export/`（新建目录，为未来PDF等导出格式预留）

**核心类**:
```python
from dataclasses import dataclass
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter

@dataclass
class SheetMeta:
    name: str
    rows: int
    columns: int

@dataclass
class ExcelGenerationOutput:
    file_name: str
    file_url: str
    file_size: int
    sheets: list[SheetMeta]
    total_rows: int
    total_columns: int

class ExcelGenerator:
    """从工具返回的结构化数据生成带格式的Excel报表"""

    # 英文字段名 → 中文列名映射
    FIELD_LABEL_MAP = {
        "user_name": "姓名", "user_code": "学号", "dept_name": "部门",
        "completion_rate": "完成率(%)", "total_courses": "课程总数",
        "courses_completed": "已完成课程", "pass_rate": "通过率(%)",
        "avg_score": "平均分", "total_exams": "考试总数",
        "date": "日期", "value": "数值", "stat_date": "统计日期",
        "metric": "指标", "org_name": "机构名称",
        "class_name": "班级名称", "student_count": "学生人数",
        "course_name": "课程名称", "exam_name": "考试名称",
        "risk_type": "风险类型", "days_since_last_study": "距上次学习天数",
        "avg_composite_score": "综合平均分", "role_name": "角色",
        "count": "数量", "trend": "趋势", "granularity": "粒度",
        "urgent": "是否紧急", "is_at_risk": "是否有风险",
        "error_count": "错误数", "total_error_steps": "总错误步骤",
        "error_rate": "错误率(%)", "rank": "排名",
    }

    def generate(self, tool_results: list[dict], question: str,
                 user_scope: str, report_dir: str) -> ExcelGenerationOutput:
        """
        1. 过滤 tool_results，只保留含 list[dict] 字段的结果
        2. 一个 list[dict] 字段 → 一个 Sheet
        3. 每个 Sheet：标题行 → 副标题行 → 表头行 → 数据行 → 格式美化
        4. 保存文件，返回元信息
        """
```

**Sheet格式规范**:
- **第1行（标题行）**: 合并单元格，字体14pt加粗，居中。内容从用户问题提取
- **第2行（副标题行）**: 合并单元格，字体10pt，灰色。内容：`机构: {scope} | 生成时间: YYYY-MM-DD HH:MM`
- **第3行（表头行）**: 白色加粗字体，深色背景填充（#1f1f1f），冻结此行
- **第4行起（数据行）**: 字体10pt，奇数行浅灰背景（#fafafa）
- **条件格式**: 百分比类字段（含"率"字的列）< 60% → 红色字体
- **列宽**: 自动调整（取表头和前20行数据中最长内容 + 2字符边距）
- **边框**: 全表格细线边框

**标题行命名规则**:
- 优先从用户问题中提取关键词，去除"帮我/生成/报表/导出"等语气词
- 兜底：`"数据报表"`

**过滤逻辑**:
```python
def _extract_sheets(self, tool_results: list[dict]) -> list[tuple[str, list[dict]]]:
    """从工具结果中提取所有 list-of-dict 字段，返回 [(sheet_name, rows), ...]"""
    sheets = []
    for tr in tool_results:
        result = tr["result"]
        for key, val in result.items():
            if isinstance(val, list) and len(val) > 0 and isinstance(val[0], dict):
                sheet_name = self._field_to_chinese(key)
                sheets.append((sheet_name, val))
    return sheets
```

### 3.4 下载API

**文件**: `backend/app/api/v1/reports.py`（新建）

```python
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import os

router = APIRouter()

@router.get("/reports/{file_name}")
async def download_report(file_name: str):
    """下载报表文件。文件在24小时后自动清理。"""
    from app.core.config import settings
    file_path = os.path.join(settings.REPORT_DIR, file_name)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="文件不存在或已过期")
    return FileResponse(
        file_path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=file_name,
    )
```

**注册到 main.py**:
```python
from app.api.v1.reports import router as reports_router
app.include_router(reports_router, prefix="/api/v1")
```

### 3.5 配置

**文件**: `backend/app/core/config.py`

新增：
```python
REPORT_DIR: str = "./data/reports"   # Excel临时存储目录
REPORT_TTL_HOURS: int = 24          # 文件过期时间（小时）
```

### 3.6 文件清理

**文件**: `backend/app/jobs/cleanup_reports.py`（新建）

```python
import os
import time

async def cleanup_expired_reports():
    """删除超过 REPORT_TTL_HOURS 的报表文件"""
    from app.core.config import settings
    report_dir = settings.REPORT_DIR
    if not os.path.exists(report_dir):
        return
    cutoff = time.time() - settings.REPORT_TTL_HOURS * 3600
    for f in os.listdir(report_dir):
        fp = os.path.join(report_dir, f)
        if os.path.isfile(fp) and os.path.getmtime(fp) < cutoff:
            os.remove(fp)
```

**注册**: 在 `main.py` 的 lifespan 中通过 APScheduler 注册为每小时执行的定时任务。

### 3.7 ai_query.py 事件流变更

**文件**: `backend/app/api/v1/ai_query.py`

在 `event_stream()` 中，ReAct 循环结束后、`done` 事件之前插入：

```python
if output_mode == "report" and tool_results:
    excel_gen = ExcelGenerator()
    output = await asyncio.to_thread(
        excel_gen.generate,
        tool_results, question, user_ctx.get("scope", ""), settings.REPORT_DIR
    )
    yield format_sse("download_ready", {
        "file_name": output.file_name,
        "file_url": output.file_url,
        "file_size": output.file_size,
        "sheets": [{"name": s.name, "rows": s.rows, "columns": s.columns} for s in output.sheets],
        "total_rows": output.total_rows,
        "total_columns": output.total_columns,
    })
```

### 3.8 依赖

**文件**: `backend/pyproject.toml`

在 `[project.dependencies]` 中新增：
```
"openpyxl>=3.1.0",
```

---

## 4. SSE 事件规范

### 4.1 新事件: `download_ready`

**触发时机**: Excel 文件生成完成并保存到磁盘后

**事件格式**:
```
event: download_ready
data: {
    "file_name": "Q1各部门完成率报表.xlsx",
    "file_url": "/api/v1/reports/abc123def456.xlsx",
    "file_size": 15360,
    "sheets": [
        {"name": "各部门完成率", "rows": 15, "columns": 5},
        {"name": "Q1趋势数据", "rows": 90, "columns": 3}
    ],
    "total_rows": 105,
    "total_columns": 8
}
```

**SSE流中的位置**:
```
intent_resolved → [step_start → step_done × N] → answer_chunk × N
  → download_ready   ← 新事件
  → evidence → done
```

---

## 5. 前端设计

### 5.1 TypeScript 类型

**文件**: `frontend/src/types/chat.ts`

新增：
```typescript
export interface SheetMeta {
  name: string;
  rows: number;
  columns: number;
}

export interface DownloadInfo {
  fileName: string;
  fileUrl: string;
  fileSize: number;
  sheets: SheetMeta[];
  totalRows: number;
  totalColumns: number;
}
```

`Message` 接口新增：
```typescript
downloads?: DownloadInfo[];
```

### 5.2 Zustand Store

**文件**: `frontend/src/stores/chatStore.ts`

新增状态：
```typescript
currentDownloads: DownloadInfo[]  // 当前轮次生成的报表下载信息
```

新增方法：
```typescript
addDownload: (d: DownloadInfo) => void
clearCurrentDownloads: () => void
```

`prepareNewRound()` 和 `finalizeRound()` 需包含 downloads 的归档/清空（逻辑与 charts 一致）。

### 5.3 SSE 事件处理

**文件**: `frontend/src/hooks/useAIQuery.ts`

在 `dispatch()` 函数中新增 case：
```typescript
case "download_ready":
  useChatStore.getState().addDownload(data);
  break;
```

### 5.4 ReasoningPanel — 报表下载区域

**文件**: `frontend/src/components/ai/ReasoningPanel.tsx`

在滚动区域中，图表列表之后新增"报表下载"区块：

```tsx
{currentDownloads.length > 0 && (
  <div className="mt-4">
    <h4 className="text-xs font-medium text-text-subdued uppercase tracking-wider mb-2">
      📥 报表下载
    </h4>
    {currentDownloads.map((dl, i) => (
      <div key={i} className="p-3 bg-bg-card rounded-lg border border-border mb-2">
        <div className="text-sm font-medium text-text-primary">{dl.fileName}</div>
        <div className="text-xs text-text-subdued mt-1">
          {dl.sheets.length}个Sheet · {dl.totalRows}行 · {formatBytes(dl.fileSize)}
        </div>
        <a
          href={dl.fileUrl}
          download
          className="inline-block mt-2 px-4 py-1.5 bg-accent text-black text-xs font-medium rounded-full hover:bg-[#1ed760]/90 transition-colors"
        >
          下载 Excel
        </a>
      </div>
    ))}
  </div>
)}
```

**辅助函数**:
```typescript
function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1048576) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1048576).toFixed(1)} MB`;
}
```

### 5.5 MessageBubble — 统计摘要卡片

**文件**: `frontend/src/components/ai/MessageBubble.tsx`

在AI消息的 markdown 内容之后、MessageActions 之前，渲染统计摘要卡片：

```tsx
{message.role === "ai" && message.downloads?.map((dl, i) => (
  <div key={i} className="mt-3 p-3 bg-bg-card rounded-lg border border-border">
    <div className="flex items-center gap-2 text-sm">
      <FileSpreadsheet size={16} className="text-accent" />
      <span className="font-medium text-text-primary">{dl.fileName}</span>
    </div>
    <div className="mt-2 grid grid-cols-3 gap-2 text-xs text-text-subdued">
      <div>
        <span className="block text-text-secondary font-medium">{dl.totalRows.toLocaleString()}</span>
        <span>总行数</span>
      </div>
      <div>
        <span className="block text-text-secondary font-medium">{dl.totalColumns}</span>
        <span>总列数</span>
      </div>
      <div>
        <span className="block text-text-secondary font-medium">{formatBytes(dl.fileSize)}</span>
        <span>文件大小</span>
      </div>
    </div>
    <div className="mt-1.5 text-xs text-text-subdued">
      {dl.sheets.map(s => `${s.name}(${s.rows}行×${s.columns}列)`).join(" · ")}
    </div>
  </div>
))}
```

使用 `lucide-react` 的 `FileSpreadsheet` 图标（项目已安装）。

---

## 6. 错误处理

| 场景 | 处理方式 |
|------|---------|
| 工具未返回list-of-dict数据 | ExcelGenerator 返回空，不发 download_ready，AI照常文字回答 |
| Excel文件生成失败（磁盘满等） | 捕获异常，yield error SSE 事件，不阻塞 done |
| 用户请求下载但文件已被清理 | 后端返回 404，前端显示"文件已过期"提示 |
| 同时多个报表请求 | 每个请求生成独立的UUID文件名，不冲突 |
| 输出目录不存在 | ExcelGenerator 自动创建目录 |

---

## 7. 测试要点

### 7.1 后端单元测试
- `ExcelGenerator._extract_sheets()` — 过滤逻辑正确性
- `ExcelGenerator.generate()` — 输出文件存在、Sheet数量、行列数正确
- `cleanup_expired_reports()` — 过期文件删除、新文件保留

### 7.2 后端集成测试
- 报表关键词触发 output_mode="report"
- SSE 流中包含 download_ready 事件
- 下载端点正常返回文件

### 7.3 前端测试
- download_ready 事件被正确 dispatch 到 store
- ReasoningPanel 渲染下载卡片
- MessageBubble 渲染统计摘要
- 下载按钮点击触发浏览器下载

### 7.4 端到端测试
- "帮我生成Q1各部门完成率报表" → 左侧有分析文字+统计卡片，右侧有下载按钮
- 点击下载按钮 → 浏览器下载 .xlsx 文件
- 打开Excel文件 → 格式正确（标题行、表头、数据、条件格式）

---

## 8. 涉及文件汇总

| 层 | 文件 | 变更类型 |
|----|------|----------|
| 后端 | `app/services/ai/intent_definitions.py` | 改 — 新增 REPORT_GENERATION |
| 后端 | `app/schemas/intent.py` | 改 — IntentResult 加 output_mode |
| 后端 | `app/services/ai/react_engine.py` | 改 — 收集 tool_results + 提示词 |
| 后端 | `app/api/v1/ai_query.py` | 改 — Excel后处理步骤 |
| 后端 | **`app/services/export/excel_generator.py`** | **新** |
| 后端 | **`app/api/v1/reports.py`** | **新** |
| 后端 | `app/core/config.py` | 改 — REPORT_DIR 等配置 |
| 后端 | **`app/jobs/cleanup_reports.py`** | **新** |
| 后端 | `app/main.py` | 改 — 注册路由 + 清理job |
| 后端 | `pyproject.toml` | 改 — 加 openpyxl |
| 前端 | `src/types/chat.ts` | 改 — 加 DownloadInfo 类型 |
| 前端 | `src/stores/chatStore.ts` | 改 — 加 downloads 状态 |
| 前端 | `src/hooks/useAIQuery.ts` | 改 — download_ready 事件 |
| 前端 | `src/components/ai/ReasoningPanel.tsx` | 改 — 报表下载区域 |
| 前端 | `src/components/ai/MessageBubble.tsx` | 改 — 统计摘要卡片 |

**共计**: 6个新文件, 9个文件修改

---

## 9. 设计决策记录

1. **为什么用后处理而非ReAct内工具**: 节省ReAct步骤（上限8步），LLM不需要学习何时调用Excel工具；Excel生成是确定性逻辑不需要AI参与
2. **为什么只导出list-of-dict数据**: 标量数据（如"完成率85%"）在AI的文字回答中已充分体现，导出冗余；list-of-dict是用户真正想在Excel中查看/分析的数据
3. **为什么用openpyxl而非xlsxwriter**: openpyxl支持更丰富格式（条件格式、合并单元格），且是纯Python不依赖系统库
4. **为什么文件24小时过期**: 报表数据有时效性，长期存储徒增磁盘和管理负担；用户需要时可重新提问生成
5. **为什么output_mode设在IntentResult而非新意图**: 保持工具选择逻辑不变，"报表"只是输出格式的切换，不影响数据查询流程
