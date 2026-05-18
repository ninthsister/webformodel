from datetime import datetime
from threading import Thread

from fastapi import APIRouter, HTTPException

from core.config import PATIENT_ROOT
from schemas.analysis import StartAnalysisRequest
from services.analysis_service import run_analysis_task
from services.patient_service import read_patient_info, write_patient_info


router = APIRouter()


@router.post("/api/analysis/start")
def start_analysis(req: StartAnalysisRequest):
    patient_id = req.patientId

    if req.signal != "start_analysis":
        raise HTTPException(
            status_code=400,
            detail="signal 必须是 start_analysis",
        )

    patient_dir = PATIENT_ROOT / patient_id
    info_path = patient_dir / "info.json"

    if not patient_dir.exists() or not patient_dir.is_dir():
        raise HTTPException(
            status_code=404,
            detail=f"未找到病人数据目录：{patient_id}",
        )

    if not info_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"未找到病人信息文件：{patient_id}/info.json",
        )

    info = read_patient_info(patient_id)
    current_status = info.get("analysis", {}).get("status")

    if current_status == "analyzing":
        return {
            "success": True,
            "message": "该病人正在分析中，请勿重复提交",
            "patientId": patient_id,
            "analysis": info.get("analysis"),
        }

    info["analysis"] = {
        "status": "analyzing",
        "message": "正在分析",
        "started_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "finished_at": None,
    }

    write_patient_info(patient_id, info)

    thread = Thread(
        target=run_analysis_task,
        args=(patient_id,),
        daemon=True,
    )
    thread.start()

    print(f"收到开始分析信号：{patient_id}")

    return {
        "success": True,
        "message": "已收到开始分析信号，分析任务已启动",
        "patientId": patient_id,
        "analysis": info["analysis"],
    }


@router.get("/api/analysis/status/{patient_id}")
def get_analysis_status(patient_id: str):
    info = read_patient_info(patient_id)

    return {
        "success": True,
        "patientId": patient_id,
        "analysis": info.get(
            "analysis",
            {
                "status": "not_started",
                "message": "尚未开始分析",
            },
        ),
    }