from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, UploadFile

from core.config import UPLOAD_DIR


router = APIRouter()


@router.post("/predict")
async def predict(file: UploadFile = File(...)):
    suffix = Path(file.filename).suffix
    file_id = uuid4().hex

    upload_path = UPLOAD_DIR / f"{file_id}{suffix}"

    content = await file.read()
    upload_path.write_bytes(content)

    return {
        "case_id": file_id,
        "filename": file.filename,
        "plnm_risk": 0.583,
        "pmi_risk": 0.312,
        "evidence_status": "insufficient",
        "report": {
            "lymph_node": "当前影像显示左侧髂外淋巴结可疑，建议进一步结合 PET/CT 评估。",
            "parametrial_invasion": "当前 MRI 显示宫旁界面不清，建议结合增强 MRI 和 DWI 进一步评估。",
            "suggestion": "当前证据不足，建议补充影像资料后进行 MDT 多学科讨论。",
        },
        "images": {
            "input_image_url": None,
            "recon_image_url": None,
            "seg_image_url": None,
            "uncertainty_image_url": None,
        },
    }