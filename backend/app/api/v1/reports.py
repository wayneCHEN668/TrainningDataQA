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
