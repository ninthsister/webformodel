# import base64
# from pathlib import Path
# from uuid import uuid4

# import httpx
# from fastapi import APIRouter, File, UploadFile

# from core.config import UPLOAD_DIR, MODEL_API_URL

# router = APIRouter()

# TIMEOUT = 180.0


# def _decide(image_b64: str, task: str, stage: str = "mr") -> dict:
#     payload = {
#         "patient_id": "web-request",
#         "task": task,
#         "stage": stage,
#         "slices": [{"modal": "t2", "image_b64": image_b64}],
#         "use_qwen": True,
#     }
#     resp = httpx.post(f"{MODEL_API_URL}/decide", json=payload, timeout=TIMEOUT)
#     resp.raise_for_status()
#     return resp.json()


# @router.post("/predict")
# async def predict(file: UploadFile = File(...)):
#     content = await file.read()

#     # save upload
#     suffix = Path(file.filename).suffix
#     file_id = uuid4().hex
#     (UPLOAD_DIR / f"{file_id}{suffix}").write_bytes(content)

#     image_b64 = base64.b64encode(content).decode()

#     try:
#         lymph = _decide(image_b64, "lymph")
#         para = _decide(image_b64, "parametrium")
#         evidence_status = "sufficient" if (lymph["trust"] and para["trust"]) else "insufficient"
#         return {
#             "case_id": file_id,
#             "filename": file.filename,
#             "plnm_risk": lymph["avg_cls_score"],
#             "pmi_risk": para["avg_cls_score"],
#             "evidence_status": evidence_status,
#             "report": {
#                 "lymph_node": lymph["recommendation_text"],
#                 "parametrial_invasion": para["recommendation_text"],
#                 "suggestion": (
#                     "影像证据充分，建议参考上述结论。"
#                     if evidence_status == "sufficient"
#                     else "当前证据不足，建议补充影像资料后进行 MDT 多学科讨论。"
#                 ),
#             },
#             "images": {
#                 "input_image_url": None,
#                 "recon_image_url": None,
#                 "seg_image_url": None,
#                 "uncertainty_image_url": None,
#             },
#             "signals": {
#                 "lymph": lymph.get("signals"),
#                 "parametrium": para.get("signals"),
#             },
#         }
#     except httpx.HTTPError as e:
#         # model server unreachable — return stub so frontend doesn't break
#         return {
#             "case_id": file_id,
#             "filename": file.filename,
#             "plnm_risk": None,
#             "pmi_risk": None,
#             "evidence_status": "error",
#             "report": {
#                 "lymph_node": f"模型服务不可达：{e}",
#                 "parametrial_invasion": f"模型服务不可达：{e}",
#                 "suggestion": "请检查模型服务是否已启动。",
#             },
#             "images": {"input_image_url": None, "recon_image_url": None,
#                        "seg_image_url": None, "uncertainty_image_url": None},
#         }
import base64
from pathlib import Path
from uuid import uuid4

import httpx
from fastapi import APIRouter
from pydantic import BaseModel

from core.config import MODEL_API_URL

router = APIRouter()

TIMEOUT = 180.0


class PredictRequest(BaseModel):
    patient_id: str = "web-request"
    stage: str = "mr"
    image_paths: list[str]


def infer_modal_from_path(path_text: str) -> str:
    s = path_text.replace("\\", "/").lower()
    parts = [p for p in s.split("/") if p]

    if "t1ce" in parts:
        return "t1ce"
    if "t1" in parts:
        return "t1"
    if "t2" in parts:
        return "t2"
    if "petct" in parts or "pet-ct" in parts or "pet_ct" in parts:
        return "petct"
    if "ct" in parts:
        return "ct"
    if "pet" in parts:
        return "pet"
    if "mri" in parts or "mr" in parts:
        return "t2"

    return "t2"


def build_slices_from_paths(image_paths: list[str]) -> tuple[list[dict], list[dict]]:
    slices = []
    files_info = []

    for image_path in image_paths:
        path = Path(image_path)

        if not path.exists():
            raise FileNotFoundError(f"图片不存在：{image_path}")

        if not path.is_file():
            raise IsADirectoryError(f"不是文件：{image_path}")

        content = path.read_bytes()
        image_b64 = base64.b64encode(content).decode()
        modal = infer_modal_from_path(image_path)

        slices.append({
            "modal": modal,
            "image_b64": image_b64,
        })

        files_info.append({
            "path": image_path,
            "filename": path.name,
            "modal": modal,
        })

    return slices, files_info


def _decide(
    slices: list[dict],
    task: str,
    patient_id: str,
    stage: str = "mr",
) -> dict:
    payload = {
        "patient_id": patient_id,
        "task": task,
        "stage": stage,
        "slices": slices,
        "use_qwen": True,
    }

    resp = httpx.post(
        f"{MODEL_API_URL}/decide",
        json=payload,
        timeout=TIMEOUT,
    )
    resp.raise_for_status()
    return resp.json()


@router.post("/predict")
async def predict(req: PredictRequest):
    case_id = uuid4().hex

    try:
        slices, files_info = build_slices_from_paths(req.image_paths)
    except Exception as e:
        return {
            "case_id": case_id,
            "patient_id": req.patient_id,
            "num_images": 0,
            "files": [],
            "plnm_risk": None,
            "pmi_risk": None,
            "evidence_status": "error",
            "report": {
                "lymph_node": f"读取图片失败：{e}",
                "parametrial_invasion": f"读取图片失败：{e}",
                "suggestion": "请检查传入的服务器图片路径是否正确。",
            },
            "images": {
                "input_image_url": None,
                "recon_image_url": None,
                "seg_image_url": None,
                "uncertainty_image_url": None,
            },
            "signals": {
                "lymph": None,
                "parametrium": None,
            },
        }

    try:
        lymph = _decide(
            slices=slices,
            task="lymph",
            patient_id=req.patient_id,
            stage=req.stage,
        )

        para = _decide(
            slices=slices,
            task="parametrium",
            patient_id=req.patient_id,
            stage=req.stage,
        )

        evidence_status = (
            "sufficient"
            if lymph.get("trust") and para.get("trust")
            else "insufficient"
        )

        return {
            "case_id": case_id,
            "patient_id": req.patient_id,
            "num_images": len(req.image_paths),
            "files": files_info,

            "plnm_risk": lymph.get("avg_cls_score"),
            "pmi_risk": para.get("avg_cls_score"),
            "evidence_status": evidence_status,

            "report": {
                "lymph_node": lymph.get("recommendation_text"),
                "parametrial_invasion": para.get("recommendation_text"),
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
        return {
            "case_id": case_id,
            "patient_id": req.patient_id,
            "num_images": len(req.image_paths),
            "files": files_info,

            "plnm_risk": None,
            "pmi_risk": None,
            "evidence_status": "error",

            "report": {
                "lymph_node": f"模型服务不可达：{e}",
                "parametrial_invasion": f"模型服务不可达：{e}",
                "suggestion": "请检查模型服务是否已启动。",
            },

            "images": {
                "input_image_url": None,
                "recon_image_url": None,
                "seg_image_url": None,
                "uncertainty_image_url": None,
            },

            "signals": {
                "lymph": None,
                "parametrium": None,
            },
        }