from fastapi import APIRouter, HTTPException, Request

from core.config import PATIENT_ROOT


router = APIRouter()


@router.get("/api/patient/{patient_id}/images")
def get_patient_images(patient_id: str, request: Request):
    modality_map = {
        "mri": "MRI",
        "ct": "CT",
        "pet": "PET",
        "pet_ct": "PET/CT",
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

    for modality_folder in ["mri", "ct", "pet", "pet_ct"]:
        modality_dir = img_dir / modality_folder

        if not modality_dir.exists():
            continue

        image_files = sorted(
            [
                file
                for file in modality_dir.iterdir()
                if file.is_file()
                and file.suffix.lower() in image_extensions
            ]
        )

        total_slices = len(image_files)

        for index, image_path in enumerate(image_files):
            image_url = (
                f"{request.base_url}"
                f"static/patient/"
                f"{patient_id}/img/{modality_folder}/{image_path.name}"
            )

            images.append(
                {
                    "id": f"{patient_id}-{modality_folder}-slice-{index + 1:03d}",
                    "url": image_url,
                    "modality": modality_map.get(
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
        "images": images,
    }