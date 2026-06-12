import base64
from pathlib import Path
from uuid import uuid4

import httpx
from fastapi import APIRouter, File, UploadFile

from core.config import UPLOAD_DIR, MODEL_API_URL

router = APIRouter()

TIMEOUT = 180.0


def _decide(image_b64: str, task: str, stage: str = "mr") -> dict:
    payload = {
        "patient_id": "web-request",
        "task": task,
        "stage": stage,
        "slices": [{"modal": "t2", "image_b64": image_b64}],
        "use_qwen": True,
    }
    resp = httpx.post(f"{MODEL_API_URL}/decide", json=payload, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()


@router.post("/predict")
async def predict(file: UploadFile = File(...)):
    content = await file.read()

    # save upload
    suffix = Path(file.filename).suffix
    file_id = uuid4().hex
    (UPLOAD_DIR / f"{file_id}{suffix}").write_bytes(content)

    image_b64 = base64.b64encode(content).decode()

    try:
        lymph = _decide(image_b64, "lymph")
        para = _decide(image_b64, "parametrium")
        evidence_status = "sufficient" if (lymph["trust"] and para["trust"]) else "insufficient"
        return {
            "case_id": file_id,
            "filename": file.filename,
            "plnm_risk": lymph["avg_cls_score"],
            "pmi_risk": para["avg_cls_score"],
            "evidence_status": evidence_status,
            "report": {
                "lymph_node": lymph["recommendation_text"],
                "parametrial_invasion": para["recommendation_text"],
                "suggestion": (
                    "影像证据充分，建议参考上述结论。"
                    if evidence_status == "sufficient"
                    else "当前证据不足，建议补充影像资料后进行 MDT 多学科讨论。"
                ),
            },
            "images": {
                "input_image_url": None,
                "recon_image_url": None,
                "seg_image_url": None,
                "uncertainty_image_url": None,
            },
            "signals": {
                "lymph": lymph.get("signals"),
                "parametrium": para.get("signals"),
            },
        }
    except httpx.HTTPError as e:
        # model server unreachable — return stub so frontend doesn't break
        return {
            "case_id": file_id,
            "filename": file.filename,
            "plnm_risk": None,
            "pmi_risk": None,
            "evidence_status": "error",
            "report": {
                "lymph_node": f"模型服务不可达：{e}",
                "parametrial_invasion": f"模型服务不可达：{e}",
                "suggestion": "请检查模型服务是否已启动。",
            },
            "images": {"input_image_url": None, "recon_image_url": None,
                       "seg_image_url": None, "uncertainty_image_url": None},
        }
