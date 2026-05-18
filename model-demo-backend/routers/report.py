from fastapi import APIRouter, HTTPException

from core.config import PATIENT_ROOT
from services.file_service import read_json_file


router = APIRouter()


@router.get("/api/patient/AIreport/{patient_id}")
def get_patient_report(patient_id: str):
    print(f"查询病人 {patient_id} 的 AI 报告草稿")

    if not patient_id:
        raise HTTPException(status_code=400, detail="patient_id 不能为空")

    aireportdraft_path = (
        PATIENT_ROOT
        / patient_id
        / "aireportdraft"
        / "aireportdraft.json"
    )

    print("AI 报告草稿文件路径:", aireportdraft_path)

    aireportdraft_data = read_json_file(aireportdraft_path, "AI 报告草稿")

    print(f"成功读取病人 {patient_id} 的 AI 报告草稿")

    return {
        "patient_id": patient_id,
        "aireportdraft": aireportdraft_data,
    }