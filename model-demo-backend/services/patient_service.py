import json
from typing import Optional

from fastapi import HTTPException

from core.config import PATIENT_ROOT
from services.file_service import get_localized_json_path, normalize_language, read_json_file


def read_patient_info(patient_id: str, language: Optional[str] = None) -> dict:
    patient_dir = PATIENT_ROOT / patient_id
    info_path = patient_dir / "info.json"
    lang = normalize_language(language)
    localized_info_path = get_localized_json_path(info_path, lang)

    if not patient_dir.exists() or not patient_dir.is_dir():
        raise HTTPException(
            status_code=404,
            detail=f"未找到病人数据目录：{patient_id}",
        )

    if not localized_info_path.exists():
        raise HTTPException(
            status_code=404,
            detail=(
                f"未找到病人信息{lang}语言文件：{patient_id}/{localized_info_path.name}。"
                f"请使用 info_{lang}.json 命名"
            ),
        )

    return read_json_file(localized_info_path, "病人信息")


def write_patient_info(patient_id: str, info: dict, language: Optional[str] = None):
    # Runtime status is written to the language-specific info file, e.g.
    # info_zh.json / info_en.json.
    patient_dir = PATIENT_ROOT / patient_id
    lang = normalize_language(language)
    info_path = get_localized_json_path(patient_dir / "info.json", lang)

    if not patient_dir.exists() or not patient_dir.is_dir():
        raise HTTPException(
            status_code=404,
            detail=f"未找到病人数据目录：{patient_id}",
        )

    try:
        with open(info_path, "w", encoding="utf-8") as f:
            json.dump(info, f, ensure_ascii=False, indent=2)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"写入 {info_path.name} 失败：{str(e)}",
        )
