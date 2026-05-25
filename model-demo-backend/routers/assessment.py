from typing import Optional

from fastapi import APIRouter, HTTPException, Request

from core.config import PATIENT_ROOT
from services.file_service import get_request_language, read_localized_json_file


router = APIRouter()


@router.get("/api/patient/{patient_id}/assessment")
def get_patient_assessment(
    patient_id: str,
    request: Request,
    language: Optional[str] = "zh",
):
    lang = get_request_language(request, language)
    print(f"查询病人 {patient_id} 的评估结果，language={lang}")

    if not patient_id:
        raise HTTPException(status_code=400, detail="patient_id 不能为空")

    assessment_path = (
        PATIENT_ROOT
        / patient_id
        / "assessment"
        / "assessment.json"
    )

    assessment_data = read_localized_json_file(
        assessment_path,
        "评估",
        lang,
    )

    print(f"成功读取病人 {patient_id} 的评估结果")

    return {
        "patient_id": patient_id,
        "language": lang,
        "assessments": assessment_data,
    }
