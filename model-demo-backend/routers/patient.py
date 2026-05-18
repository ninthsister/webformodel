from fastapi import APIRouter, HTTPException

from core.config import PATIENT_ROOT
from services.patient_service import read_patient_info


router = APIRouter()


@router.get("/api/patient/import-demo")
def import_patient_demo():
    print("前后端连接成功")
    return {
        "message": "连接后端成功",
        "patient_id": "C-2026-0128",
        "name": "示例病人",
        "age": 47,
        "gender": "女",
        "stage": "IB2",
        "date": "2026-05-20",
    }


@router.get("/api/report/export-demo")
def export_report_demo():
    print("导出报告成功")
    return {
        "message": "导出报告成功",
        "report_id": "R-2026-0128",
        "patient_id": "C-2026-0128",
        "date": "2026-05-20",
    }


@router.get("/api/patient/list")
def list_patients():
    if not PATIENT_ROOT.exists():
        raise HTTPException(status_code=404, detail="病人数据目录不存在")

    patients = []

    for patient_dir in PATIENT_ROOT.iterdir():
        if not patient_dir.is_dir():
            continue

        patient_id = patient_dir.name

        try:
            info = read_patient_info(patient_id)

            if "id" not in info:
                info["id"] = patient_id

            patients.append(info)

        except HTTPException as e:
            print(f"跳过 {patient_id}：{e.detail}")
            continue

        except Exception as e:
            print(f"读取 {patient_id} 失败：{e}")
            continue

    print("获取病人列表成功")

    return {
        "message": "获取病人列表成功",
        "patients": patients,
    }


@router.get("/api/patient/import/{patient_id}")
def import_patient(patient_id: str):
    patient_dir = PATIENT_ROOT / patient_id

    info = read_patient_info(patient_id)

    if "id" not in info:
        info["id"] = patient_id

    data_paths = {
        "root": str(patient_dir),
        "info": str(patient_dir / "info.json"),
        "img": str(patient_dir / "img"),
        "AI_generated_report": str(patient_dir / "AI_generated_report"),
        "assessment": str(patient_dir / "assessment"),
        "clinical_history": str(patient_dir / "clinical_history"),
        "evidence": str(patient_dir / "evidence"),
    }

    print(f"导入病人成功：{patient_id}")

    return {
        "message": "病人信息导入成功",
        "patient": info,
        "paths": data_paths,
    }