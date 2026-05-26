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

    # 兼容两种格式：
    # 旧格式：[
    #   {...},
    #   {...}
    # ]
    #
    # 新格式：{
    #   "assessment": [
    #       {...},
    #       {...}
    #   ]
    # }
    if isinstance(assessment_data, dict):
        assessments = assessment_data.get("assessment", [])

        # 兼容可能写成 assessments 的情况
        if not assessments:
            assessments = assessment_data.get("assessments", [])

    elif isinstance(assessment_data, list):
        assessments = assessment_data

    else:
        assessments = []

    print(f"成功读取病人 {patient_id} 的评估结果")

    return {
        "patient_id": patient_id,
        "language": lang,

        # 前端主要用这个
        "assessments": assessments,

        # 保留原始 dict，方便你调试 Ollama 原始输出
        "raw": assessment_data,
    }