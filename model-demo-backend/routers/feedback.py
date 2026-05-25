from datetime import datetime

from fastapi import APIRouter, HTTPException, Request

from core.config import PATIENT_ROOT
from schemas.feedback import DoctorFeedbackRequest
from services.file_service import get_request_language, write_json_file


router = APIRouter()


def _text(lang: str, zh: str, en: str) -> str:
    return en if lang == "en" else zh


@router.post("/api/patient/{patient_id}/doctor-feedback")
def save_doctor_feedback(
    patient_id: str,
    payload: DoctorFeedbackRequest,
    request: Request,
):
    lang = get_request_language(request, payload.language)
    print(f"保存病人 {patient_id} 的医生反馈，language={lang}")

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
        / f"doctor_feedback_{lang}.json"
    )

    feedback_data = {
        "patient_id": patient_id,
        "language": lang,
        "feedback": payload.feedback,
        "comment": payload.comment,
        "saved_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    write_json_file(feedback_path, feedback_data, "医生反馈")

    print("医生反馈保存路径:", feedback_path)

    return {
        "patient_id": patient_id,
        "language": lang,
        "message": _text(lang, "医生反馈保存成功", "Doctor feedback saved successfully"),
        "feedback_path": str(feedback_path),
        "data": feedback_data,
    }
