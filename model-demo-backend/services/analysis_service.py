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

        started_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 同时更新中英文为 analyzing
        for target_lang in ["zh", "en"]:
            info = read_patient_info(patient_id, target_lang)

            info["analysis"] = {
                "status": "analyzing",
                "message": _text(target_lang, "正在分析", "Analyzing"),
                "started_at": started_at,
                "finished_at": None,
            }

            write_patient_info(patient_id, info, target_lang)

        # 调用分析主流程
        ollama_result = asyncio.run(
            generate_all_patient_outputs_with_ollama(
                patient_id=patient_id,
                language=lang,
            )
        )

        finished_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 同时更新中英文为 completed
        for target_lang in ["zh", "en"]:
            info = read_patient_info(patient_id, target_lang)

            old_started_at = info.get("analysis", {}).get("started_at", started_at)

            info["analysis"] = {
                "status": "completed",
                "message": _text(target_lang, "分析完成", "Analysis completed"),
                "started_at": old_started_at,
                "finished_at": finished_at,
                "result": {},
            }

            write_patient_info(patient_id, info, target_lang)

        print(f"[分析任务] 病人 {patient_id} 分析完成")
        print(f"[分析任务] Ollama 生成结果已写入病人目录：{ollama_result.keys()}")

    except Exception as e:
        print(f"[分析任务] 病人 {patient_id} 分析失败：{e}")

        try:
            finished_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # 同时更新中英文为 failed
            for target_lang in ["zh", "en"]:
                info = read_patient_info(patient_id, target_lang)

                old_started_at = info.get("analysis", {}).get("started_at")

                info["analysis"] = {
                    "status": "failed",
                    "message": _text(
                        target_lang,
                        f"分析失败：{str(e)}",
                        f"Analysis failed: {str(e)}"
                    ),
                    "started_at": old_started_at,
                    "finished_at": finished_at,
                }

                write_patient_info(patient_id, info, target_lang)

        except Exception as inner_e:
            print(f"[分析任务] 写入失败状态也失败：{inner_e}")