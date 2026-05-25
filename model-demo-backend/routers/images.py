from typing import Optional

from fastapi import APIRouter, HTTPException, Request

from core.config import PATIENT_ROOT
from services.file_service import get_request_language


router = APIRouter()


@router.get("/api/patient/{patient_id}/images")
def get_patient_images(
    patient_id: str,
    request: Request,
    language: Optional[str] = "zh",
):
    lang = get_request_language(request, language)

    if lang not in ["zh", "en"]:
        lang = "zh"

    modality_map = {
        "zh": {
            "mri": "MRI",
            "ct": "CT",
            "pet": "PET",
            "pet_ct": "PET/CT",
        },
        "en": {
            "mri": "MRI",
            "ct": "CT",
            "pet": "PET",
            "pet_ct": "PET/CT",
        },
    }

    mri_sequence_map = {
        "t1": "T1",
        "t1ce": "T1CE",
        "t2": "T2",
    }

    image_extensions = {
        ".png",
        ".jpg",
        ".jpeg",
        ".webp",
        ".bmp",
    }

    if not patient_id or patient_id == "??????":
        raise HTTPException(status_code=400, detail="Invalid patient id")

    patient_dir = PATIENT_ROOT / patient_id
    img_dir = patient_dir / "img"

    if not patient_dir.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Patient {patient_id} not found",
        )

    if not img_dir.exists():
        raise HTTPException(
            status_code=404,
            detail=f"No img folder found for patient {patient_id}",
        )

    images = []

    def build_image_url(*parts: str) -> str:
        """
        生成图片访问 URL。

        例如：
        static/patient/C-2026-0128/img/mri/t1/slice_001.png
        """
        relative_path = "/".join(parts)

        return (
            f"{request.base_url}"
            f"static/patient/"
            f"{patient_id}/img/{relative_path}"
        )

    def list_image_files(folder_path):
        """
        获取某个文件夹下的图片文件。
        """
        if not folder_path.exists() or not folder_path.is_dir():
            return []

        return sorted(
            [
                file
                for file in folder_path.iterdir()
                if file.is_file()
                and file.suffix.lower() in image_extensions
            ]
        )

    # =========================
    # 1. 读取 MRI 子序列
    # =========================
    mri_dir = img_dir / "mri"

    if mri_dir.exists() and mri_dir.is_dir():
        for sequence_folder in ["t1", "t1ce", "t2"]:
            sequence_dir = mri_dir / sequence_folder

            image_files = list_image_files(sequence_dir)

            if len(image_files) == 0:
                continue

            total_slices = len(image_files)

            for index, image_path in enumerate(image_files):
                image_url = build_image_url(
                    "mri",
                    sequence_folder,
                    image_path.name,
                )

                images.append(
                    {
                        "id": (
                            f"{patient_id}-mri-"
                            f"{sequence_folder}-slice-{index + 1:03d}"
                        ),
                        "url": image_url,
                        "modality": "MRI",
                        "sequence": mri_sequence_map.get(
                            sequence_folder,
                            sequence_folder.upper(),
                        ),
                        "sliceIndex": index + 1,
                        "totalSlices": total_slices,
                    }
                )

        # 兼容旧结构：
        # img/mri/slice_001.png
        # 如果你的 MRI 图片不是放在 t1/t1ce/t2 子文件夹下，也能读到。
        root_mri_images = list_image_files(mri_dir)

        if len(root_mri_images) > 0:
            total_slices = len(root_mri_images)

            for index, image_path in enumerate(root_mri_images):
                image_url = build_image_url(
                    "mri",
                    image_path.name,
                )

                images.append(
                    {
                        "id": f"{patient_id}-mri-slice-{index + 1:03d}",
                        "url": image_url,
                        "modality": "MRI",
                        "sequence": "",
                        "sliceIndex": index + 1,
                        "totalSlices": total_slices,
                    }
                )

    # =========================
    # 2. 读取普通模态：CT / PET / PET-CT
    # =========================
    for modality_folder in ["ct", "pet", "pet_ct"]:
        modality_dir = img_dir / modality_folder

        image_files = list_image_files(modality_dir)

        if len(image_files) == 0:
            continue

        total_slices = len(image_files)

        for index, image_path in enumerate(image_files):
            image_url = build_image_url(
                modality_folder,
                image_path.name,
            )

            images.append(
                {
                    "id": f"{patient_id}-{modality_folder}-slice-{index + 1:03d}",
                    "url": image_url,
                    "modality": modality_map[lang].get(
                        modality_folder,
                        modality_folder.upper(),
                    ),
                    "sliceIndex": index + 1,
                    "totalSlices": total_slices,
                }
            )

    if len(images) == 0:
        raise HTTPException(
            status_code=404,
            detail=f"No images found under patient/{patient_id}/img",
        )

    return {
        "patientId": patient_id,
        "language": lang,
        "images": images,
    }