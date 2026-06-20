"""下载端点 — 提供已生成的报表文件下载"""
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from app.api.deps import get_current_user
from app.core.config import settings
from app.schemas.auth import UserContext

router = APIRouter()


@router.get("/reports/{file_name}")
async def download_report(
    file_name: str,
    current_user: UserContext = Depends(get_current_user),
    display_name: str = Query(default="", description="Human-readable filename for browser download dialog"),
):
    """下载之前生成的报表文件。文件在 REPORT_TTL_HOURS 后自动清理。"""
    report_root = Path(settings.REPORT_DIR).resolve()
    file_path = (report_root / file_name).resolve()

    # 防止路径遍历攻击：确保解析后路径在 REPORT_DIR 内
    if report_root not in file_path.parents and file_path != report_root:
        raise HTTPException(status_code=400, detail="Invalid file name")

    if not file_path.is_file():
        raise HTTPException(
            status_code=404,
            detail="文件不存在或已过期，请重新提问生成报表",
        )

    download_name = display_name if display_name else file_name
    return FileResponse(
        str(file_path),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=download_name,
    )
