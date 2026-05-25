from pathlib import Path
from typing import Optional
import json
import tempfile
import shutil

import numpy as np
import nibabel as nib
from PIL import Image

from fastapi import APIRouter, HTTPException, Request, UploadFile, File, Form

from core.config import PATIENT_ROOT
from services.file_service import get_request_language
from services.patient_service import read_patient_info


router = APIRouter()


def _text(lang: str, zh: str, en: str) -> str:
    return en if lang == "en" else zh


def _safe_filename(filename: str) -> str:
    return Path(filename).name


def _get_modality_folder_name(modality: str) -> str:
    mapping = {
        "MRI": "mri",
        "CT": "ct",
        "PET": "pet",
        "PET/CT": "pet_ct",
    }
    return mapping.get(modality, modality.lower())


def _check_nii_gz_file(upload_file: UploadFile, modality_name: str):
    if upload_file is None:
        raise HTTPException(
            status_code=400,
            detail=f"{modality_name} 文件不能为空",
        )

    if not upload_file.filename:
        raise HTTPException(
            status_code=400,
            detail=f"{modality_name} 文件名为空",
        )

    if not upload_file.filename.endswith(".nii.gz"):
        raise HTTPException(
            status_code=400,
            detail=f"{modality_name} 只允许上传 .nii.gz 文件",
        )


def _normalize_slice_to_uint8(slice_data: np.ndarray) -> np.ndarray:
    """
    将医学图像切片按 min-max 归一化到 0-255，保存为 png。
    """
    slice_data = np.asarray(slice_data, dtype=np.float32)

    slice_data = np.nan_to_num(
        slice_data,
        nan=0.0,
        posinf=0.0,
        neginf=0.0,
    )

    min_val = float(np.min(slice_data))
    max_val = float(np.max(slice_data))

    if max_val - min_val < 1e-8:
        return np.zeros_like(slice_data, dtype=np.uint8)

    slice_data = (slice_data - min_val) / (max_val - min_val)
    slice_data = slice_data * 255.0

    return slice_data.astype(np.uint8)


def _convert_nii_gz_to_png_slices(
    upload_file: UploadFile,
    save_dir: Path,
    modality: str,
) -> int:
    """
    读取上传的 .nii.gz 文件，并将其中的医学图像切片保存为 png。

    示例：
    img/mri/t1/slice_000.png
    img/mri/t1ce/slice_000.png
    img/mri/t2/slice_000.png
    img/ct/slice_000.png
    """
    save_dir.mkdir(parents=True, exist_ok=True)

    original_filename = _safe_filename(upload_file.filename or "upload.nii.gz")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir) / original_filename

        with temp_path.open("wb") as buffer:
            shutil.copyfileobj(upload_file.file, buffer)

        try:
            nii_img = nib.load(str(temp_path))
            data = nii_img.get_fdata()
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"{modality} 文件读取失败，请确认是有效的 .nii.gz 医学影像文件：{str(e)}",
            )

    if data.ndim == 2:
        data = data[:, :, np.newaxis]

    if data.ndim == 3:
        volume = data
    elif data.ndim == 4:
        volume = data[:, :, :, 0]
    else:
        raise HTTPException(
            status_code=400,
            detail=f"{modality} 文件维度不支持，当前维度为 {data.ndim}",
        )

    num_slices = volume.shape[2]

    if num_slices <= 0:
        raise HTTPException(
            status_code=400,
            detail=f"{modality} 文件没有可保存的切片",
        )

    for old_file in save_dir.glob("*.png"):
        old_file.unlink()

    for slice_index in range(num_slices):
        slice_data = volume[:, :, slice_index]

        # 为了前端显示方向更接近常见医学图像
        slice_data = np.rot90(slice_data)

        image_uint8 = _normalize_slice_to_uint8(slice_data)

        image = Image.fromarray(image_uint8, mode="L")

        save_path = save_dir / f"slice_{slice_index:03d}.png"
        image.save(save_path)

    return num_slices

def _normalize_gender(gender: str, lang: str) -> str:
    """
    根据语言返回性别显示文本：
    zh: 男 / 女 / 未知
    en: Male / Female / Unknown
    """
    gender = (gender or "").strip()

    male_values = {"男", "男性", "male", "Male", "M", "m"}
    female_values = {"女", "女性", "female", "Female", "F", "f"}

    if gender in male_values:
        return "Male" if lang == "en" else "男"

    if gender in female_values:
        return "Female" if lang == "en" else "女"

    return "Unknown" if lang == "en" else "未知"
def _build_patient_info(
    *,
    lang: str,
    patient_id: str,
    name: str,
    age: int,
    gender: str,
    stage: str,
    date: str,
    modality_list: list[str],
    mri_sequence_list: list[str],
    clinical_history_status: str,
):
    """
    生成病人信息。

    关键字段：
    modalities: ["MRI", "CT", "PET"]
    mriSequences: ["T1", "T1CE", "T2"]
    """
    return {
        "id": patient_id,
        "name": name,
        "age": age,
        "gender": _normalize_gender(gender, lang),
        "stage": stage,
        "date": date,
        "modalities": modality_list,
        "mriSequences": mri_sequence_list,
        "clinicalHistoryStatus": clinical_history_status,
        "analysis": {
            "status": "not_started",
            "message": _text(lang, "尚未开始分析", "Analysis not started"),
            "started_at": None,
            "finished_at": None,
            "result": {},
        },
    }


@router.get("/api/patient/import-demo")
def import_patient_demo(request: Request, language: Optional[str] = "zh"):
    lang = get_request_language(request, language)

    print("前后端连接成功")

    return {
        "message": _text(lang, "连接后端成功", "Connected to backend successfully"),
        "language": lang,
        "patient_id": "C-2026-0128",
        "id": "C-2026-0128",
        "name": _text(lang, "示例病人", "Demo Patient"),
        "age": 47,
        "gender": _text(lang, "女", "Female"),
        "stage": "IB2",
        "date": "2026-05-20",
        "modalities": ["MRI", "PET", "CT", "PET/CT"],
        "mriSequences": ["T1", "T1CE", "T2"],
        "clinicalHistoryStatus": "partial",
    }


@router.get("/api/patient/list")
def list_patients(request: Request, language: Optional[str] = "zh"):
    lang = get_request_language(request, language)

    if not PATIENT_ROOT.exists():
        raise HTTPException(status_code=404, detail="病人数据目录不存在")

    patients = []

    for patient_dir in PATIENT_ROOT.iterdir():
        if not patient_dir.is_dir():
            continue

        patient_id = patient_dir.name

        try:
            info = read_patient_info(patient_id, lang)

            if "id" not in info:
                info["id"] = patient_id

            if "mriSequences" not in info:
                info["mriSequences"] = []

            patients.append(info)

        except HTTPException as e:
            print(f"跳过 {patient_id}：{e.detail}")
            continue

        except Exception as e:
            print(f"读取 {patient_id} 失败：{e}")
            continue

    print(f"获取病人列表成功，language={lang}")

    return {
        "message": _text(lang, "获取病人列表成功", "Patient list loaded successfully"),
        "language": lang,
        "patients": patients,
    }


@router.get("/api/patient/import/{patient_id}")
def import_patient(
    patient_id: str,
    request: Request,
    language: Optional[str] = "zh",
):
    lang = get_request_language(request, language)
    patient_dir = PATIENT_ROOT / patient_id

    if not patient_dir.exists() or not patient_dir.is_dir():
        raise HTTPException(
            status_code=404,
            detail=f"未找到病人数据目录：{patient_id}",
        )

    info = read_patient_info(patient_id, lang)

    if "id" not in info:
        info["id"] = patient_id

    if "mriSequences" not in info:
        info["mriSequences"] = []

    data_paths = {
        "root": str(patient_dir),
        "info_zh": str(patient_dir / "info_zh.json"),
        "info_en": str(patient_dir / "info_en.json"),
        "img": str(patient_dir / "img"),
        "mri": str(patient_dir / "img" / "mri"),
        "mri_t1": str(patient_dir / "img" / "mri" / "t1"),
        "mri_t1ce": str(patient_dir / "img" / "mri" / "t1ce"),
        "mri_t2": str(patient_dir / "img" / "mri" / "t2"),
        "ct": str(patient_dir / "img" / "ct"),
        "pet": str(patient_dir / "img" / "pet"),
        "pet_ct": str(patient_dir / "img" / "pet_ct"),
        "aireportdraft": str(patient_dir / "aireportdraft"),
        "assessment": str(patient_dir / "assessment"),
        "clinical_history": str(patient_dir / "clinical_history"),
        "doctor_feedback": str(patient_dir / "doctor_feedback"),
        "evidence": str(patient_dir / "evidence"),
        "keyevidence": str(patient_dir / "keyevidence"),
        "reasoning": str(patient_dir / "reasoning"),
    }

    print(f"导入病人成功：{patient_id}，language={lang}")

    return {
        "message": _text(lang, "病人信息导入成功", "Patient information imported successfully"),
        "language": lang,
        "patient": info,
        "paths": data_paths,
    }


@router.post("/api/patient/upload-local")
async def upload_local_patient(
    request: Request,
    language: Optional[str] = "zh",

    id: str = Form(...),
    name: str = Form(...),
    age: int = Form(...),
    gender: str = Form(""),
    stage: str = Form(""),
    date: str = Form(""),
    clinicalHistoryStatus: str = Form("missing"),

    # 前端传来的真实模态，例如 ["MRI", "CT"]
    modalities: str = Form(...),

    # 前端传来的 MRI 子序列，例如 ["T1", "T1CE", "T2"]
    mriSequences: str = Form("[]"),

    # MRI 子序列文件
    mri_t1_file: Optional[UploadFile] = File(None),
    mri_t1ce_file: Optional[UploadFile] = File(None),
    mri_t2_file: Optional[UploadFile] = File(None),

    # 其他模态文件
    ct_file: Optional[UploadFile] = File(None),
    pet_file: Optional[UploadFile] = File(None),
    petct_file: Optional[UploadFile] = File(None),
):
    """
    本地上传病人数据。

    前端 FormData 字段：
    - id
    - name
    - age
    - gender
    - stage
    - date
    - clinicalHistoryStatus
    - modalities: JSON 字符串，例如 ["MRI", "CT", "PET/CT"]
    - mriSequences: JSON 字符串，例如 ["T1", "T1CE", "T2"]
    - mri_t1_file
    - mri_t1ce_file
    - mri_t2_file
    - ct_file
    - pet_file
    - petct_file

    实际保存：
    - img/mri/t1/*.png
    - img/mri/t1ce/*.png
    - img/mri/t2/*.png
    - img/ct/*.png
    - img/pet/*.png
    - img/pet_ct/*.png
    """
    lang = get_request_language(request, language)

    patient_id = id.strip()

    if not patient_id:
        raise HTTPException(status_code=400, detail="病人 ID 不能为空")

    if not name.strip():
        raise HTTPException(status_code=400, detail="病人姓名不能为空")

    patient_dir = PATIENT_ROOT / patient_id

    if patient_dir.exists():
        raise HTTPException(
            status_code=409,
            detail=f"病人 ID 已存在：{patient_id}，请重新输入",
        )

    try:
        modality_list = json.loads(modalities)
    except Exception:
        raise HTTPException(
            status_code=400,
            detail='modalities 字段格式错误，应为 JSON 字符串，例如 ["MRI", "CT"]',
        )

    if not isinstance(modality_list, list) or len(modality_list) == 0:
        raise HTTPException(
            status_code=400,
            detail="请至少选择一种影像模态",
        )

    allowed_modalities = {"MRI", "CT", "PET", "PET/CT"}

    for modality in modality_list:
        if modality not in allowed_modalities:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的影像模态：{modality}",
            )

    try:
        mri_sequence_list = json.loads(mriSequences)
    except Exception:
        raise HTTPException(
            status_code=400,
            detail='mriSequences 字段格式错误，应为 JSON 字符串，例如 ["T1", "T1CE"]',
        )

    if not isinstance(mri_sequence_list, list):
        raise HTTPException(
            status_code=400,
            detail="mriSequences 字段必须是数组",
        )

    allowed_mri_sequences = {"T1", "T1CE", "T2"}

    cleaned_mri_sequence_list = []

    for sequence in mri_sequence_list:
        sequence_upper = str(sequence).upper()

        if sequence_upper not in allowed_mri_sequences:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的 MRI 子序列：{sequence}",
            )

        if sequence_upper not in cleaned_mri_sequence_list:
            cleaned_mri_sequence_list.append(sequence_upper)

    mri_sequence_list = cleaned_mri_sequence_list

    if "MRI" in modality_list and len(mri_sequence_list) == 0:
        raise HTTPException(
            status_code=400,
            detail="已选择 MRI，但没有选择 MRI 子序列",
        )

    if "MRI" not in modality_list and len(mri_sequence_list) > 0:
        modality_list.append("MRI")

    mri_file_map = {
        "T1": mri_t1_file,
        "T1CE": mri_t1ce_file,
        "T2": mri_t2_file,
    }

    normal_modality_file_map = {
        "CT": ct_file,
        "PET": pet_file,
        "PET/CT": petct_file,
    }

    if "MRI" in modality_list:
        for sequence in mri_sequence_list:
            upload_file = mri_file_map.get(sequence)

            if upload_file is None:
                raise HTTPException(
                    status_code=400,
                    detail=f"已选择 MRI/{sequence}，但没有上传对应的 .nii.gz 文件",
                )

            _check_nii_gz_file(upload_file, f"MRI/{sequence}")

    for modality in modality_list:
        if modality == "MRI":
            continue

        upload_file = normal_modality_file_map.get(modality)

        if upload_file is None:
            raise HTTPException(
                status_code=400,
                detail=f"已选择 {modality}，但没有上传对应的 .nii.gz 文件",
            )

        _check_nii_gz_file(upload_file, modality)

    try:
        patient_dir.mkdir(parents=True, exist_ok=False)

        img_root = patient_dir / "img"
        img_root.mkdir(parents=True, exist_ok=True)

        mri_root = img_root / "mri"
        mri_root.mkdir(parents=True, exist_ok=True)

        for sequence_folder in ["t1", "t1ce", "t2"]:
            (mri_root / sequence_folder).mkdir(parents=True, exist_ok=True)

        for folder_name in ["ct", "pet", "pet_ct"]:
            (img_root / folder_name).mkdir(parents=True, exist_ok=True)

        slice_counts = {}

        if "MRI" in modality_list:
            sequence_folder_map = {
                "T1": "t1",
                "T1CE": "t1ce",
                "T2": "t2",
            }

            for sequence in mri_sequence_list:
                upload_file = mri_file_map[sequence]

                if upload_file is None:
                    continue

                sequence_folder = sequence_folder_map[sequence]
                save_dir = mri_root / sequence_folder

                slice_count = _convert_nii_gz_to_png_slices(
                    upload_file=upload_file,
                    save_dir=save_dir,
                    modality=f"MRI/{sequence}",
                )

                slice_counts[f"MRI/{sequence}"] = slice_count

                print(
                    f"MRI/{sequence} 影像解析完成，共保存 {slice_count} 张切片到：{save_dir}"
                )

        for modality in modality_list:
            if modality == "MRI":
                continue

            upload_file = normal_modality_file_map[modality]

            if upload_file is None:
                continue

            folder_name = _get_modality_folder_name(modality)
            save_dir = img_root / folder_name

            slice_count = _convert_nii_gz_to_png_slices(
                upload_file=upload_file,
                save_dir=save_dir,
                modality=modality,
            )

            slice_counts[modality] = slice_count

            print(
                f"{modality} 影像解析完成，共保存 {slice_count} 张切片到：{save_dir}"
            )

        common_kwargs = {
            "patient_id": patient_id,
            "name": name,
            "age": age,
            "gender": gender,
            "stage": stage,
            "date": date,
            "modality_list": modality_list,
            "mri_sequence_list": mri_sequence_list,
            "clinical_history_status": clinicalHistoryStatus,
        }

        info_zh = _build_patient_info(
            lang="zh",
            **common_kwargs,
        )

        info_en = _build_patient_info(
            lang="en",
            **common_kwargs,
        )

        info_zh_path = patient_dir / "info_zh.json"
        info_en_path = patient_dir / "info_en.json"

        with info_zh_path.open("w", encoding="utf-8") as f:
            json.dump(info_zh, f, ensure_ascii=False, indent=2)

        with info_en_path.open("w", encoding="utf-8") as f:
            json.dump(info_en, f, ensure_ascii=False, indent=2)

        returned_info = info_en if lang == "en" else info_zh

        print(f"本地上传病人成功：{patient_id}，language={lang}")

        return {
            "message": _text(
                lang,
                "本地病人数据上传成功",
                "Local patient data uploaded successfully",
            ),
            "language": lang,
            "patient": returned_info,
            "slice_counts": slice_counts,
            "paths": {
                "root": str(patient_dir),
                "info_zh": str(info_zh_path),
                "info_en": str(info_en_path),
                "img": str(img_root),
                "mri": str(mri_root),
                "mri_t1": str(mri_root / "t1"),
                "mri_t1ce": str(mri_root / "t1ce"),
                "mri_t2": str(mri_root / "t2"),
                "ct": str(img_root / "ct"),
                "pet": str(img_root / "pet"),
                "pet_ct": str(img_root / "pet_ct"),
            },
        }

    except HTTPException:
        if patient_dir.exists():
            shutil.rmtree(patient_dir, ignore_errors=True)
        raise

    except Exception as e:
        if patient_dir.exists():
            shutil.rmtree(patient_dir, ignore_errors=True)

        raise HTTPException(
            status_code=500,
            detail=f"本地病人数据上传失败：{str(e)}",
        )