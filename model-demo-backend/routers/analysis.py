from datetime import datetime
from threading import Thread
from typing import Optional

from fastapi import APIRouter, HTTPException, Request

from core.config import PATIENT_ROOT
from schemas.analysis import StartAnalysisRequest
from services.analysis_service import run_analysis_task
from services.file_service import get_localized_json_path, get_request_language
from services.patient_service import read_patient_info, write_patient_info


router = APIRouter()


def _text(lang: str, zh: str, en: str) -> str:
    return en if lang == "en" else zh


@router.post("/api/analysis/start")
def start_analysis(req: StartAnalysisRequest, request: Request):
    patient_id = req.patientId
    lang = get_request_language(request, req.language)

    if req.signal != "start_analysis":
        raise HTTPException(
            status_code=400,
            detail="signal 必须是 start_analysis",
        )

    patient_dir = PATIENT_ROOT / patient_id
    info_path = get_localized_json_path(patient_dir / "info.json", lang)

    if not patient_dir.exists() or not patient_dir.is_dir():
        raise HTTPException(
            status_code=404,
            detail=f"未找到病人数据目录：{patient_id}",
        )

    if not info_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"未找到病人信息文件：{patient_id}/{info_path.name}",
        )

    # Analysis status is stored in the corresponding language file, e.g. info_zh.json / info_en.json.
    info = read_patient_info(patient_id, lang)
    current_status = info.get("analysis", {}).get("status")

    if current_status == "analyzing":
        return {
            "success": True,
            "language": lang,
            "message": _text(
                lang,
                "该病人正在分析中，请勿重复提交",
                "This patient is already being analyzed. Please do not submit again.",
            ),
            "patientId": patient_id,
            "analysis": info.get("analysis"),
        }

    info["analysis"] = {
        "status": "analyzing",
        "message": _text(lang, "正在分析", "Analyzing"),
        "started_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "finished_at": None,
    }

    write_patient_info(patient_id, info, lang)

    thread = Thread(
        target=run_analysis_task,
        args=(patient_id, lang),
        daemon=True,
    )
    thread.start()

    print(f"收到开始分析信号：{patient_id}，language={lang}")

    return {
        "success": True,
        "language": lang,
        "message": _text(
            lang,
            "已收到开始分析信号，分析任务已启动",
            "Analysis request received. The analysis task has started.",
        ),
        "patientId": patient_id,
        "analysis": info["analysis"],
    }


@router.get("/api/analysis/status/{patient_id}")
def get_analysis_status(
    patient_id: str,
    request: Request,
    language: Optional[str] = "zh",
):
    lang = get_request_language(request, language)
    info = read_patient_info(patient_id, lang)

    analysis = info.get(
        "analysis",
        {
            "status": "not_started",
            "message": _text(lang, "尚未开始分析", "Analysis has not started"),
        },
    )

    status = analysis.get("status")
    localized_message = {
        "not_started": _text(lang, "尚未开始分析", "Analysis has not started"),
        "analyzing": _text(lang, "正在分析", "Analyzing"),
        "completed": _text(lang, "分析完成", "Analysis completed"),
        "failed": _text(lang, "分析失败", "Analysis failed"),
    }.get(status, analysis.get("message"))

    analysis = {**analysis, "message": localized_message}

    return {
        "success": True,
        "language": lang,
        "patientId": patient_id,
        "analysis": analysis,
    }
