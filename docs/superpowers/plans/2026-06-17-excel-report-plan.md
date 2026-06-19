# Excel报表导出功能 — 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 新增Excel报表导出功能——用户以"报表"/"导出"等关键词提问时，系统在右侧面板提供带格式的Excel文件下载，左侧给出自然语言分析+统计摘要卡片

**Architecture:** 意图驱动+后处理模式——IntentClassifier检测报表关键词设置output_mode="report"，ReAct流程不变但收集工具返回值，循环结束后ExcelGenerator用原始数据生成带格式的Excel，通过新SSE事件download_ready推送下载URL

**Tech Stack:** Python 3.11 + FastAPI + openpyxl + React 18 + TypeScript 5 + Zustand

**Design Spec:** `docs/superpowers/specs/2026-06-17-excel-report-design.md`

## Global Constraints

- openpyxl >= 3.1.0
- Excel文件存储在 `./data/reports/`，24小时自动清理
- 只导出工具返回值中的 list-of-dict 数据（不导出标量字段）
- 输出格式: .xlsx（openpyxl原生格式）
- SSE新事件类型: `download_ready`，位置在 answer_chunk 之后、evidence 之前
- 前端新图标使用 lucide-react 的 `FileSpreadsheet`（项目已安装）
- 不改变现有18个工具的选择逻辑，不消耗额外ReAct步骤
- 遵循现有代码风格: Python 用中文注释，TypeScript 用 JSDoc 注释

---

### Task 1: Dependencies & Configuration

**Files:**
- Modify: `backend/pyproject.toml`
- Modify: `backend/app/core/config.py`

**Interfaces:**
- Produces: `settings.REPORT_DIR: str`, `settings.REPORT_TTL_HOURS: int`
- Produces: `openpyxl` package available for import

- [ ] **Step 1: Add openpyxl dependency**

Edit `backend/pyproject.toml` — in `[project.dependencies]`, add after `"langchain-openai>=0.2.0"`:

```toml
"openpyxl>=3.1.0",
```

- [ ] **Step 2: Add config fields**

Edit `backend/app/core/config.py` — add after the `SCHEMA_YAML_PATH` line:

```python
# Excel report storage
REPORT_DIR: str = "./data/reports"
REPORT_TTL_HOURS: int = 24
```

- [ ] **Step 3: Install the new dependency**

```bash
cd backend && pip install openpyxl>=3.1.0
```
Expected: `Successfully installed openpyxl-3.x.x`

- [ ] **Step 4: Verify config loads**

```bash
cd backend && python -c "from app.core.config import settings; print(settings.REPORT_DIR); print(settings.REPORT_TTL_HOURS)"
```
Expected:
```
./data/reports
24
```

- [ ] **Step 5: Commit**

```bash
git add backend/pyproject.toml backend/app/core/config.py
git commit -m "feat: add openpyxl dependency and report storage config"
```

---

### Task 2: Excel Generator Service (Core New Code)

**Files:**
- Create: `backend/app/services/export/__init__.py`
- Create: `backend/app/services/export/excel_generator.py`
- Create: `backend/tests/services/export/__init__.py`
- Create: `backend/tests/services/export/test_excel_generator.py`

**Interfaces:**
- Produces: `ExcelGenerator` class with method `generate(tool_results, question, user_scope, report_dir) -> dict | None`
- Returns dict: `{"file_name": str, "file_url": str, "file_size": int, "sheets": list[dict], "total_rows": int, "total_columns": int}`
- Produces: `FIELD_LABEL_MAP: dict[str, str]` — 英文字段名→中文列名映射

- [ ] **Step 1: Create package init files**

Create `backend/app/services/export/__init__.py`:
```python
"""Export services — Excel, PDF, etc."""
```

Create `backend/tests/services/export/__init__.py`:
```python
# empty
```

- [ ] **Step 2: Write the failing test**

Create `backend/tests/services/export/test_excel_generator.py`:
```python
"""Tests for ExcelGenerator."""
import os
import tempfile
import pytest
from app.services.export.excel_generator import ExcelGenerator


class TestExtractSheets:
    """测试 _extract_sheets — 从工具结果中过滤 list-of-dict 字段"""

    def test_extracts_list_of_dict_fields(self):
        gen = ExcelGenerator()
        tool_results = [
            {
                "tool_name": "query_completion_rate",
                "result": {
                    "completion_rate": 85.0,
                    "total_learners": 100,
                    "breakdown": [
                        {"dept_name": "信息学院", "rate": 90.0},
                        {"dept_name": "机械学院", "rate": 80.0},
                    ],
                }
            }
        ]
        sheets = gen._extract_sheets(tool_results)
        assert len(sheets) == 1
        name, rows = sheets[0]
        assert "明细" in name  # breakdown → 明细数据
        assert len(rows) == 2
        assert rows[0]["dept_name"] == "信息学院"

    def test_skips_scalar_fields(self):
        gen = ExcelGenerator()
        tool_results = [
            {
                "tool_name": "query_completion_rate",
                "result": {
                    "completion_rate": 85.0,
                    "total_learners": 100,
                    "data_source": "course_grade",
                }
            }
        ]
        sheets = gen._extract_sheets(tool_results)
        assert len(sheets) == 0

    def test_skips_empty_lists(self):
        gen = ExcelGenerator()
        tool_results = [
            {
                "tool_name": "query_incomplete_learners",
                "result": {"incomplete_count": 0, "learners": []},
            }
        ]
        sheets = gen._extract_sheets(tool_results)
        assert len(sheets) == 0

    def test_handles_multiple_tools(self):
        gen = ExcelGenerator()
        tool_results = [
            {
                "tool_name": "query_completion_rate",
                "result": {"breakdown": [{"dept": "A", "val": 1}]},
            },
            {
                "tool_name": "query_learning_trend",
                "result": {"data_points": [{"date": "2026-01-01", "value": 50}]},
            },
        ]
        sheets = gen._extract_sheets(tool_results)
        assert len(sheets) == 2

    def test_handles_multiple_list_fields_in_one_result(self):
        gen = ExcelGenerator()
        tool_results = [
            {
                "tool_name": "query_multi",
                "result": {
                    "breakdown": [{"a": 1}],
                    "learners": [{"b": 2}],
                    "summary": "text only",
                }
            }
        ]
        sheets = gen._extract_sheets(tool_results)
        assert len(sheets) == 2


class TestGenerate:
    """集成测试 — generate() 方法"""

    def test_generates_valid_xlsx(self):
        gen = ExcelGenerator()
        tool_results = [
            {
                "tool_name": "query_completion_rate",
                "result": {
                    "breakdown": [
                        {"dept_name": "信息学院", "completion_rate": 85.5, "total_courses": 12},
                        {"dept_name": "机械学院", "completion_rate": 42.0, "total_courses": 8},
                    ]
                }
            }
        ]
        with tempfile.TemporaryDirectory() as tmpdir:
            output = gen.generate(
                tool_results=tool_results,
                question="帮我生成各部门完成率报表",
                user_scope="全部机构",
                report_dir=tmpdir,
            )
            # 检查输出元数据
            assert output is not None
            assert output["file_name"].endswith(".xlsx")
            assert output["file_url"].startswith("/api/v1/reports/")
            assert output["file_size"] > 0
            assert len(output["sheets"]) == 1
            assert output["sheets"][0]["rows"] == 2
            assert output["sheets"][0]["columns"] == 3
            assert output["total_rows"] == 2
            assert output["total_columns"] == 3

            # 检查文件存在于磁盘
            file_name = os.path.basename(output["file_url"])
            file_path = os.path.join(tmpdir, file_name)
            assert os.path.exists(file_path)

            # 验证是有效的 xlsx 文件
            from openpyxl import load_workbook
            wb = load_workbook(file_path)
            assert len(wb.sheetnames) == 1
            ws = wb.active
            # 行1: 标题, 行2: 副标题, 行3: 表头, 行4-5: 数据
            assert ws.cell(1, 1).value is not None  # 标题存在
            assert ws.cell(3, 1).value in ("部门", "dept_name")  # 表头行
            assert ws.cell(4, 1).value == "信息学院"
            assert ws.cell(5, 1).value == "机械学院"

    def test_generates_multiple_sheets(self):
        gen = ExcelGenerator()
        tool_results = [
            {
                "tool_name": "query_completion_rate",
                "result": {"breakdown": [{"dept": "A", "rate": 80.0}]},
            },
            {
                "tool_name": "query_learning_trend",
                "result": {"data_points": [{"date": "2026-01-01", "value": 10}]},
            },
        ]
        with tempfile.TemporaryDirectory() as tmpdir:
            output = gen.generate(tool_results, "报表", "全部", tmpdir)
            assert output is not None
            assert len(output["sheets"]) == 2

    def test_empty_tool_results_returns_none(self):
        gen = ExcelGenerator()
        with tempfile.TemporaryDirectory() as tmpdir:
            output = gen.generate([], "报表", "全部", tmpdir)
            assert output is None

    def test_conditional_formatting_applied(self):
        """验证完成率 < 60% 的单元格标红"""
        gen = ExcelGenerator()
        tool_results = [
            {
                "tool_name": "query_completion_rate",
                "result": {
                    "breakdown": [
                        {"dept_name": "优秀部门", "completion_rate": 85.0},
                        {"dept_name": "落后部门", "completion_rate": 42.0},
                    ]
                }
            }
        ]
        with tempfile.TemporaryDirectory() as tmpdir:
            output = gen.generate(tool_results, "报表", "全部", tmpdir)
            assert output is not None
            from openpyxl import load_workbook
            file_path = os.path.join(tmpdir, os.path.basename(output["file_url"]))
            wb = load_workbook(file_path)
            ws = wb.active
            # 行4列2 = 85.0 (>= 60, 不标红)
            # 行5列2 = 42.0 (< 60, 标红)
            cell_low = ws.cell(5, 2)
            assert cell_low.value == 42.0
            assert cell_low.font.color is not None  # 有颜色设置
```

- [ ] **Step 3: Run tests to verify they fail**

```bash
cd backend && python -m pytest tests/services/export/test_excel_generator.py -v
```
Expected: All tests FAIL — `ModuleNotFoundError` for `app.services.export.excel_generator`

- [ ] **Step 4: Implement ExcelGenerator**

Create `backend/app/services/export/excel_generator.py`:

```python
"""生成带格式的 Excel 报表 — 从工具查询的结构化数据生成 .xlsx 文件"""
import os
import re
import uuid
from datetime import datetime
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter


class ExcelGenerator:
    """从工具返回的结构化数据生成带格式的 Excel 报表。

    仅导出 list-of-dict 类型的数据字段 — 标量值（如 completion_rate=85.0）
    已在 AI 的文字回答中体现，不再重复导出。
    """

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
        "user_id": "用户ID", "dept_code": "部门代码",
        "courseware_code": "课件代码", "exam_code": "考试代码",
        "scope_type": "范围类型", "summary": "摘要",
    }

    # 常见字段名 → Sheet 中文名
    SHEET_NAME_MAP = {
        "breakdown": "明细数据",
        "learners": "学员列表",
        "data_points": "趋势数据",
        "students": "学生列表",
        "classes": "班级列表",
        "top_errors": "错误排行",
        "distribution": "分布统计",
        "org_stats": "机构统计",
    }

    # ── 预定义样式 ──────────────────────────────────────────
    _TITLE_FONT = Font(name="微软雅黑", size=14, bold=True, color="1f1f1f")
    _SUBTITLE_FONT = Font(name="微软雅黑", size=10, color="888888")
    _HEADER_FONT = Font(name="微软雅黑", size=10, bold=True, color="ffffff")
    _HEADER_FILL = PatternFill(start_color="1f1f1f", end_color="1f1f1f", fill_type="solid")
    _DATA_FONT = Font(name="微软雅黑", size=10)
    _RED_FONT = Font(name="微软雅黑", size=10, color="cc0000")
    _ALT_FILL = PatternFill(start_color="fafafa", end_color="fafafa", fill_type="solid")
    _THIN_BORDER = Border(
        left=Side(style="thin", color="dddddd"),
        right=Side(style="thin", color="dddddd"),
        top=Side(style="thin", color="dddddd"),
        bottom=Side(style="thin", color="dddddd"),
    )

    # ── 公开 API ────────────────────────────────────────────

    def generate(
        self,
        tool_results: list[dict],
        question: str,
        user_scope: str,
        report_dir: str,
    ) -> dict | None:
        """生成格式化的 .xlsx 文件。

        返回元数据 dict，如果没有可导出的表格数据则返回 None。
        """
        sheets_data = self._extract_sheets(tool_results)
        if not sheets_data:
            return None

        os.makedirs(report_dir, exist_ok=True)
        file_id = uuid.uuid4().hex[:12]
        file_name = self._derive_title(question) + ".xlsx"
        safe_name = f"{file_id}.xlsx"
        file_path = os.path.join(report_dir, safe_name)

        wb = Workbook()
        # 删除默认 sheet，用命名 sheet 替换
        if sheets_data:
            wb.remove(wb.active)

        for sheet_name, rows in sheets_data:
            ws = wb.create_sheet(title=sheet_name[:31])  # Excel sheet名限31字符
            self._write_sheet(ws, sheet_name, rows, question, user_scope)

        wb.save(file_path)
        file_size = os.path.getsize(file_path)

        total_rows = sum(len(rows) for _, rows in sheets_data)
        total_columns = max(
            (len(rows[0]) for _, rows in sheets_data if rows), default=0
        )

        return {
            "file_name": file_name,
            "file_url": f"/api/v1/reports/{safe_name}",
            "file_size": file_size,
            "sheets": [
                {
                    "name": name,
                    "rows": len(rows),
                    "columns": len(rows[0]) if rows else 0,
                }
                for name, rows in sheets_data
            ],
            "total_rows": total_rows,
            "total_columns": total_columns,
        }

    # ── 内部方法 ─────────────────────────────────────────────

    def _extract_sheets(
        self, tool_results: list[dict]
    ) -> list[tuple[str, list[dict]]]:
        """从工具结果中提取所有 list-of-dict 字段。

        返回 [(sheet_name, rows), ...] 列表。
        """
        sheets = []
        for tr in tool_results:
            result = tr.get("result", {})
            if not isinstance(result, dict):
                continue
            for key, val in result.items():
                if (
                    isinstance(val, list)
                    and len(val) > 0
                    and isinstance(val[0], dict)
                ):
                    sheet_name = self.SHEET_NAME_MAP.get(
                        key, self._field_to_chinese(key)
                    )
                    sheets.append((sheet_name, val))
        return sheets

    def _field_to_chinese(self, field: str) -> str:
        """英文字段名 → 中文列名，未映射的保留英文"""
        return self.FIELD_LABEL_MAP.get(field, field)

    def _derive_title(self, question: str) -> str:
        """从用户问题中提取报表标题"""
        noise = r"(帮我|请|生成|一个|一份|导出|下载|报表|Excel|excel|数据|的|吗|吧|一下)"
        cleaned = re.sub(noise, "", question).strip()
        if not cleaned:
            cleaned = "数据报表"
        return cleaned[:50]

    def _write_sheet(
        self,
        ws,
        sheet_name: str,
        rows: list[dict],
        question: str,
        user_scope: str,
    ):
        """填充单个 Sheet：标题 → 副标题 → 表头 → 数据 → 格式化"""
        if not rows:
            return

        columns = list(rows[0].keys())
        ncols = len(columns)
        nrows = len(rows)

        # 第1行: 标题（合并单元格）
        title = self._derive_title(question)
        ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=ncols)
        title_cell = ws.cell(1, 1, title)
        title_cell.font = self._TITLE_FONT
        title_cell.alignment = Alignment(horizontal="center", vertical="center")
        ws.row_dimensions[1].height = 30

        # 第2行: 副标题
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=ncols)
        subtitle_cell = ws.cell(2, 1, f"机构: {user_scope} | 生成时间: {now}")
        subtitle_cell.font = self._SUBTITLE_FONT
        subtitle_cell.alignment = Alignment(horizontal="center")
        ws.row_dimensions[2].height = 20

        # 第3行: 表头
        for ci, col_name in enumerate(columns, start=1):
            header = self._field_to_chinese(col_name)
            cell = ws.cell(3, ci, header)
            cell.font = self._HEADER_FONT
            cell.fill = self._HEADER_FILL
            cell.alignment = Alignment(horizontal="center", vertical="center")
        ws.row_dimensions[3].height = 22
        ws.freeze_panes = "A4"  # 冻结表头

        # 数据行（从第4行开始）
        for ri, row in enumerate(rows, start=4):
            for ci, col_name in enumerate(columns, start=1):
                value = row.get(col_name)
                cell = ws.cell(ri, ci, value)
                cell.font = self._DATA_FONT
                if ri % 2 == 0:  # 偶数行浅灰背景
                    cell.fill = self._ALT_FILL

        # 条件格式: 含"率"字的列 < 60 → 红色
        for ci, col_name in enumerate(columns, start=1):
            header_cn = self._field_to_chinese(col_name)
            if "率" in header_cn:
                for ri in range(4, 4 + nrows):
                    cell = ws.cell(ri, ci)
                    if isinstance(cell.value, (int, float)) and cell.value < 60:
                        cell.font = self._RED_FONT

        # 全表细线边框
        for ri in range(1, 4 + nrows):
            for ci in range(1, ncols + 1):
                ws.cell(ri, ci).border = self._THIN_BORDER

        # 自动列宽（取表头和前20行中最大值）
        for ci, col_name in enumerate(columns, start=1):
            max_len = len(self._field_to_chinese(col_name))
            sample = min(nrows, 20)
            for ri in range(4, 4 + sample):
                val = ws.cell(ri, ci).value
                if val is not None:
                    max_len = max(max_len, len(str(val)))
            ws.column_dimensions[get_column_letter(ci)].width = min(max_len + 4, 40)
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
cd backend && python -m pytest tests/services/export/test_excel_generator.py -v
```
Expected: All 8 tests PASS

- [ ] **Step 6: Commit**

```bash
git add backend/app/services/export/ backend/tests/services/export/
git commit -m "feat: add ExcelGenerator service with formatted xlsx output"
```

---

### Task 3: Intent Classification Changes

**Files:**
- Modify: `backend/app/services/ai/intent_definitions.py:29`
- Modify: `backend/app/schemas/intent.py:42-49`

**Interfaces:**
- Consumes: (none — independent change)
- Produces: `INTENT_DEFINITIONS` now includes `REPORT_GENERATION` entry
- Produces: `IntentResult.output_mode: str` (default `"analysis"`)

- [ ] **Step 1: Add REPORT_GENERATION intent definition**

Edit `backend/app/services/ai/intent_definitions.py` — add after the `ORG_STRUCTURE_QUERY` line (line 29):

```python
    {"intent": "REPORT_GENERATION",        "label": "报表导出",      "complexity": "moderate", "keywords": "报表/导出/生成Excel/生成excel/下载/导出数据/生成报告"},
```

- [ ] **Step 2: Add output_mode to IntentResult**

Edit `backend/app/schemas/intent.py` — add `output_mode` field to `IntentResult` class, at line 49 (after `clarification_question`):

```python
    output_mode: str = Field(default="analysis", description="analysis | report")
```

- [ ] **Step 3: Verify existing tests still pass**

```bash
cd backend && python -m pytest tests/services/ai/test_intent_classifier.py -v
```
Expected: Existing intent classifier tests still PASS

- [ ] **Step 4: Commit**

```bash
git add backend/app/services/ai/intent_definitions.py backend/app/schemas/intent.py
git commit -m "feat: add REPORT_GENERATION intent and output_mode field to IntentResult"
```

---

### Task 4: ReactEngine Enhancement

**Files:**
- Modify: `backend/app/services/ai/react_engine.py:18-105, 133-137, 232-233, 316-331`

**Interfaces:**
- Consumes: `IntentResult.output_mode: str`
- Produces: `ReactEngine.run()` accepts `output_mode: str = "analysis"` parameter
- Produces: `engine._tool_results: list[dict]` collected during ReAct loop (caller reads after loop)

- [ ] **Step 1: Add REPORT_MODE_APPENDIX constant**

Edit `backend/app/services/ai/react_engine.py` — add after the `REACT_SYSTEM_TEMPLATE` block (after line 105):

```python
REPORT_MODE_APPENDIX = """## 报表模式
用户需要生成可下载的Excel报表。请：
1. 优先使用能返回表格数据的工具（如 query_completion_rate、query_exam_performance 等）
2. 在最终回答中概述报表内容（包含哪些数据、大概行数）
3. 在回答末尾提示用户："报表已生成，请从右侧面板下载Excel文件"
4. 回答保持简洁——详细数据在Excel中，这里只需给出关键统计结论"""
```

- [ ] **Step 2: Update _build_system_prompt to accept output_mode**

Edit `_build_system_prompt` method (line 316). Change signature and add conditional appendix:

```python
    def _build_system_prompt(self, question: str, intent_result, output_mode: str = "analysis") -> str:
        """Build the full system prompt from template parts."""
        history_text = self._format_history()
        intent_text = (
            f"intent={intent_result.intent}, "
            f"complexity={intent_result.complexity}"
        )
        base = REACT_SYSTEM_TEMPLATE.format(
            user_name=self._user_ctx.user_name,
            role_level=self._user_ctx.role_level,
            dept_code=self._user_ctx.dept_code or "N/A",
            current_time=time.strftime("%Y-%m-%d %H:%M"),
            chat_history=history_text,
            input=question,
            schema_context=self._schema_context,
            tools=self._format_tools(),
            intent_info=intent_text,
        )
        if output_mode == "report":
            base += "\n\n" + REPORT_MODE_APPENDIX
        return base
```

- [ ] **Step 3: Update run() signature and call**

Edit `run()` method (line 133). Change:

```python
    async def run(
        self, question: str, intent_result, output_mode: str = "analysis"
    ) -> AsyncGenerator[SSEEvent, None]:
```

Update the `_build_system_prompt` call on line 137:

```python
        system_prompt = self._build_system_prompt(question, intent_result, output_mode)
```

- [ ] **Step 4: Collect tool results during loop**

After line 137 (`tool_by_name = ...`), initialize collector:

```python
        self._tool_results: list[dict] = []
```

After line 233 (`observation = json.dumps(result, ensure_ascii=False)`), save result:

```python
                        self._tool_results.append({
                            "tool_name": tool_name,
                            "result": result,
                        })
```

- [ ] **Step 5: Run existing tests to verify no regressions**

```bash
cd backend && python -m pytest tests/services/ai/ -v
```
Expected: Existing tests PASS

- [ ] **Step 6: Commit**

```bash
git add backend/app/services/ai/react_engine.py
git commit -m "feat: add output_mode parameter, tool result collection, and report prompt to ReactEngine"
```

---

### Task 5: SSE Integration in ai_query.py

**Files:**
- Modify: `backend/app/api/v1/ai_query.py:94-107, 130, 170-178`
- Modify: `backend/app/services/ai/intent_classifier.py` (add report keyword detection)

**Interfaces:**
- Consumes: `IntentResult.output_mode`, `ReactEngine.run(output_mode=)`, `engine._tool_results`
- Consumes: `ExcelGenerator.generate()`
- Produces: `download_ready` SSE event in event stream

- [ ] **Step 1: Add report keyword detection in IntentClassifier**

Edit `backend/app/services/ai/intent_classifier.py`. In the `classify()` method, after the `IntentResult` is constructed and before return, add:

```python
        # 检测报表关键词，设置 output_mode
        report_keywords = ["报表", "导出", "生成Excel", "生成excel", "下载", "导出数据", "生成报告"]
        if any(kw in question for kw in report_keywords):
            intent_result.output_mode = "report"
```

(Note: read the actual classifier to find the exact insertion point — it should be right where `intent_result` variable exists and before the `return` statement.)

- [ ] **Step 2: Extract output_mode and pass to ReactEngine**

Edit `backend/app/api/v1/ai_query.py`. After the `intent_resolved` yield (around line 134), add:

```python
        output_mode = getattr(intent_result, "output_mode", "analysis")
        print(f"[Backend SSE] output_mode={output_mode}", flush=True)
```

Then update the `engine.run()` call on line 170:

```python
        async for event in engine.run(q, intent_result, output_mode=output_mode):
```

- [ ] **Step 3: Add Excel generation post-processing block**

After the ReAct engine loop (after line 178, before the `[6] Final events` section), add:

```python
        # [5b] Excel 报表生成（后处理，不消耗 ReAct 步骤）
        if output_mode == "report":
            tool_results = getattr(engine, "_tool_results", [])
            if tool_results:
                print(f"[Backend SSE] [5b] 生成Excel报表, 工具结果数: {len(tool_results)}", flush=True)
                try:
                    from app.services.export.excel_generator import ExcelGenerator
                    excel_gen = ExcelGenerator()
                    output = await asyncio.to_thread(
                        excel_gen.generate,
                        tool_results, q,
                        current_user.dept_code or "全部机构",
                        settings.REPORT_DIR,
                    )
                    if output:
                        print(f"[Backend SSE] [5b] Excel生成成功: {output['file_name']}", flush=True)
                        yield format_sse("download_ready", {
                            "file_name": output["file_name"],
                            "file_url": output["file_url"],
                            "file_size": output["file_size"],
                            "sheets": output["sheets"],
                            "total_rows": output["total_rows"],
                            "total_columns": output["total_columns"],
                        })
                    else:
                        print(f"[Backend SSE] [5b] 无可导出的表格数据", flush=True)
                except Exception as exc:
                    print(f"[Backend SSE] [5b] Excel生成失败: {exc}", flush=True)
                    yield format_sse("error", {
                        "code": "EXCEL_GENERATION_FAILED",
                        "message": f"报表生成失败: {str(exc)[:100]}",
                        "recoverable": False,
                    })
```

- [ ] **Step 4: Verify SSE format for download_ready**

```bash
cd backend && python -c "
from app.schemas.sse_events import format_sse
event = format_sse('download_ready', {'file_name': 'test.xlsx', 'file_url': '/api/v1/reports/test.xlsx', 'file_size': 1024, 'sheets': [], 'total_rows': 0, 'total_columns': 0})
assert 'event: download_ready' in event
assert 'data:' in event
print('OK')
"
```
Expected: `OK`

- [ ] **Step 5: Commit**

```bash
git add backend/app/api/v1/ai_query.py backend/app/services/ai/intent_classifier.py
git commit -m "feat: wire Excel generation into SSE event stream for report mode"
```

---

### Task 6: Download API & File Cleanup

**Files:**
- Create: `backend/app/api/v1/reports.py`
- Create: `backend/app/jobs/cleanup_reports.py`
- Modify: `backend/app/main.py`

**Interfaces:**
- Produces: `GET /api/v1/reports/{file_name}` → FileResponse (200) or 404
- Produces: `cleanup_expired_reports()` async function (for APScheduler)

- [ ] **Step 1: Create download API endpoint**

Create `backend/app/api/v1/reports.py`:

```python
"""下载端点 — 提供已生成的报表文件下载"""
import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from app.core.config import settings

router = APIRouter()


@router.get("/reports/{file_name}")
async def download_report(file_name: str):
    """下载之前生成的报表文件。文件在 REPORT_TTL_HOURS 后自动清理。"""
    # 防止路径遍历攻击
    if ".." in file_name or "/" in file_name or "\\" in file_name:
        raise HTTPException(status_code=400, detail="Invalid file name")

    file_path = os.path.join(settings.REPORT_DIR, file_name)
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=404,
            detail="文件不存在或已过期，请重新提问生成报表",
        )

    return FileResponse(
        file_path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=file_name,
    )
```

- [ ] **Step 2: Create file cleanup job**

Create `backend/app/jobs/cleanup_reports.py`:

```python
"""定期清理过期的报表文件"""
import os
import time
import logging

logger = logging.getLogger(__name__)


async def cleanup_expired_reports():
    """删除超过 REPORT_TTL_HOURS 的报表文件"""
    from app.core.config import settings

    report_dir = settings.REPORT_DIR
    if not os.path.exists(report_dir):
        return

    cutoff = time.time() - settings.REPORT_TTL_HOURS * 3600
    deleted = 0
    for f in os.listdir(report_dir):
        fp = os.path.join(report_dir, f)
        if os.path.isfile(fp) and os.path.getmtime(fp) < cutoff:
            try:
                os.remove(fp)
                deleted += 1
            except OSError:
                pass

    if deleted:
        logger.info(f"已清理 {deleted} 个过期报表文件")
```

- [ ] **Step 3: Register route and cleanup job in main.py**

Read `backend/app/main.py`. Add route registration alongside existing router includes:

```python
from app.api.v1.reports import router as reports_router
app.include_router(reports_router, prefix="/api/v1")
```

In the lifespan function, add cleanup job to existing APScheduler setup:

```python
from app.jobs.cleanup_reports import cleanup_expired_reports
scheduler.add_job(
    cleanup_expired_reports,
    "interval",
    hours=1,
    id="cleanup_reports",
    replace_existing=True,
)
```

- [ ] **Step 4: Verify routes**

```bash
cd backend && python -c "
from app.main import app
routes = [r.path for r in app.routes if hasattr(r, 'path')]
print([r for r in routes if 'report' in r])
"
```
Expected: `['/api/v1/reports/{file_name}']`

- [ ] **Step 5: Commit**

```bash
git add backend/app/api/v1/reports.py backend/app/jobs/cleanup_reports.py backend/app/main.py
git commit -m "feat: add report download endpoint and periodic file cleanup job"
```

---

### Task 7: Frontend Types, Store & SSE Handler

**Files:**
- Modify: `frontend/src/types/chat.ts`
- Modify: `frontend/src/stores/chatStore.ts`
- Modify: `frontend/src/hooks/useAIQuery.ts`

**Interfaces:**
- Produces: `SheetMeta`, `DownloadInfo` TypeScript interfaces
- Produces: `Message.downloads?: DownloadInfo[]`
- Produces: `currentDownloads: DownloadInfo[]` store state + `addDownload()` / `clearCurrentDownloads()`
- Produces: `download_ready` SSE event → store dispatch

- [ ] **Step 1: Add TypeScript types**

Edit `frontend/src/types/chat.ts` — add new interfaces after existing types:

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

Add `downloads` optional field to `Message` interface:

```typescript
export interface Message {
  id: string;
  role: "user" | "ai" | "system";
  content: string;
  timestamp: number;
  steps?: ThinkingStep[];
  charts?: ChartSpec[];
  downloads?: DownloadInfo[];       // 报表下载信息
  clarificationOptions?: ClarificationOption[];
}
```

- [ ] **Step 2: Add store state and actions**

Edit `frontend/src/stores/chatStore.ts`. Read the current store — add to state interface:

```typescript
currentDownloads: DownloadInfo[];
```

In initial state:
```typescript
currentDownloads: [],
```

Implement actions:

```typescript
addDownload: (d: DownloadInfo) =>
  set((s) => ({ currentDownloads: [...s.currentDownloads, d] })),

clearCurrentDownloads: () => set({ currentDownloads: [] }),
```

In `prepareNewRound()` — add `clearCurrentDownloads()` alongside existing clear calls.

In `finalizeRound()` — attach downloads to the last AI message (same pattern as charts):

```typescript
const { currentDownloads, updateLastAiMessage } = get();
if (currentDownloads.length > 0) {
  updateLastAiMessage({ downloads: [...currentDownloads] } as Partial<Message>);
}
```

Also add downloads to the round object saved to `rounds[]` (follow the exact pattern used for charts).

- [ ] **Step 3: Handle download_ready SSE event**

Edit `frontend/src/hooks/useAIQuery.ts`. In the `dispatch()` function, add case:

```typescript
case "download_ready":
  useChatStore.getState().addDownload({
    fileName: data.file_name,
    fileUrl: data.file_url,
    fileSize: data.file_size,
    sheets: data.sheets || [],
    totalRows: data.total_rows,
    totalColumns: data.total_columns,
  });
  break;
```

- [ ] **Step 4: Verify TypeScript compiles**

```bash
cd frontend && npx tsc --noEmit
```
Expected: No new type errors from our changes

- [ ] **Step 5: Commit**

```bash
git add frontend/src/types/chat.ts frontend/src/stores/chatStore.ts frontend/src/hooks/useAIQuery.ts
git commit -m "feat: add DownloadInfo types, store state, and SSE handler for download_ready"
```

---

### Task 8: Frontend UI Components

**Files:**
- Modify: `frontend/src/components/ai/ReasoningPanel.tsx`
- Modify: `frontend/src/components/ai/MessageBubble.tsx`

**Interfaces:**
- Consumes: `useChatStore().currentDownloads` (ReasoningPanel)
- Consumes: `message.downloads` (MessageBubble)

- [ ] **Step 1: Add formatBytes helper**

Add at top of `ReasoningPanel.tsx` (before the component function):

```typescript
function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1048576) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1048576).toFixed(1)} MB`;
}
```

- [ ] **Step 2: Add download section to ReasoningPanel**

Read `currentDownloads` from store at the top of the ReasoningPanel component:

```typescript
const currentDownloads = useChatStore((s) => s.currentDownloads);
```

After the charts rendering section, add:

```tsx
{/* 报表下载区域 */}
{currentDownloads.length > 0 && (
  <div className="mt-4">
    <h4 className="text-xs font-medium text-text-subdued uppercase tracking-wider mb-2">
      📥 报表下载
    </h4>
    {currentDownloads.map((dl, i) => (
      <div
        key={i}
        className="p-3 bg-bg-card rounded-lg border border-border mb-2"
      >
        <div className="text-sm font-medium text-text-primary">
          {dl.fileName}
        </div>
        <div className="text-xs text-text-subdued mt-1">
          {dl.sheets.length}个Sheet · {dl.totalRows.toLocaleString()}行 · {formatBytes(dl.fileSize)}
        </div>
        <a
          href={dl.fileUrl}
          download
          className="inline-block mt-2 px-4 py-1.5 bg-accent text-black text-xs font-medium rounded-full hover:opacity-90 transition-opacity"
        >
          下载 Excel
        </a>
      </div>
    ))}
  </div>
)}
```

- [ ] **Step 3: Add statistics card to MessageBubble**

Edit `MessageBubble.tsx`. Add import at top:

```typescript
import { FileSpreadsheet } from "lucide-react";
```

After the markdown content rendering and before `MessageActions`, add:

```tsx
{/* 报表统计摘要卡片 */}
{message.role === "ai" && message.downloads && message.downloads.length > 0 && (
  <div className="mt-3 space-y-2">
    {message.downloads.map((dl, i) => (
      <div
        key={i}
        className="p-3 bg-bg-card rounded-lg border border-border"
      >
        <div className="flex items-center gap-2 text-sm">
          <FileSpreadsheet size={16} className="text-accent" />
          <span className="font-medium text-text-primary">{dl.fileName}</span>
        </div>
        <div className="mt-2 grid grid-cols-3 gap-2 text-xs text-text-subdued">
          <div>
            <span className="block text-text-secondary font-medium">
              {dl.totalRows.toLocaleString()}
            </span>
            <span>总行数</span>
          </div>
          <div>
            <span className="block text-text-secondary font-medium">
              {dl.totalColumns}
            </span>
            <span>总列数</span>
          </div>
          <div>
            <span className="block text-text-secondary font-medium">
              {dl.fileSize < 1024
                ? `${dl.fileSize} B`
                : dl.fileSize < 1048576
                  ? `${(dl.fileSize / 1024).toFixed(1)} KB`
                  : `${(dl.fileSize / 1048576).toFixed(1)} MB`}
            </span>
            <span>文件大小</span>
          </div>
        </div>
        <div className="mt-1.5 text-xs text-text-subdued">
          {dl.sheets.map((s) => `${s.name}(${s.rows}行×${s.columns}列)`).join(" · ")}
        </div>
      </div>
    ))}
  </div>
)}
```

- [ ] **Step 4: Verify TypeScript compiles**

```bash
cd frontend && npx tsc --noEmit
```
Expected: No new type errors

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/ai/ReasoningPanel.tsx frontend/src/components/ai/MessageBubble.tsx
git commit -m "feat: add report download card in ReasoningPanel and statistics card in MessageBubble"
```

---

## Verification

After all tasks are implemented:

- [ ] **Backend unit tests**:
```bash
cd backend && python -m pytest tests/services/export/test_excel_generator.py tests/services/ai/test_intent_classifier.py -v
```

- [ ] **Backend manual integration check**:
```bash
cd backend && python -c "
from app.services.export.excel_generator import ExcelGenerator
import tempfile
gen = ExcelGenerator()
results = [{'tool_name': 'q1', 'result': {'breakdown': [{'dept': 'A', 'rate': 80.0}]}}]
with tempfile.TemporaryDirectory() as d:
    out = gen.generate(results, '生成Q1报表', '全机构', d)
    assert out and out['total_rows'] == 1
    print('PASS')
"
```

- [ ] **Frontend build**:
```bash
cd frontend && npx tsc --noEmit && npx vite build
```

- [ ] **End-to-end manual test**:
1. 启动后端: `cd backend && uvicorn app.main:app --reload`
2. 启动前端: `cd frontend && npm run dev`
3. 输入: "帮我生成各部门完成率报表"
4. 验证: 左侧显示 AI 分析文字 + 统计卡片（行数/列数/文件大小）
5. 验证: 右侧 ReasoningPanel 显示 "📥 报表下载" 卡片
6. 点击 "下载 Excel" → 浏览器下载 .xlsx 文件
7. 打开 .xlsx → 验证格式（标题、副标题、表头、数据、条件格式）
8. 输入一个非报表问题 → 验证正常流程不受影响（无下载卡片）
