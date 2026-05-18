import json
from fastapi import HTTPException

from core.config import PATIENT_ROOT


def read_patient_info(patient_id: str) -> dict:
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

    try:
        with open(info_path, "r", encoding="utf-8") as f:
            info = json.load(f)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"读取 info.json 失败：{str(e)}",
        )

    return info


def write_patient_info(patient_id: str, info: dict):
    patient_dir = PATIENT_ROOT / patient_id
    info_path = patient_dir / "info.json"

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
            detail=f"写入 info.json 失败：{str(e)}",
        )