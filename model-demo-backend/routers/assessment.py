from fastapi import APIRouter, HTTPException

from core.config import PATIENT_ROOT
from services.file_service import read_json_file


router = APIRouter()


@router.get("/api/patient/{patient_id}/assessment")
def get_patient_assessment(patient_id: str):
    print(f"查询病人 {patient_id} 的评估结果")

    if not patient_id:
        raise HTTPException(status_code=400, detail="patient_id 不能为空")

    assessment_path = (
        PATIENT_ROOT
        / patient_id
        / "assessment"
        / "assessment.json"
    )

    print("评估文件路径:", assessment_path)

    assessment_data = read_json_file(assessment_path, "评估")

    print(f"成功读取病人 {patient_id} 的评估结果")

    return {
        "patient_id": patient_id,
        "assessments": assessment_data,
    }