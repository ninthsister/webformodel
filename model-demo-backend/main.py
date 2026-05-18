from pathlib import Path
from uuid import uuid4
import json
import time
from datetime import datetime
from threading import Thread

from fastapi import FastAPI, File, UploadFile, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel


from fastapi import HTTPException
# 病人数据根目录
PATIENT_ROOT = Path("static/patient")




app = FastAPI(title="Medical AI Model Backend")

# 允许前端 Next.js 访问后端
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
RESULT_DIR = BASE_DIR / "static" / "results"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
RESULT_DIR.mkdir(parents=True, exist_ok=True)

# 让前端可以通过 /static/results/xxx.png 访问结果图
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

#############
class StartAnalysisRequest(BaseModel):
    patientId: str
    signal: str


def read_patient_info(patient_id: str) -> dict:
    """
    读取某个病人的 info.json
    """
    patient_dir = PATIENT_ROOT / patient_id
    info_path = patient_dir / "info.json"

    if not patient_dir.exists() or not patient_dir.is_dir():
        raise HTTPException(
            status_code=404,
            detail=f"未找到病人数据目录：{patient_id}",
        )

    if not info_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"未找到病人信息文件：{patient_id}/info.json",
        )

    try:
        with open(info_path, "r", encoding="utf-8") as f:
            info = json.load(f)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"读取 info.json 失败：{str(e)}",
        )

    return info


def write_patient_info(patient_id: str, info: dict):
    """
    写回某个病人的 info.json
    """
    patient_dir = PATIENT_ROOT / patient_id
    info_path = patient_dir / "info.json"

    if not patient_dir.exists() or not patient_dir.is_dir():
        raise HTTPException(
            status_code=404,
            detail=f"未找到病人数据目录：{patient_id}",
        )

    try:
        with open(info_path, "w", encoding="utf-8") as f:
            json.dump(info, f, ensure_ascii=False, indent=2)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"写入 info.json 失败：{str(e)}",
        )


def run_analysis_task(patient_id: str):
    """
    后台分析任务。

    这里先用 sleep(5) 模拟真实模型分析。
    后面你真正接模型时，把 time.sleep(5) 换成你的分析代码即可。
    """
    try:
        print(f"[分析任务] 病人 {patient_id} 开始分析")

        # 1. 先把状态写成 analyzing
        info = read_patient_info(patient_id)
        info["analysis"] = {
            "status": "analyzing",
            "message": "正在分析",
            "started_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "finished_at": None,
        }
        write_patient_info(patient_id, info)

        # 2. 模拟耗时分析
        time.sleep(5)

        # 3. 分析完成后，把结果写入病人信息
        info = read_patient_info(patient_id)

        info["analysis"] = {
            "status": "completed",
            "message": "分析完成",
            "started_at": info.get("analysis", {}).get("started_at"),
            "finished_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "result": {
            },
        }

        write_patient_info(patient_id, info)

        print(f"[分析任务] 病人 {patient_id} 分析完成")

    except Exception as e:
        print(f"[分析任务] 病人 {patient_id} 分析失败：{e}")

        try:
            info = read_patient_info(patient_id)
            info["analysis"] = {
                "status": "failed",
                "message": f"分析失败：{str(e)}",
                "started_at": info.get("analysis", {}).get("started_at"),
                "finished_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
            write_patient_info(patient_id, info)
        except Exception as inner_e:
            print(f"[分析任务] 写入失败状态也失败：{inner_e}")
#############




@app.get("/")
def root():
    print('有人进入')
    return {
        "message": "Medical AI backend is running",
        "docs": "/docs",
    }
@app.get("/api/patient/import-demo")
def import_patient_demo():
    print('前后端连接成功')
    return {
        "message": "连接后端成功",
        "patient_id": "C-2026-0128",
        "name": "示例病人",
        "age": 47,
        "gender": "女",
        "stage": "IB2",
        "date": "2026-05-20"
    }

@app.get("/api/report/export-demo")
def export_report_demo():
    print('导出报告成功')
    return {
        "message": "导出报告成功",
        "report_id": "R-2026-0128",
        "patient_id": "C-2026-0128",
        "date": "2026-05-20"
    }
@app.get("/api/patient/list")
@app.get("/api/patient/list")
def list_patients():
    """
    获取服务端已经保存的病人列表。

    逻辑：
    1. 遍历 PATIENT_ROOT 下的所有子文件夹
    2. 每个子文件夹代表一个病人
    3. 使用 read_patient_info(patient_id) 读取 info.json
    4. 将所有病人信息组成列表返回给前端
    """

    if not PATIENT_ROOT.exists():
        raise HTTPException(status_code=404, detail="病人数据目录不存在")

    patients = []

    for patient_dir in PATIENT_ROOT.iterdir():
        # 只处理文件夹，跳过普通文件
        if not patient_dir.is_dir():
            continue

        # 默认用文件夹名作为 patient_id
        patient_id = patient_dir.name

        try:
            # 统一使用 read_patient_info 读取 info.json
            info = read_patient_info(patient_id)

            # 如果 info.json 里有 id，则优先使用 info.json 里的 id
            real_patient_id = info.get("id", patient_id)

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
@app.get("/api/patient/import/{patient_id}")
def import_patient(patient_id: str):
    """
    导入某一个服务端已经保存的病人数据。

    逻辑：
    1. 根据 patient_id 找到 static/patient/{patient_id}
    2. 使用 read_patient_info(patient_id) 读取 info.json
    3. 直接返回 info.json 的完整内容
    """

    patient_dir = PATIENT_ROOT / patient_id

    # 1. 使用统一函数读取 info.json
    info = read_patient_info(patient_id)

    # 2. 如果 info.json 里没有 id，就用文件夹名补一个
    if "id" not in info:
        info["id"] = patient_id

    # 3. 返回这个病人的相关目录信息
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

@app.post("/api/analysis/start")
def start_analysis(req: StartAnalysisRequest):
    """
    接收前端开始分析信号。

    前端请求示例：
    POST /api/analysis/start

    body:
    {
        "patientId": "C-2026-0128",
        "signal": "start_analysis"
    }
    """

    patient_id = req.patientId

    if req.signal != "start_analysis":
        raise HTTPException(
            status_code=400,
            detail="signal 必须是 start_analysis",
        )

    patient_dir = PATIENT_ROOT / patient_id
    info_path = patient_dir / "info.json"

    if not patient_dir.exists() or not patient_dir.is_dir():
        raise HTTPException(
            status_code=404,
            detail=f"未找到病人数据目录：{patient_id}",
        )

    if not info_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"未找到病人信息文件：{patient_id}/info.json",
        )

    info = read_patient_info(patient_id)
    current_status = info.get("analysis", {}).get("status")

    if current_status == "analyzing":
        return {
            "success": True,
            "message": "该病人正在分析中，请勿重复提交",
            "patientId": patient_id,
            "analysis": info.get("analysis"),
        }

    # 先立即写入 analyzing 状态，让前端马上知道已经开始
    info["analysis"] = {
        "status": "analyzing",
        "message": "正在分析",
        "started_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "finished_at": None,
    }
    write_patient_info(patient_id, info)

    # 启动后台线程执行分析任务
    thread = Thread(
        target=run_analysis_task,
        args=(patient_id,),
        daemon=True,
    )
    thread.start()

    print(f"收到开始分析信号：{patient_id}")

    return {
        "success": True,
        "message": "已收到开始分析信号，分析任务已启动",
        "patientId": patient_id,
        "analysis": info["analysis"],
    }
@app.get("/api/analysis/status/{patient_id}")
def get_analysis_status(patient_id: str):
    """
    查询某个病人的分析状态。

    前端如果想知道 5 秒后是否分析完成，
    可以轮询这个接口。
    """

    info = read_patient_info(patient_id)

    return {
        "success": True,
        "patientId": patient_id,
        "analysis": info.get(
            "analysis",
            {
                "status": "not_started",
                "message": "尚未开始分析",
            },
        ),
    }


@app.get("/api/patient/{patient_id}/images")
def get_patient_images(patient_id: str, request: Request):
    """
    自动读取当前目录下：
    patient/{patient_id}/img/ct
    patient/{patient_id}/img/mri
    patient/{patient_id}/img/pet
    patient/{patient_id}/img/pet_ct

    返回前端 MRIViewer 可以直接使用的 images 列表。
    """
    MODALITY_MAP = {
        "mri": "MRI",
        "ct": "CT",
        "pet": "PET",
        "pet_ct": "PET/CT",
    }
    IMAGE_EXTENSIONS = {
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

    # 依次扫描 img 下的各个子文件夹
    for modality_folder in ["mri", "ct", "pet", "pet_ct"]:
        modality_dir = img_dir / modality_folder

        if not modality_dir.exists():
            continue

        image_files = sorted(
            [
                file
                for file in modality_dir.iterdir()
                if file.is_file() and file.suffix.lower() in IMAGE_EXTENSIONS
            ]
        )

        total_slices = len(image_files)

        for index, image_path in enumerate(image_files):
            # 拼成浏览器可访问的静态图片 URL
            image_url = (
                f"{request.base_url}"
                f"{PATIENT_ROOT}/"
                f"{patient_id}/img/{modality_folder}/{image_path.name}"
            )

            images.append(
                {
                    "id": f"{patient_id}-{modality_folder}-slice-{index + 1:03d}",
                    "url": image_url,
                    "modality": MODALITY_MAP.get(modality_folder, modality_folder.upper()),
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

@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    """
    第一版测试接口：
    1. 接收前端上传文件
    2. 保存到 uploads
    3. 暂时返回模拟结果
    """

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
@app.get("/api/patient/{patient_id}/assessment")
def get_patient_assessment(patient_id: str):
    print(f"查询病人 {patient_id} 的评估结果")

    if not patient_id:
        raise HTTPException(status_code=400, detail="patient_id 不能为空")

    # static/patient/C-2026-0128/assessment/assessment.json
    assessment_path = (
        PATIENT_ROOT
        / patient_id
        / "assessment"
        / "assessment.json"
    )

    print("评估文件路径:", assessment_path)

    if not assessment_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"未找到病人评估文件: {assessment_path}"
        )

    try:
        with open(assessment_path, "r", encoding="utf-8") as f:
            assessment_data = json.load(f)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=500,
            detail=f"评估文件 JSON 格式错误: {assessment_path}"
        )
    print(f"成功读取病人 {patient_id} 的评估结果")
    return {
        "patient_id": patient_id,
        "assessments": assessment_data,
    }
@app.get("/api/patient/reasoning/{patient_id}")
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

    if not reasoning_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"未找到病人推理文件: {reasoning_path}"
        )

    try:
        with open(reasoning_path, "r", encoding="utf-8") as f:
            reasoning_data = json.load(f)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=500,
            detail=f"推理文件 JSON 格式错误: {reasoning_path}"
        )
    print(f"成功读取病人 {patient_id} 的推理结果")
    return {
        "patient_id": patient_id,
        "reasoning": reasoning_data,
    }
@app.get("/api/patient/AIreport/{patient_id}")
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

    if not aireportdraft_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"未找到病人 AI 报告草稿文件: {aireportdraft_path}"
        )

    try:
        with open(aireportdraft_path, "r", encoding="utf-8") as f:
            aireportdraft_data = json.load(f)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=500,
            detail=f"AI 报告草稿文件 JSON 格式错误: {aireportdraft_path}"
        )
    print(f"成功读取病人 {patient_id} 的 AI 报告草稿")
    return {
        "patient_id": patient_id,
        "aireportdraft": aireportdraft_data,
    }
@app.get("/api/patient/{patient_id}/key-evidence")
def get_patient_key_evidence(patient_id: str):
    print(f"查询病人 {patient_id} 的关键证据")

    if not patient_id:
        raise HTTPException(status_code=400, detail="patient_id 不能为空")

    keyevidence_path = (
        PATIENT_ROOT
        / patient_id
        / "keyevidence"
        / "keyevidence.json"
    )

    print("关键证据文件路径:", keyevidence_path)

    if not keyevidence_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"未找到病人关键证据文件: {keyevidence_path}"
        )

    try:
        with open(keyevidence_path, "r", encoding="utf-8") as f:
            keyevidence_data = json.load(f)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=500,
            detail=f"关键证据文件 JSON 格式错误: {keyevidence_path}"
        )

    print(f"成功读取病人 {patient_id} 的关键证据")

    return {
        "patient_id": patient_id,
        "evidenceItems": keyevidence_data,
    }
class DoctorFeedbackRequest(BaseModel):
    feedback: str
    comment: str = ""
@app.post("/api/patient/{patient_id}/doctor-feedback")
def save_doctor_feedback(patient_id: str, payload: DoctorFeedbackRequest):
    print(f"保存病人 {patient_id} 的医生反馈")

    if not patient_id:
        raise HTTPException(status_code=400, detail="patient_id 不能为空")

    patient_dir = PATIENT_ROOT / patient_id

    if not patient_dir.exists() or not patient_dir.is_dir():
        raise HTTPException(
            status_code=404,
            detail=f"未找到病人目录: {patient_dir}"
        )

    feedback_dir = patient_dir / "doctor_feedback"
    feedback_dir.mkdir(parents=True, exist_ok=True)

    feedback_path = feedback_dir / "doctor_feedback.json"

    feedback_data = {
        "patient_id": patient_id,
        "feedback": payload.feedback,
        "comment": payload.comment,
        "saved_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    try:
        with open(feedback_path, "w", encoding="utf-8") as f:
            json.dump(feedback_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"保存医生反馈失败: {str(e)}"
        )

    print("医生反馈保存路径:", feedback_path)

    return {
        "patient_id": patient_id,
        "message": "医生反馈保存成功",
        "feedback_path": str(feedback_path),
        "data": feedback_data,
    }
#uvicorn main:app --reload --host 0.0.0.0 --port 8000