from fastapi import APIRouter, HTTPException

from core.config import PATIENT_ROOT
from services.file_service import read_json_file


router = APIRouter()


@router.get("/api/patient/{patient_id}/key-evidence")
def get_patient_key_evidence(patient_id: str):
    print(f"查询病人 {patient_id} 的关键证据")

    if not patient_id:
        raise HTTPException(status_code=400, detail="patient_id 不能为空")

    keyevidence_path = (
        PATIENT_ROOT
        / patient_id
        / "keyevidence"
        / "keyevidence.json"
    )

    print("关键证据文件路径:", keyevidence_path)

    keyevidence_data = read_json_file(keyevidence_path, "关键证据")

    print(f"成功读取病人 {patient_id} 的关键证据")

    return {
        "patient_id": patient_id,
        "evidenceItems": keyevidence_data,
        #"summary": keyevidence_data.get("summary", ""),
    }