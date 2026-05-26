from typing import Optional

from fastapi import APIRouter, HTTPException, Request

from core.config import PATIENT_ROOT
from services.file_service import get_request_language, read_localized_json_file


router = APIRouter()


@router.get("/api/patient/{patient_id}/key-evidence")
def get_patient_key_evidence(
    patient_id: str,
    request: Request,
    language: Optional[str] = "zh",
):
    lang = get_request_language(request, language)
    print(f"查询病人 {patient_id} 的关键证据，language={lang}")

    if not patient_id:
        raise HTTPException(status_code=400, detail="patient_id 不能为空")

    keyevidence_path = (
        PATIENT_ROOT
        / patient_id
        / "keyevidence"
        / "keyevidence.json"
    )

    keyevidence_data = read_localized_json_file(
        keyevidence_path,
        "关键证据",
        lang,
    )

    # 兼容两种格式：
    # 旧格式：[
    #   {...},
    #   {...}
    # ]
    #
    # 新格式：{
    #   "keyevidence": [
    #       {...},
    #       {...}
    #   ]
    # }
    if isinstance(keyevidence_data, dict):
        evidence_items = keyevidence_data.get("keyevidence", [])

        # 兼容可能写成 keyEvidence / evidenceItems 的情况
        if not evidence_items:
            evidence_items = keyevidence_data.get("keyEvidence", [])

        if not evidence_items:
            evidence_items = keyevidence_data.get("evidenceItems", [])

    elif isinstance(keyevidence_data, list):
        evidence_items = keyevidence_data

    else:
        evidence_items = []

    print(f"成功读取病人 {patient_id} 的关键证据")

    return {
        "patient_id": patient_id,
        "language": lang,

        # 前端主要使用这个字段
        "evidenceItems": evidence_items,

        # 兼容你现在的 dict 命名
        "keyevidence": evidence_items,

        # 保留原始 Ollama 输出，方便调试
        "raw": keyevidence_data,
    }