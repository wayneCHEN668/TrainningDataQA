"""Daily evolution job: analyze QA logs + unmatched queries -> report."""
import logging
from datetime import date
from pathlib import Path
from app.core.database import AsyncSessionLocal
from app.core.redis import redis_pool
from app.services.ai.evolution_analyzer import EvolutionAnalyzer

logger = logging.getLogger(__name__)


async def run_daily_evolution():
    """Daily 02:00: analyze qa_session_log + unmatched_queries.md -> generate report."""
    try:
        async with AsyncSessionLocal() as db:
            analyzer = EvolutionAnalyzer(db)
            report = await analyzer.analyze(days=7)

            # Write markdown report
            today = date.today().isoformat()
            report_dir = Path("../doc/analysis")
            report_dir.mkdir(parents=True, exist_ok=True)
            report_path = report_dir / f"{today}-evolution-report.md"
            report_path.write_text(report.to_markdown(), encoding="utf-8")

            # Cache to Redis
            if redis_pool:
                await redis_pool.set(
                    "evolution_stats:daily",
                    report.to_summary_json(),
                    ex=86400 * 7,
                )

            logger.info("Evolution report generated: %s", report_path)
    except Exception:
        logger.exception("Evolution job failed")
