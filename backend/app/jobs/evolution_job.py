"""Daily evolution job: analyze QA logs + unmatched queries -> report."""
import logging
from datetime import date
from pathlib import Path
from app.core.database import AsyncSessionLocal
from app.services.ai.evolution_analyzer import EvolutionAnalyzer

logger = logging.getLogger(__name__)

EVOLUTION_DIR = Path("../doc/evolution")


async def run_daily_evolution():
    """Daily 02:00: analyze qa_session_log + unmatched_queries.md -> generate report."""
    try:
        async with AsyncSessionLocal() as db:
            analyzer = EvolutionAnalyzer(db)
            report = await analyzer.analyze(days=7)

            # Ensure output directory
            EVOLUTION_DIR.mkdir(parents=True, exist_ok=True)

            # Write markdown report
            today = date.today().isoformat()
            md_path = EVOLUTION_DIR / f"{today}-evolution-report.md"
            md_path.write_text(report.to_markdown(), encoding="utf-8")

            # Write JSON summary (for admin API)
            json_path = EVOLUTION_DIR / f"{today}-summary.json"
            json_path.write_text(report.to_summary_json(), encoding="utf-8")

            logger.info("Evolution report generated: %s", md_path)
    except Exception:
        logger.exception("Evolution job failed")
