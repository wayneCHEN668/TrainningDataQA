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
