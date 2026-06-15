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
      static/patient/11111/reasoning/reasoning_zh.json
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

    优先读取：
      static/patient/{patient_id}/info_zh.json

    如果当前语言文件不存在，兜底读取：
      static/patient/{patient_id}/info_zh.json
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


def _simple_diag_text(diagnosis: Optional[str]) -> str:
    if diagnosis == "positive":
        return "阳性"
    if diagnosis == "negative":
        return "阴性"
    return "不确定"


def _diagnosis_text(task_name: str, diagnosis: Optional[str]) -> str:
    if diagnosis == "positive":
        return f"{task_name}阳性"
    if diagnosis == "negative":
        return f"{task_name}阴性"
    return f"{task_name}结果不确定"


def _risk_style_from_score(score: Optional[float]) -> dict:
    """
    根据 avg_cls_score 生成前端风险样式。

    当前规则：
      score >= 0.6        高风险
      0.25 <= score < 0.6 中等风险
      score < 0.25        低风险
    """
    if score is None:
        return {
            "riskText": "未知风险",
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
            "riskText": "高风险",
            "riskColor": "red",
            "strokeColor": "#ef4444",
            "railColor": "#fee2e2",
            "borderClassName": "border-red-200",
            "bgClassName": "bg-red-50",
            "titleClassName": "text-red-500",
        }

    if score >= 0.25:
        return {
            "riskText": "中等风险",
            "riskColor": "orange",
            "strokeColor": "#f59e0b",
            "railColor": "#ffedd5",
            "borderClassName": "border-orange-200",
            "bgClassName": "bg-orange-50",
            "titleClassName": "text-orange-500",
        }

    return {
        "riskText": "低风险",
        "riskColor": "green",
        "strokeColor": "#22c55e",
        "railColor": "#dcfce7",
        "borderClassName": "border-green-200",
        "bgClassName": "bg-green-50",
        "titleClassName": "text-green-600",
    }


def _evidence_style_from_trust(trust: bool) -> dict:
    """
    模型 trust 字段 -> 前端证据充分性字段。
    """
    if trust:
        return {
            "evidenceSufficiency": "较充分",
            "evidenceClassName": "text-green-600",
            "modelConsistency": "高",
        }

    return {
        "evidenceSufficiency": "不足",
        "evidenceClassName": "text-red-500",
        "modelConsistency": "低",
    }


def _slice_ratio(task_raw: dict) -> str:
    """
    生成 positiveSliceRatio。

    当前模型返回：
      n_slices
      per_modal.t2.vote
      per_modal.t2.n

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


def build_evidence_items_from_patient_info(patient_info: dict) -> list:
    """
    根据当前病人的 info_zh.json 生成 reasoning 里的“证据充分性检查”。

    使用字段：
      modalities
      mriSequences
      clinicalHistoryStatus

    示例：
      modalities: ["MRI", "CT"]
      mriSequences: ["T1"]
      clinicalHistoryStatus: "partial"

    生成：
      MRI 已提供
      PET/CT 缺失
      CT 已提供
      临床病史 部分缺失
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
                "status": "已提供",
                "className": "text-green-600",
            }

        return {
            "name": name,
            "status": "缺失",
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
            "name": "临床病史",
            "status": "已提供",
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
            "name": "临床病史",
            "status": "部分缺失",
            "className": "text-orange-500",
        }
    else:
        clinical_item = {
            "name": "临床病史",
            "status": "缺失",
            "className": "text-red-500",
        }

    return [
        modality_item("MRI", has_mri),
        modality_item("PET/CT", has_petct),
        modality_item("CT", has_ct),
        clinical_item,
    ]


def build_assessment_from_result_raw(result_raw: dict) -> dict:
    """
    从 result_raw 生成 assessment_zh.json。
    """
    raw = _unwrap_result_raw(result_raw)

    lymph = raw.get("lymph") or {}
    para = raw.get("parametrium") or {}

    lymph_score = lymph.get("avg_cls_score")
    para_score = para.get("avg_cls_score")

    lymph_risk = _risk_style_from_score(lymph_score)
    para_risk = _risk_style_from_score(para_score)

    lymph_evidence = _evidence_style_from_trust(bool(lymph.get("trust")))
    para_evidence = _evidence_style_from_trust(bool(para.get("trust")))

    return {
        "assessment": [
            {
                "title": "盆腔淋巴结转移",
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
                "keyFinding": lymph.get("recommendation_text")
                or _diagnosis_text("盆腔淋巴结转移", lymph.get("diagnosis")),
            },
            {
                "title": "宫旁浸润",
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
                "keyFinding": para.get("recommendation_text")
                or _diagnosis_text("宫旁浸润", para.get("diagnosis")),
            },
        ]
    }


def build_reasoning_from_result_raw(
    result_raw: dict,
    patient_info: Optional[dict] = None,
) -> dict:
    """
    从 result_raw + 当前病人 info_zh.json 生成 reasoning_zh.json。

    其中“证据充分性检查”来自 patient_info：
      modalities
      mriSequences
      clinicalHistoryStatus
    """
    raw = _unwrap_result_raw(result_raw)

    lymph = raw.get("lymph") or {}
    para = raw.get("parametrium") or {}

    evidence_status = raw.get("evidence_status", "insufficient")
    sufficient = evidence_status == "sufficient"

    lymph_diag = lymph.get("diagnosis")
    para_diag = para.get("diagnosis")

    lymph_score = lymph.get("avg_cls_score")
    para_score = para.get("avg_cls_score")

    evidence_items = build_evidence_items_from_patient_info(patient_info or {})

    if sufficient:
        conclusion = (
            "模型已完成可信判定："
            f"盆腔淋巴结转移{_simple_diag_text(lymph_diag)}；"
            f"宫旁浸润{_simple_diag_text(para_diag)}。"
        )

        conclusion_class = (
            "text-red-600"
            if para_diag == "positive" or lymph_diag == "positive"
            else "text-green-600"
        )

        warning = (
            "当前模型结果可信，但仍建议结合完整影像序列、临床资料和医生复核后形成最终术前结论。"
        )

        suggestions = [
            "结合医生阅片结果复核 AI 判断",
            "将模型输出作为术前辅助评估依据",
            "如临床表现与模型结果不一致，建议补充多模态影像或 MDT 讨论",
        ]

    else:
        conclusion = "当前证据不足，不能形成明确术前结论。"
        conclusion_class = "text-orange-600"

        warning = (
            "模型提示当前证据不足，存在误判风险，建议补充影像资料后再进行综合判断。"
        )

        suggestions = [
            "补充缺失的影像序列或临床病史",
            "等待完整影像分析流程完成",
            "必要时进行 MDT 多学科讨论",
        ]

    return {
        "reasoning": [
            {
                "type": "summary",
                "title": "推理摘要",
                "content": (
                    "模型基于当前输入图像完成盆腔淋巴结转移与宫旁浸润两项任务评估。"
                    f"淋巴结转移风险分数为 {_percent(lymph_score)}%，"
                    f"宫旁浸润风险分数为 {_percent(para_score)}%。"
                ),
                "className": "text-blue-700",
            },
            {
                "type": "conclusion",
                "title": "评估结论",
                "content": conclusion,
                "className": conclusion_class,
            },
            {
                "type": "evidence",
                "title": "证据充分性检查",
                "items": evidence_items,
            },
            {
                "type": "warning",
                "title": "风险提示",
                "content": warning,
                "className": "text-red-600",
            },
            {
                "type": "suggestions",
                "title": "下一步建议",
                "items": suggestions,
            },
        ]
    }


def build_aireportdraft_from_result_raw(result_raw: dict) -> dict:
    """
    从 result_raw 生成 aireportdraft_zh.json。
    """
    raw = _unwrap_result_raw(result_raw)

    lymph = raw.get("lymph") or {}
    para = raw.get("parametrium") or {}

    lymph_score = lymph.get("avg_cls_score")
    para_score = para.get("avg_cls_score")

    lymph_risk = _risk_style_from_score(lymph_score)
    para_risk = _risk_style_from_score(para_score)

    lymph_text = lymph.get("recommendation_text") or _diagnosis_text(
        "盆腔淋巴结转移", lymph.get("diagnosis")
    )

    para_text = para.get("recommendation_text") or _diagnosis_text(
        "宫旁浸润", para.get("diagnosis")
    )

    if raw.get("evidence_status") == "sufficient":
        suggestion = (
            "当前模型提示影像证据较充分，可将上述 AI 结果作为术前辅助评估参考。"
            "最终诊疗决策仍需结合医生阅片、临床病史、实验室检查及 MDT 讨论综合判断。"
        )
    else:
        suggestion = (
            "当前模型提示证据不足，建议补充完整影像资料和临床病史后再次分析。"
            "在证据不足情况下，不建议仅凭 AI 结果形成确定性术前结论。"
        )

    return {
        "aireportdraft": [
            {
                "title": "盆腔淋巴结评估：",
                "content": (
                    f"AI 模型评估盆腔淋巴结转移风险分数为 {_percent(lymph_score)}%。"
                    f"{lymph_text}"
                ),
                "titleClassName": lymph_risk["titleClassName"],
            },
            {
                "title": "宫旁浸润评估：",
                "content": (
                    f"AI 模型评估宫旁浸润风险分数为 {_percent(para_score)}%。"
                    f"{para_text}"
                ),
                "titleClassName": para_risk["titleClassName"],
            },
            {
                "title": "最终建议：",
                "content": suggestion,
                "titleClassName": "text-blue-600",
            },
        ]
    }


def build_keyevidence_from_result_raw(
    result_raw: dict,
    patient_info: Optional[dict] = None,
) -> dict:
    """
    从 result_raw + info_zh.json 生成 keyevidence_zh.json。

    这里会根据当前病人的 MRI 序列显示：
      MRI T1 已提供 / MRI T2WI 缺失 / MRI DWI 缺失 等。
    """
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

    # MRI 序列证据项
    if "t1" in mri_sequences_norm:
        key_items.append({
            "title": "MRI T1 已提供",
            "color": "green",
            "status": "已提供",
            "highlight": True,
        })
    else:
        key_items.append({
            "title": "MRI T1 缺失",
            "color": "red",
            "status": "缺失",
            "missing": True,
        })

    if "t2" in mri_sequences_norm or "t2wi" in mri_sequences_norm:
        key_items.append({
            "title": "MRI T2WI 已提供",
            "color": "green",
            "status": "已提供",
            "highlight": True,
        })
    else:
        key_items.append({
            "title": "MRI T2WI 缺失",
            "color": "red",
            "status": "缺失",
            "missing": True,
        })

    if "dwi" in mri_sequences_norm:
        key_items.append({
            "title": "MRI DWI 已提供",
            "color": "green",
            "status": "已提供",
            "highlight": True,
        })
    else:
        key_items.append({
            "title": "MRI DWI 缺失",
            "color": "red",
            "status": "缺失",
            "missing": True,
        })

    # 模型结果证据项
    key_items.extend([
        {
            "title": (
                f"盆腔淋巴结转移：{_simple_diag_text(lymph_diag)}，"
                f"风险分数 {_percent(lymph_score)}%"
            ),
            "color": (
                "red"
                if lymph_diag == "positive"
                else "green"
                if lymph_diag == "negative"
                else "orange"
            ),
            "status": "可信" if lymph_trust else "证据不足",
            "highlight": lymph_trust,
            "missing": not lymph_trust,
        },
        {
            "title": (
                f"宫旁浸润：{_simple_diag_text(para_diag)}，"
                f"风险分数 {_percent(para_score)}%"
            ),
            "color": (
                "red"
                if para_diag == "positive"
                else "green"
                if para_diag == "negative"
                else "orange"
            ),
            "status": "可信" if para_trust else "证据不足",
            "highlight": para_trust,
            "missing": not para_trust,
        },
    ])

    return {"keyevidence": key_items}


def build_all_outputs_from_result_raw(
    result_raw: dict,
    patient_info: Optional[dict] = None,
) -> dict:
    """
    只构造四个模块，不保存文件。
    """
    return {
        "assessment": build_assessment_from_result_raw(result_raw),
        "reasoning": build_reasoning_from_result_raw(result_raw, patient_info),
        "aireportdraft": build_aireportdraft_from_result_raw(result_raw),
        "keyevidence": build_keyevidence_from_result_raw(result_raw, patient_info),
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
      static/patient/{id}/reasoning/reasoning_zh.json
      static/patient/{id}/aireportdraft/aireportdraft_zh.json
      static/patient/{id}/keyevidence/keyevidence_zh.json
    """
    lang = normalize_language(language)

    patient_info = read_patient_info_from_file(patient_id, lang)

    generated = build_all_outputs_from_result_raw(
        result_raw=result_raw,
        patient_info=patient_info,
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