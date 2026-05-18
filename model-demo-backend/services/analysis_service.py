import time
from datetime import datetime

from services.patient_service import read_patient_info, write_patient_info


def run_analysis_task(patient_id: str):
    try:
        print(f"[分析任务] 病人 {patient_id} 开始分析")

        info = read_patient_info(patient_id)
        info["analysis"] = {
            "status": "analyzing",
            "message": "正在分析",
            "started_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "finished_at": None,
        }
        write_patient_info(patient_id, info)

        time.sleep(5)

        info = read_patient_info(patient_id)
        info["analysis"] = {
            "status": "completed",
            "message": "分析完成",
            "started_at": info.get("analysis", {}).get("started_at"),
            "finished_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "result": {},
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