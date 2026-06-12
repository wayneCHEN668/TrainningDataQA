import pytest
import pytest_asyncio
from app.services.ai.schema_index import SchemaIndexService


YAML_PATH = "../doc/db_table_index.yaml"


@pytest_asyncio.fixture
async def svc():
    s = SchemaIndexService(yaml_path=YAML_PATH)
    await s.load()
    return s


@pytest.mark.asyncio
async def test_loads_module_index(svc):
    text = svc.get_module_index_text()
    assert "M1_" in text
    assert "M11_" in text
    assert "Available Data Modules" in text


@pytest.mark.asyncio
async def test_intent_routing_known(svc):
    modules = svc.get_modules_for_intent("EXAM_SCORE_QUERY")
    assert "M5_考试系统" in modules


@pytest.mark.asyncio
async def test_intent_routing_unknown_returns_default(svc):
    modules = svc.get_modules_for_intent("NONEXISTENT_INTENT")
    assert len(modules) == 2
    assert "M10_" in modules[0] or "M9_" in modules[0]


@pytest.mark.asyncio
async def test_table_summaries_full(svc):
    text = svc.get_table_summaries_text(
        modules=["M5_考试系统"], compact=False
    )
    assert "exam_session" in text
    assert "exam_enrollment" in text
    assert "### " in text  # full mode has section headers


@pytest.mark.asyncio
async def test_table_summaries_compact(svc):
    text = svc.get_table_summaries_text(
        modules=["M5_考试系统"], compact=True
    )
    assert "exam_session" in text
    assert "### " not in text  # compact mode skips headers


@pytest.mark.asyncio
async def test_table_summaries_filters_by_module(svc):
    text = svc.get_table_summaries_text(
        modules=["M1_组织架构"], compact=False
    )
    assert "org" in text.lower()
    # M5 tables should NOT appear when only M1 is loaded
    assert "exam_session" not in text


@pytest.mark.asyncio
async def test_blacklist_blocks_forbidden(svc):
    ok, msg = svc.validate_query_tables("SELECT * FROM users")
    assert not ok
    assert "users" in msg


@pytest.mark.asyncio
async def test_blacklist_blocks_cache(svc):
    ok, msg = svc.validate_query_tables("SELECT * FROM cache")
    assert not ok


@pytest.mark.asyncio
async def test_blacklist_allows_business_table(svc):
    ok, msg = svc.validate_query_tables("SELECT * FROM user_info")
    assert ok


@pytest.mark.asyncio
async def test_all_22_intents_route(svc):
    routing = svc._index.get("INTENT_MODULE_ROUTING", {})
    assert len(routing) == 22, f"Expected 22 intents, got {len(routing)}"
