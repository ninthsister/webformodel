from fastapi import APIRouter, HTTPException

from core.config import PATIENT_ROOT
from services.file_service import read_json_file


router = APIRouter()


@router.get("/api/patient/reasoning/{patient_id}")
def get_patient_reasoning(patient_id: str):
    print(f"查询病人 {patient_id} 的推理结果")

    if not patient_id:
        raise HTTPException(status_code=400, detail="patient_id 不能为空")

    reasoning_path = (
        PATIENT_ROOT
        / patient_id
        / "reasoning"
        / "reasoning.json"
    )

    print("推理文件路径:", reasoning_path)

    reasoning_data = read_json_file(reasoning_path, "推理")

    print(f"成功读取病人 {patient_id} 的推理结果")

    return {
        "patient_id": patient_id,
        "reasoning": reasoning_data,
    }