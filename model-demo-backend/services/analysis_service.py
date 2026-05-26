import time
import asyncio
from datetime import datetime
from typing import Optional

from services.file_service import normalize_language
from services.patient_service import read_patient_info, write_patient_info
from services.ollama_service import generate_all_patient_outputs_with_ollama


def _text(lang: str, zh: str, en: str) -> str:
    return en if lang == "en" else zh


def run_analysis_task(patient_id: str, language: Optional[str] = "zh"):
    lang = normalize_language(language)

    try:
        print(f"[分析任务] 病人 {patient_id} 开始分析，language={lang}")

        info = read_patient_info(patient_id, lang)

        started_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        info["analysis"] = {
            "status": "analyzing",
            "message": _text(lang, "正在分析", "Analyzing"),
            "started_at": started_at,
            "finished_at": None,
        }

        write_patient_info(patient_id, info, lang)

        # ================================
        # 调用 Ollama 生成 4 个前端模块对应的 JSON 文件：
        # 1. assessment/assessment_{lang}.json
        # 2. reasoning/reasoning_{lang}.json
        # 3. aireportdraft/aireportdraft_{lang}.json
        # 4. keyevidence/keyevidence_{lang}.json
        # ================================
        ollama_result = asyncio.run(
            generate_all_patient_outputs_with_ollama(
                patient_id=patient_id,
                language=lang,
            )
        )

        # 再次读取，避免覆盖其他地方更新过的 info
        info = read_patient_info(patient_id, lang)

        info["analysis"] = {
            "status": "completed",
            "message": _text(lang, "分析完成", "Analysis completed"),
            "started_at": info.get("analysis", {}).get("started_at", started_at),
            "finished_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "result": {},
        }

        write_patient_info(patient_id, info, lang)

        print(f"[分析任务] 病人 {patient_id} 分析完成")
        print(f"[分析任务] Ollama 生成结果已写入病人目录：{ollama_result.keys()}")

    except Exception as e:
        print(f"[分析任务] 病人 {patient_id} 分析失败：{e}")

        try:
            info = read_patient_info(patient_id, lang)

            info["analysis"] = {
                "status": "failed",
                "message": _text(
                    lang,
                    f"分析失败：{str(e)}",
                    f"Analysis failed: {str(e)}"
                ),
                "started_at": info.get("analysis", {}).get("started_at"),
                "finished_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }

            write_patient_info(patient_id, info, lang)

        except Exception as inner_e:
            print(f"[分析任务] 写入失败状态也失败：{inner_e}")