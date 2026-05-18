from datetime import datetime

from fastapi import APIRouter, HTTPException

from core.config import PATIENT_ROOT
from schemas.feedback import DoctorFeedbackRequest
from services.file_service import write_json_file


router = APIRouter()


@router.post("/api/patient/{patient_id}/doctor-feedback")
def save_doctor_feedback(patient_id: str, payload: DoctorFeedbackRequest):
    print(f"保存病人 {patient_id} 的医生反馈")

    if not patient_id:
        raise HTTPException(status_code=400, detail="patient_id 不能为空")

    patient_dir = PATIENT_ROOT / patient_id

    if not patient_dir.exists() or not patient_dir.is_dir():
        raise HTTPException(
            status_code=404,
            detail=f"未找到病人目录: {patient_dir}",
        )

    feedback_path = (
        patient_dir
        / "doctor_feedback"
        / "doctor_feedback.json"
    )

    feedback_data = {
        "patient_id": patient_id,
        "feedback": payload.feedback,
        "comment": payload.comment,
        "saved_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    write_json_file(feedback_path, feedback_data, "医生反馈")

    print("医生反馈保存路径:", feedback_path)

    return {
        "patient_id": patient_id,
        "message": "医生反馈保存成功",
        "feedback_path": str(feedback_path),
        "data": feedback_data,
    }