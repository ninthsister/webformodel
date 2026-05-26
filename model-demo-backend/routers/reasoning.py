from typing import Optional

from fastapi import APIRouter, HTTPException, Request

from core.config import PATIENT_ROOT
from services.file_service import get_request_language, read_localized_json_file


router = APIRouter()


@router.get("/api/patient/reasoning/{patient_id}")
def get_patient_reasoning(
    patient_id: str,
    request: Request,
    language: Optional[str] = "zh",
):
    lang = get_request_language(request, language)
    print(f"查询病人 {patient_id} 的推理结果，language={lang}")

    if not patient_id:
        raise HTTPException(status_code=400, detail="patient_id 不能为空")

    reasoning_path = (
        PATIENT_ROOT
        / patient_id
        / "reasoning"
        / "reasoning.json"
    )

    reasoning_data = read_localized_json_file(
        reasoning_path,
        "推理",
        lang,
    )

    # 兼容两种格式：
    # 旧格式：[
    #   {...},
    #   {...}
    # ]
    #
    # 新格式：{
    #   "reasoning": [
    #       {...},
    #       {...}
    #   ]
    # }
    if isinstance(reasoning_data, dict):
        reasoning = reasoning_data.get("reasoning", [])

        # 兼容可能写成 reasoningItems 的情况
        if not reasoning:
            reasoning = reasoning_data.get("reasoningItems", [])

    elif isinstance(reasoning_data, list):
        reasoning = reasoning_data

    else:
        reasoning = []

    print(f"成功读取病人 {patient_id} 的推理结果")

    return {
        "patient_id": patient_id,
        "language": lang,

        # 前端主要使用这个
        "reasoning": reasoning,

        # 兼容旧前端可能使用的字段
        "reasoningItems": reasoning,

        # 保留原始 Ollama 输出，方便调试
        "raw": reasoning_data,
    }