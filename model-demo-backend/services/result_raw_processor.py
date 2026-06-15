# services/result_raw_processor.py

import json
from pathlib import Path
from typing import Any, Optional

from core.config import PATIENT_ROOT
from services.file_service import normalize_language


def _localized_file(patient_id: str, folder: str, stem: str, lang: str) -> Path:
    """
    生成本地化 JSON 文件路径。

    例如：
      static/patient/11111/assessment/assessment_zh.json
      static/patient/11111/assessment/assessment_en.json
    """
    return PATIENT_ROOT / patient_id / folder / f"{stem}_{lang}.json"


def _save_json(path: Path, data: Any) -> Any:
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return data


def read_patient_info_from_file(patient_id: str, language: Optional[str] = "zh") -> dict:
    """
    读取当前病人的 info_{lang}.json。

    如果 info_en.json 不存在，会兜底读取 info_zh.json。
    """
    lang = normalize_language(language)

    info_path = PATIENT_ROOT / patient_id / f"info_{lang}.json"

    if not info_path.exists():
        info_path = PATIENT_ROOT / patient_id / "info_zh.json"

    if not info_path.exists():
        return {}

    with open(info_path, "r", encoding="utf-8") as f:
        return json.load(f)


def _unwrap_result_raw(result_raw: dict) -> dict:
    """
    兼容两种输入：

    1. {
         "result_raw": {
           "lymph": {...},
           "parametrium": {...}
         }
       }

    2. {
         "lymph": {...},
         "parametrium": {...}
       }
    """
    if not isinstance(result_raw, dict):
        return {}

    return result_raw.get("result_raw", result_raw)


def _percent(score: Optional[float]) -> int:
    """
    0.3394 -> 34
    0.5117 -> 51
    """
    if score is None:
        return 0

    try:
        return int(round(float(score) * 100))
    except Exception:
        return 0


def _is_en(lang: Optional[str]) -> bool:
    return normalize_language(lang) == "en"


def _txt(lang: Optional[str], zh: str, en: str) -> str:
    return en if _is_en(lang) else zh


def _simple_diag_text(diagnosis: Optional[str], lang: Optional[str] = "zh") -> str:
    if diagnosis == "positive":
        return _txt(lang, "阳性", "Positive")
    if diagnosis == "negative":
        return _txt(lang, "阴性", "Negative")
    return _txt(lang, "不确定", "Indeterminate")


def _diagnosis_text(
    task_name: str,
    diagnosis: Optional[str],
    lang: Optional[str] = "zh",
) -> str:
    if _is_en(lang):
        if diagnosis == "positive":
            return f"{task_name}: positive."
        if diagnosis == "negative":
            return f"{task_name}: negative."
        return f"{task_name}: indeterminate."

    if diagnosis == "positive":
        return f"{task_name}阳性"
    if diagnosis == "negative":
        return f"{task_name}阴性"
    return f"{task_name}结果不确定"


def _risk_style_from_score(
    score: Optional[float],
    lang: Optional[str] = "zh",
) -> dict:
    """
    根据 avg_cls_score 生成前端风险样式。

    当前规则：
      score >= 0.6        高风险
      0.25 <= score < 0.6 中等风险
      score < 0.25        低风险
    """
    if score is None:
        return {
            "riskText": _txt(lang, "未知风险", "Unknown risk"),
            "riskColor": "gray",
            "strokeColor": "#64748b",
            "railColor": "#e2e8f0",
            "borderClassName": "border-slate-200",
            "bgClassName": "bg-slate-50",
            "titleClassName": "text-slate-500",
        }

    try:
        score = float(score)
    except Exception:
        score = 0.0

    if score >= 0.6:
        return {
            "riskText": _txt(lang, "高风险", "High risk"),
            "riskColor": "red",
            "strokeColor": "#ef4444",
            "railColor": "#fee2e2",
            "borderClassName": "border-red-200",
            "bgClassName": "bg-red-50",
            "titleClassName": "text-red-500",
        }

    if score >= 0.25:
        return {
            "riskText": _txt(lang, "中等风险", "Intermediate risk"),
            "riskColor": "orange",
            "strokeColor": "#f59e0b",
            "railColor": "#ffedd5",
            "borderClassName": "border-orange-200",
            "bgClassName": "bg-orange-50",
            "titleClassName": "text-orange-500",
        }

    return {
        "riskText": _txt(lang, "低风险", "Low risk"),
        "riskColor": "green",
        "strokeColor": "#22c55e",
        "railColor": "#dcfce7",
        "borderClassName": "border-green-200",
        "bgClassName": "bg-green-50",
        "titleClassName": "text-green-600",
    }


def _evidence_style_from_trust(
    trust: bool,
    lang: Optional[str] = "zh",
) -> dict:
    """
    模型 trust 字段 -> 前端证据充分性字段。
    """
    if trust:
        return {
            "evidenceSufficiency": _txt(lang, "较充分", "Sufficient"),
            "evidenceClassName": "text-green-600",
            "modelConsistency": _txt(lang, "高", "High"),
        }

    return {
        "evidenceSufficiency": _txt(lang, "不足", "Insufficient"),
        "evidenceClassName": "text-red-500",
        "modelConsistency": _txt(lang, "低", "Low"),
    }


def _slice_ratio(task_raw: dict) -> str:
    """
    生成 positiveSliceRatio。

    当前模型返回：
      n_slices
      per_modal.xxx.vote
      per_modal.xxx.n

    如果没有逐 slice 阳性数量，就用 vote * n 近似。
    """
    if not isinstance(task_raw, dict):
        return "0 / 0"

    n_slices = int(task_raw.get("n_slices") or 0)

    vote_sum = 0
    per_modal = task_raw.get("per_modal") or {}

    if isinstance(per_modal, dict):
        for item in per_modal.values():
            if not isinstance(item, dict):
                continue

            vote = int(item.get("vote") or 0)
            n = int(item.get("n") or 0)
            vote_sum += vote * n

    if n_slices <= 0:
        return "0 / 0"

    return f"{vote_sum} / {n_slices}"


def _normalize_set(values: Any) -> set:
    if not isinstance(values, list):
        return set()

    return {
        str(x).strip().lower().replace("-", "/").replace("_", "/")
        for x in values
        if str(x).strip()
    }


def build_evidence_items_from_patient_info(
    patient_info: dict,
    lang: Optional[str] = "zh",
) -> list:
    """
    根据当前病人的 info_{lang}.json 生成 reasoning 里的“证据充分性检查”。

    使用字段：
      modalities
      mriSequences
      clinicalHistoryStatus
    """
    if not isinstance(patient_info, dict):
        patient_info = {}

    modalities = patient_info.get("modalities") or []
    mri_sequences = patient_info.get("mriSequences") or []
    clinical_status = patient_info.get("clinicalHistoryStatus")

    modalities_norm = _normalize_set(modalities)
    mri_sequences_norm = _normalize_set(mri_sequences)

    has_mri = (
        "mri" in modalities_norm
        or len(mri_sequences_norm) > 0
    )

    has_ct = "ct" in modalities_norm

    has_petct = (
        "pet/ct" in modalities_norm
        or "petct" in modalities_norm
        or "pet" in modalities_norm
        or "pet/ct" in {x.replace(" ", "") for x in modalities_norm}
    )

    def modality_item(name: str, provided: bool) -> dict:
        if provided:
            return {
                "name": name,
                "status": _txt(lang, "已提供", "Provided"),
                "className": "text-green-600",
            }

        return {
            "name": name,
            "status": _txt(lang, "缺失", "Missing"),
            "className": "text-red-500",
        }

    clinical_status_norm = str(clinical_status or "").strip().lower()

    if clinical_status_norm in {
        "provided",
        "complete",
        "full",
        "yes",
        "true",
        "已提供",
        "完整",
        "充分",
    }:
        clinical_item = {
            "name": _txt(lang, "临床病史", "Clinical history"),
            "status": _txt(lang, "已提供", "Provided"),
            "className": "text-green-600",
        }
    elif clinical_status_norm in {
        "partial",
        "partially",
        "incomplete",
        "部分缺失",
        "部分提供",
        "不完整",
    }:
        clinical_item = {
            "name": _txt(lang, "临床病史", "Clinical history"),
            "status": _txt(lang, "部分缺失", "Partially missing"),
            "className": "text-orange-500",
        }
    else:
        clinical_item = {
            "name": _txt(lang, "临床病史", "Clinical history"),
            "status": _txt(lang, "缺失", "Missing"),
            "className": "text-red-500",
        }

    return [
        modality_item("MRI", has_mri),
        modality_item("PET/CT", has_petct),
        modality_item("CT", has_ct),
        clinical_item,
    ]


def _safe_model_text(
    task_name_zh: str,
    task_name_en: str,
    task_raw: dict,
    lang: Optional[str] = "zh",
) -> str:
    """
    中文：优先使用模型返回的 recommendation_text。
    英文：不直接使用中文 recommendation_text，而是根据 diagnosis 生成英文文本。
    """
    if not isinstance(task_raw, dict):
        task_raw = {}

    if not _is_en(lang):
        return task_raw.get("recommendation_text") or _diagnosis_text(
            task_name_zh,
            task_raw.get("diagnosis"),
            lang,
        )

    return _diagnosis_text(
        task_name_en,
        task_raw.get("diagnosis"),
        lang,
    )


def build_assessment_from_result_raw(
    result_raw: dict,
    lang: Optional[str] = "zh",
) -> dict:
    """
    从 result_raw 生成 assessment_{lang}.json。
    """
    lang = normalize_language(lang)
    raw = _unwrap_result_raw(result_raw)

    lymph = raw.get("lymph") or {}
    para = raw.get("parametrium") or {}

    lymph_score = lymph.get("avg_cls_score")
    para_score = para.get("avg_cls_score")

    lymph_risk = _risk_style_from_score(lymph_score, lang)
    para_risk = _risk_style_from_score(para_score, lang)

    lymph_evidence = _evidence_style_from_trust(bool(lymph.get("trust")), lang)
    para_evidence = _evidence_style_from_trust(bool(para.get("trust")), lang)

    return {
        "assessment": [
            {
                "title": _txt(
                    lang,
                    "盆腔淋巴结转移",
                    "Pelvic lymph node metastasis",
                ),
                "riskText": lymph_risk["riskText"],
                "riskColor": lymph_risk["riskColor"],
                "percent": _percent(lymph_score),
                "strokeColor": lymph_risk["strokeColor"],
                "railColor": lymph_risk["railColor"],
                "borderClassName": lymph_risk["borderClassName"],
                "bgClassName": lymph_risk["bgClassName"],
                "evidenceSufficiency": lymph_evidence["evidenceSufficiency"],
                "evidenceClassName": lymph_evidence["evidenceClassName"],
                "modelConsistency": lymph_evidence["modelConsistency"],
                "positiveSliceRatio": _slice_ratio(lymph),
                # "keyFinding": _safe_model_text(
                #     "盆腔淋巴结转移",
                #     "Pelvic lymph node metastasis",
                #     lymph,
                #     lang,
                # ),
            },
            {
                "title": _txt(
                    lang,
                    "宫旁浸润",
                    "Parametrial invasion",
                ),
                "riskText": para_risk["riskText"],
                "riskColor": para_risk["riskColor"],
                "percent": _percent(para_score),
                "strokeColor": para_risk["strokeColor"],
                "railColor": para_risk["railColor"],
                "borderClassName": para_risk["borderClassName"],
                "bgClassName": para_risk["bgClassName"],
                "evidenceSufficiency": para_evidence["evidenceSufficiency"],
                "evidenceClassName": para_evidence["evidenceClassName"],
                "modelConsistency": para_evidence["modelConsistency"],
                "positiveSliceRatio": _slice_ratio(para),
                # "keyFinding": _safe_model_text(
                #     "宫旁浸润",
                #     "Parametrial invasion",
                #     para,
                #     lang,
                # ),
            },
        ]
    }


def build_reasoning_from_result_raw(
    result_raw: dict,
    patient_info: Optional[dict] = None,
    lang: Optional[str] = "zh",
) -> dict:
    """
    从 result_raw + 当前病人 info_{lang}.json 生成 reasoning_{lang}.json。

    修改点：
    - 不再生成统一的“下一步建议”
    - 改成两个 suggestions：
      1. 淋巴结建议
      2. 宫旁建议
    - 建议内容直接使用 result_raw 中的 recommendation_text
    """
    lang = normalize_language(lang)
    raw = _unwrap_result_raw(result_raw)

    lymph = raw.get("lymph") or {}
    para = raw.get("parametrium") or {}

    evidence_status = raw.get("evidence_status", "insufficient")
    sufficient = evidence_status == "sufficient"

    lymph_diag = lymph.get("diagnosis")
    para_diag = para.get("diagnosis")

    lymph_score = lymph.get("avg_cls_score")
    para_score = para.get("avg_cls_score")

    evidence_items = build_evidence_items_from_patient_info(
        patient_info or {},
        lang,
    )

    # 直接使用模型返回的 recommendation_text
    patient_id = (
        raw.get("patient_id")
        or (patient_info or {}).get("id")
        or (patient_info or {}).get("patient_id")
        or _txt(lang, "当前病人", "the current patient")
    )


    def _make_advice_from_raw(
        task_raw: dict,
        task_name_zh: str,
        task_name_en: str,
    ) -> str:
        """
        中文：优先使用模型返回的 recommendation_text。
        英文：不要直接使用中文 recommendation_text，而是根据 trust / diagnosis 自动生成英文建议。
        """
        if not isinstance(task_raw, dict):
            task_raw = {}

        trust = bool(task_raw.get("trust"))
        diagnosis = task_raw.get("diagnosis")

        # 中文直接使用模型返回文本
        if not _is_en(lang):
            return task_raw.get("recommendation_text") or (
                f"暂无{task_name_zh}相关建议。"
            )

        # 如果以后模型支持英文建议，可以优先读取这些字段
        english_text = (
            task_raw.get("recommendation_text_en")
            or task_raw.get("recommendation_en")
            or task_raw.get("recommendationTextEn")
        )

        if english_text:
            return english_text

        # 英文兜底生成
        if trust:
            if diagnosis == "positive":
                return (
                    f"For patient {patient_id}, {task_name_en} is reliably assessed as positive. "
                    "Further imaging is not immediately required, but physician review is still recommended."
                )

            if diagnosis == "negative":
                return (
                    f"For patient {patient_id}, {task_name_en} is reliably assessed as negative. "
                    "Further imaging is not prioritized unless clinically indicated."
                )

            return (
                f"For patient {patient_id}, the assessment of {task_name_en} is reliable but indeterminate. "
                "Physician review is recommended before deciding whether additional imaging is needed."
            )

        return (
            f"For patient {patient_id}, the current conclusion for {task_name_en} is not reliable. "
            "Additional PET/CT or other necessary imaging is recommended before final assessment."
        )


    lymph_advice = _make_advice_from_raw(
        lymph,
        "淋巴结转移",
        "lymph node metastasis",
    )

    para_advice = _make_advice_from_raw(
        para,
        "宫旁浸润",
        "parametrial invasion",
    )

    if sufficient:
        conclusion = _txt(
            lang,
            (
                "模型已完成可信判定："
                f"盆腔淋巴结转移{_simple_diag_text(lymph_diag, lang)}；"
                f"宫旁浸润{_simple_diag_text(para_diag, lang)}。"
            ),
            (
                "The model has completed a trusted assessment: "
                f"pelvic lymph node metastasis is {_simple_diag_text(lymph_diag, lang).lower()}; "
                f"parametrial invasion is {_simple_diag_text(para_diag, lang).lower()}."
            ),
        )

        conclusion_class = (
            "text-red-600"
            if para_diag == "positive" or lymph_diag == "positive"
            else "text-green-600"
        )

        warning = _txt(
            lang,
            "当前模型结果可信，但仍建议结合完整影像序列、临床资料和医生复核后形成最终术前结论。",
            "The model output is considered reliable, but the final preoperative conclusion should still be made together with complete imaging, clinical history, and physician review.",
        )

    else:
        conclusion = _txt(
            lang,
            "当前证据不足，不能形成明确术前结论。",
            "Current evidence is insufficient to form a definite preoperative conclusion.",
        )

        conclusion_class = "text-orange-600"

        warning = _txt(
            lang,
            "模型提示当前证据不足，存在误判风险，建议补充影像资料后再进行综合判断。",
            "The model indicates insufficient evidence and a risk of misclassification; additional imaging data are recommended before comprehensive assessment.",
        )

    summary_content = _txt(
        lang,
        (
            "模型基于当前输入图像完成盆腔淋巴结转移与宫旁浸润两项任务评估。"
            f"淋巴结转移风险分数为 {_percent(lymph_score)}%，"
            f"宫旁浸润风险分数为 {_percent(para_score)}%。"
        ),
        (
            "The model assessed pelvic lymph node metastasis and parametrial invasion based on the current input images. "
            f"The risk score for lymph node metastasis is {_percent(lymph_score)}%, "
            f"and the risk score for parametrial invasion is {_percent(para_score)}%."
        ),
    )

    return {
        "reasoning": [
            {
                "type": "summary",
                "title": _txt(lang, "推理摘要", "Reasoning summary"),
                "content": summary_content,
                "className": "text-blue-700",
            },
            {
                "type": "conclusion",
                "title": _txt(lang, "评估结论", "Assessment conclusion"),
                "content": conclusion,
                "className": conclusion_class,
            },
            {
                "type": "evidence",
                "title": _txt(lang, "证据充分性检查", "Evidence sufficiency check"),
                "items": evidence_items,
            },
            {
                "type": "warning",
                "title": _txt(lang, "风险提示", "Risk warning"),
                "content": warning,
                "className": "text-red-600",
            },
            {
                "type": "suggestions",
                "title": _txt(lang, "淋巴结建议", "Lymph node recommendation"),
                "items": [
                    lymph_advice,
                ],
            },
            {
                "type": "suggestions",
                "title": _txt(lang, "宫旁建议", "Parametrial recommendation"),
                "items": [
                    para_advice,
                ],
            },
        ]
    }


def build_aireportdraft_from_result_raw(
    result_raw: dict,
    lang: Optional[str] = "zh",
) -> dict:
    """
    从 result_raw 生成 aireportdraft_{lang}.json。
    """
    lang = normalize_language(lang)
    raw = _unwrap_result_raw(result_raw)

    lymph = raw.get("lymph") or {}
    para = raw.get("parametrium") or {}

    lymph_score = lymph.get("avg_cls_score")
    para_score = para.get("avg_cls_score")

    lymph_risk = _risk_style_from_score(lymph_score, lang)
    para_risk = _risk_style_from_score(para_score, lang)

    lymph_text = _safe_model_text(
        "盆腔淋巴结转移",
        "Pelvic lymph node metastasis",
        lymph,
        lang,
    )

    para_text = _safe_model_text(
        "宫旁浸润",
        "Parametrial invasion",
        para,
        lang,
    )

    if raw.get("evidence_status") == "sufficient":
        suggestion = _txt(
            lang,
            (
                "当前模型提示影像证据较充分，可将上述 AI 结果作为术前辅助评估参考。"
                "最终诊疗决策仍需结合医生阅片、临床病史、实验室检查及 MDT 讨论综合判断。"
            ),
            (
                "The model indicates that the imaging evidence is relatively sufficient. "
                "The above AI results may be used as auxiliary preoperative assessment references. "
                "Final clinical decisions should still be made together with physician review, clinical history, laboratory findings, and MDT discussion."
            ),
        )
    else:
        suggestion = _txt(
            lang,
            (
                "当前模型提示证据不足，建议补充完整影像资料和临床病史后再次分析。"
                "在证据不足情况下，不建议仅凭 AI 结果形成确定性术前结论。"
            ),
            (
                "The model indicates insufficient evidence. Complete imaging data and clinical history should be supplemented before re-analysis. "
                "When evidence is insufficient, a definitive preoperative conclusion should not be made based only on the AI result."
            ),
        )

    return {
        "aireportdraft": [
            {
                "title": _txt(
                    lang,
                    "盆腔淋巴结评估：",
                    "Pelvic lymph node assessment:",
                ),
                "content": _txt(
                    lang,
                    (
                        f"AI 模型评估盆腔淋巴结转移风险分数为 {_percent(lymph_score)}%。"
                        f"{lymph_text}"
                    ),
                    (
                        f"The AI model estimated the risk score for pelvic lymph node metastasis as {_percent(lymph_score)}%. "
                        f"{lymph_text}"
                    ),
                ),
                "titleClassName": lymph_risk["titleClassName"],
            },
            {
                "title": _txt(
                    lang,
                    "宫旁浸润评估：",
                    "Parametrial invasion assessment:",
                ),
                "content": _txt(
                    lang,
                    (
                        f"AI 模型评估宫旁浸润风险分数为 {_percent(para_score)}%。"
                        f"{para_text}"
                    ),
                    (
                        f"The AI model estimated the risk score for parametrial invasion as {_percent(para_score)}%. "
                        f"{para_text}"
                    ),
                ),
                "titleClassName": para_risk["titleClassName"],
            },
            {
                "title": _txt(lang, "最终建议：", "Final recommendation:"),
                "content": suggestion,
                "titleClassName": "text-blue-600",
            },
        ]
    }


def build_keyevidence_from_result_raw(
    result_raw: dict,
    patient_info: Optional[dict] = None,
    lang: Optional[str] = "zh",
) -> dict:
    """
    从 result_raw + info_{lang}.json 生成 keyevidence_{lang}.json。
    """
    lang = normalize_language(lang)
    raw = _unwrap_result_raw(result_raw)

    lymph = raw.get("lymph") or {}
    para = raw.get("parametrium") or {}

    lymph_score = lymph.get("avg_cls_score")
    para_score = para.get("avg_cls_score")

    lymph_trust = bool(lymph.get("trust"))
    para_trust = bool(para.get("trust"))

    lymph_diag = lymph.get("diagnosis")
    para_diag = para.get("diagnosis")

    patient_info = patient_info or {}
    mri_sequences = patient_info.get("mriSequences") or []
    mri_sequences_norm = _normalize_set(mri_sequences)

    key_items = []

    def add_mri_item(seq_key: str, title_zh: str, title_en: str):
        if seq_key in mri_sequences_norm:
            key_items.append({
                "title": _txt(lang, f"{title_zh} 已提供", f"{title_en} provided"),
                "color": "green",
                "status": _txt(lang, "已提供", "Provided"),
                "highlight": True,
            })
        else:
            key_items.append({
                "title": _txt(lang, f"{title_zh} 缺失", f"{title_en} missing"),
                "color": "red",
                "status": _txt(lang, "缺失", "Missing"),
                "missing": True,
            })

    add_mri_item("t1", "MRI T1", "MRI T1")

    if "t2" in mri_sequences_norm or "t2wi" in mri_sequences_norm:
        key_items.append({
            "title": _txt(lang, "MRI T2WI 已提供", "MRI T2WI provided"),
            "color": "green",
            "status": _txt(lang, "已提供", "Provided"),
            "highlight": True,
        })
    else:
        key_items.append({
            "title": _txt(lang, "MRI T2WI 缺失", "MRI T2WI missing"),
            "color": "red",
            "status": _txt(lang, "缺失", "Missing"),
            "missing": True,
        })

    add_mri_item("t1ce", "MRI T1CE", "MRI T1CE")

    key_items.extend([
        {
            "title": _txt(
                lang,
                (
                    f"盆腔淋巴结转移：{_simple_diag_text(lymph_diag, lang)}，"
                    f"风险分数 {_percent(lymph_score)}%"
                ),
                (
                    f"Pelvic lymph node metastasis: {_simple_diag_text(lymph_diag, lang)}, "
                    f"risk score {_percent(lymph_score)}%"
                ),
            ),
            "color": (
                "red"
                if lymph_diag == "positive"
                else "green"
                if lymph_diag == "negative"
                else "orange"
            ),
            "status": _txt(lang, "可信", "Trusted") if lymph_trust else _txt(lang, "证据不足", "Insufficient evidence"),
            "highlight": lymph_trust,
            "missing": not lymph_trust,
        },
        {
            "title": _txt(
                lang,
                (
                    f"宫旁浸润：{_simple_diag_text(para_diag, lang)}，"
                    f"风险分数 {_percent(para_score)}%"
                ),
                (
                    f"Parametrial invasion: {_simple_diag_text(para_diag, lang)}, "
                    f"risk score {_percent(para_score)}%"
                ),
            ),
            "color": (
                "red"
                if para_diag == "positive"
                else "green"
                if para_diag == "negative"
                else "orange"
            ),
            "status": _txt(lang, "可信", "Trusted") if para_trust else _txt(lang, "证据不足", "Insufficient evidence"),
            "highlight": para_trust,
            "missing": not para_trust,
        },
    ])

    return {"keyevidence": key_items}


def build_all_outputs_from_result_raw(
    result_raw: dict,
    patient_info: Optional[dict] = None,
    language: Optional[str] = "zh",
) -> dict:
    """
    只构造四个模块，不保存文件。
    """
    lang = normalize_language(language)

    return {
        "assessment": build_assessment_from_result_raw(result_raw, lang),
        "reasoning": build_reasoning_from_result_raw(result_raw, patient_info, lang),
        "aireportdraft": build_aireportdraft_from_result_raw(result_raw, lang),
        "keyevidence": build_keyevidence_from_result_raw(result_raw, patient_info, lang),
    }


def save_patient_outputs_from_result_raw(
    patient_id: str,
    result_raw: dict,
    language: Optional[str] = "zh",
) -> dict:
    """
    从 result_raw 生成并保存四个前端模块。

    保存路径：
      static/patient/{id}/assessment/assessment_zh.json
      static/patient/{id}/assessment/assessment_en.json
      static/patient/{id}/reasoning/reasoning_zh.json
      static/patient/{id}/reasoning/reasoning_en.json
      static/patient/{id}/aireportdraft/aireportdraft_zh.json
      static/patient/{id}/aireportdraft/aireportdraft_en.json
      static/patient/{id}/keyevidence/keyevidence_zh.json
      static/patient/{id}/keyevidence/keyevidence_en.json
    """
    lang = normalize_language(language)

    patient_info = read_patient_info_from_file(patient_id, lang)

    generated = build_all_outputs_from_result_raw(
        result_raw=result_raw,
        patient_info=patient_info,
        language=lang,
    )

    assessment = _save_json(
        _localized_file(patient_id, "assessment", "assessment", lang),
        generated["assessment"],
    )

    reasoning = _save_json(
        _localized_file(patient_id, "reasoning", "reasoning", lang),
        generated["reasoning"],
    )

    aireportdraft = _save_json(
        _localized_file(patient_id, "aireportdraft", "aireportdraft", lang),
        generated["aireportdraft"],
    )

    keyevidence = _save_json(
        _localized_file(patient_id, "keyevidence", "keyevidence", lang),
        generated["keyevidence"],
    )

    return {
        "assessment": assessment,
        "reasoning": reasoning,
        "aireportdraft": aireportdraft,
        "keyevidence": keyevidence,
    }