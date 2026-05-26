from typing import Optional

from fastapi import APIRouter, HTTPException, Request

from core.config import PATIENT_ROOT
from services.file_service import get_request_language, read_localized_json_file


router = APIRouter()


@router.get("/api/patient/AIreport/{patient_id}")
def get_patient_report(
    patient_id: str,
    request: Request,
    language: Optional[str] = "zh",
):
    lang = get_request_language(request, language)
    print(f"查询病人 {patient_id} 的 AI 报告草稿，language={lang}")

    if not patient_id:
        raise HTTPException(status_code=400, detail="patient_id 不能为空")

    aireportdraft_path = (
        PATIENT_ROOT
        / patient_id
        / "aireportdraft"
        / "aireportdraft.json"
    )

    aireportdraft_data = read_localized_json_file(
        aireportdraft_path,
        "AI 报告草稿",
        lang,
    )

    # 兼容两种格式：
    # 旧格式：[
    #   {...},
    #   {...}
    # ]
    #
    # 新格式：{
    #   "aireportdraft": [
    #       {...},
    #       {...}
    #   ]
    # }
    if isinstance(aireportdraft_data, dict):
        aireportdraft = aireportdraft_data.get("aireportdraft", [])

        # 兼容可能写成 aiReportDraft / reportDraft / report 的情况
        if not aireportdraft:
            aireportdraft = aireportdraft_data.get("aiReportDraft", [])

        if not aireportdraft:
            aireportdraft = aireportdraft_data.get("reportDraft", [])

        if not aireportdraft:
            aireportdraft = aireportdraft_data.get("report", [])

    elif isinstance(aireportdraft_data, list):
        aireportdraft = aireportdraft_data

    else:
        aireportdraft = []

    print(f"成功读取病人 {patient_id} 的 AI 报告草稿")

    return {
        "patient_id": patient_id,
        "language": lang,

        # 前端主要使用这个字段
        "aireportdraft": aireportdraft,

        # 兼容可能的前端命名
        "aiReportDraft": aireportdraft,
        "reportDraft": aireportdraft,

        # 保留原始 Ollama 输出，方便调试
        "raw": aireportdraft_data,
    }