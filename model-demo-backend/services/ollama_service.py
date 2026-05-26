import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, List, Optional

import httpx

from core.config import OLLAMA_BASE_URL, OLLAMA_MODEL, PATIENT_ROOT
from schemas.llm_schema import ChatMessage
from services.file_service import normalize_language
from services.patient_service import read_patient_info


async def chat_with_ollama(
    message: str,
    system_prompt: Optional[str] = None,
    history: Optional[List[ChatMessage]] = None,
    model: Optional[str] = None,
) -> dict:
    """
    调用本地 Ollama 的 /api/chat 接口。
    """

    used_model = model or OLLAMA_MODEL

    messages = []

    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})

    if history:
        for item in history:
            messages.append({"role": item.role, "content": item.content})

    messages.append({"role": "user", "content": message})

    payload = {
        "model": used_model,
        "messages": messages,
        "stream": False,
        # format=json 对部分模型有效；无效时也不会影响 /api/chat 的正常调用。
        "format": "json",
        "options": {
            "temperature": 0.2,
        },
    }

    url = f"{OLLAMA_BASE_URL}/api/chat"

    try:
        async with httpx.AsyncClient(timeout=180.0, trust_env=False) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()

        answer = data.get("message", {}).get("content", "")

        return {"answer": answer, "model": used_model}

    except httpx.ConnectError:
        raise RuntimeError(
            "无法连接 Ollama，请确认 Ollama 已启动，并且地址为 http://localhost:11434"
        )

    except httpx.HTTPStatusError as e:
        raise RuntimeError(
            f"Ollama 请求失败，状态码：{e.response.status_code}，内容：{e.response.text}"
        )

    except Exception as e:
        raise RuntimeError(f"Ollama 调用异常：{str(e)}")


async def test_ollama_chat_and_save(
    save_dir: str = "static/llm_test",
    filename: str = "ollama_test_answer.json",
    model: Optional[str] = None,
) -> dict:
    """
    测试 Ollama 是否可以正常对话，并将结果保存为 JSON 文件。

    返回格式：
    {
        "testanswer": "模型回答内容"
    }
    """

    result = await chat_with_ollama(
        message="请随便介绍一下你自己，控制在100字以内。",
        system_prompt="你是一个本地运行的大语言模型助手，请使用中文回答。",
        model=model,
    )

    answer = result.get("answer", "")

    output_data = {"testanswer": answer}

    save_path = Path(save_dir)
    save_path.mkdir(parents=True, exist_ok=True)

    file_path = save_path / filename

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    return output_data


def _text(lang: str, zh: str, en: str) -> str:
    return en if lang == "en" else zh


def _localized_file(patient_id: str, folder: str, stem: str, lang: str) -> Path:
    return PATIENT_ROOT / patient_id / folder / f"{stem}_{lang}.json"


def _save_json(path: Path, data: Any) -> Any:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return data


def _strip_think(text: str) -> str:
    # qwen3 有时会输出 <think>...</think>，这里去掉思考段，避免影响 JSON 解析。
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL | re.IGNORECASE).strip()


def _parse_json_answer(answer: str) -> Any:
    """从模型回答中解析 JSON。支持模型额外包裹 ```json 或输出解释文字的情况。"""
    raw = _strip_think(answer)
    raw = raw.strip()

    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?", "", raw, flags=re.IGNORECASE).strip()
        raw = re.sub(r"```$", "", raw).strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    # 兜底：截取第一个数组或对象。
    candidates = []
    for left, right in [("[", "]"), ("{", "}")]:
        start = raw.find(left)
        end = raw.rfind(right)
        if start != -1 and end != -1 and end > start:
            candidates.append(raw[start : end + 1])

    for item in candidates:
        try:
            return json.loads(item)
        except json.JSONDecodeError:
            continue

    raise RuntimeError(f"Ollama 返回内容不是合法 JSON：{answer}")


def _ensure_dict_key(data: Any, key: str, name: str) -> dict:
    """
    统一要求 Ollama 返回 JSON 对象(dict)，例如：
      {"assessment": [...]}
      {{"reasoning": [...]}
      {{"aireportdraft": [...]}
      {"keyevidence": [...]}

    同时兼容旧版本/模型偶尔直接返回数组(list)的情况，会自动包成指定 key。
    """
    if isinstance(data, dict):
        if key in data:
            return data

        # 兼容常见别名，避免模型把字段名写成复数或通用 items。
        alias_map = {
            "assessment": ["assessments", "items", "data"],
            "reasoning": ["reasonings", "items", "data"],
            "aireportdraft": ["aiReportDraft", "reportDraft", "report", "items", "data"],
            "keyevidence": ["keyEvidence", "evidenceItems", "items", "data"],
        }
        for alias in alias_map.get(key, []):
            if alias in data:
                return {key: data[alias]}

        raise RuntimeError(
            f"{name} 结果必须是包含字段 {key} 的 JSON 对象，"
            f"当前对象字段：{list(data.keys())}"
        )

    if isinstance(data, list):
        return {key: data}

    raise RuntimeError(f"{name} 结果必须是 JSON 对象，当前类型：{type(data).__name__}")


def _patient_context(patient_id: str, lang: str) -> dict:
    info = read_patient_info(patient_id, lang)
    return {
        "patient_id": patient_id,
        "name": info.get("name"),
        "age": info.get("age"),
        "gender": info.get("gender") or info.get("sex"),
        "stage": info.get("stage"),
        "date": info.get("date"),
        "modalities": info.get("modalities", []),
        "mriSequences": info.get("mriSequences", []),
        "clinicalHistoryStatus": info.get("clinicalHistoryStatus"),
        "analysis": info.get("analysis", {}),
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


def _system_prompt(lang: str) -> str:
    if lang == "en":
        return (
            "You are a medical AI report assistant. Return ONLY valid JSON. "
            "Do not return markdown, comments, explanations, or extra text. "
            "This is a demo system; avoid definitive diagnosis. Use cautious clinical language."
        )
    return (
        "你是医学影像 AI 报告辅助助手。只允许返回合法 JSON，"
        "不要返回 Markdown、解释、注释或多余文本。"
        "这是演示系统，不要给出绝对诊断，要使用谨慎的术前评估表述。"
    )


async def _generate_json_with_ollama(
    prompt: str,
    name: str,
    lang: str,
    model: Optional[str] = None,
) -> Any:
    result = await chat_with_ollama(
        message=prompt,
        system_prompt=_system_prompt(lang),
        model=model,
    )
    return _parse_json_answer(result.get("answer", ""))


async def generate_assessment_with_ollama_and_save(
    patient_id: str,
    language: Optional[str] = "zh",
    model: Optional[str] = None,
) -> dict:
    """生成并保存评估模块数据：static/patient/{id}/assessment/assessment_{lang}.json"""
    lang = normalize_language(language)
    ctx = _patient_context(patient_id, lang)

    prompt = f"""
根据下面病人信息，生成前端“评估”模块 JSON 对象。
语言：{lang}
病人信息：{json.dumps(ctx, ensure_ascii=False)}

必须严格返回 JSON 对象，格式为 {{"assessment": [...]}}，其中 assessment 数组固定 2 项：
1. 盆腔淋巴结转移
2. 宫旁浸润

每项字段必须完整：
{{
  "title": "字符串",
  "riskText": "高风险/中等风险/低风险 或 High risk/Intermediate risk/Low risk",
  "riskColor": "red/orange/green/gray",
  "percent": 数字0到100,
  "strokeColor": "#ef4444/#f59e0b/#22c55e/#64748b",
  "railColor": "#fee2e2/#ffedd5/#dcfce7/#e2e8f0",
  "borderClassName": "border-red-200/border-orange-200/border-green-200/border-slate-200",
  "bgClassName": "bg-red-50/bg-orange-50/bg-green-50/bg-slate-50",
  "evidenceSufficiency": "较充分/一般/不足 或 Sufficient/Moderate/Insufficient",
  "evidenceClassName": "text-green-600/text-orange-500/text-red-500",
  "modelConsistency": "高/中等/低 或 High/Moderate/Low",
  "positiveSliceRatio": "例如 47 / 429",
  "keyFinding": "一句关键发现"
}}

要求：如果证据不足，不要编造确定性影像结果；可以使用默认/示例性质的术前评估语言。
""".strip()

    data = _ensure_dict_key(
        await _generate_json_with_ollama(prompt, "评估", lang, model),
        "assessment",
        "评估",
    )
    return _save_json(_localized_file(patient_id, "assessment", "assessment", lang), data)


async def generate_reasoning_with_ollama_and_save(
    patient_id: str,
    language: Optional[str] = "zh",
    model: Optional[str] = None,
) -> dict:
    """生成并保存证据状态/推理模块数据：static/patient/{id}/reasoning/reasoning_{lang}.json"""
    lang = normalize_language(language)
    ctx = _patient_context(patient_id, lang)

    prompt = f"""
根据下面病人信息，生成前端“证据状态/推理摘要”模块 JSON 对象。
语言：{lang}
病人信息：{json.dumps(ctx, ensure_ascii=False)}

必须严格返回 JSON 对象，格式为 {{"reasoning": [...]}}，其中 reasoning 数组建议包含 5 项，字段结构如下：
{{"reasoning": [
  {{"type":"summary","title":"推理摘要","content":"...","className":"text-blue-700"}},
  {{"type":"conclusion","title":"评估结论","content":"...","className":"text-red-600 或 text-orange-600 或 text-green-600"}},
  {{"type":"evidence","title":"证据充分性检查","items":[
    {{"name":"MRI","status":"已提供/缺失/等待分析","className":"text-green-600/text-red-500/text-orange-500"}},
    {{"name":"PET/CT","status":"已提供/缺失/等待分析","className":"text-green-600/text-red-500/text-orange-500"}},
    {{"name":"CT","status":"已提供/缺失/等待分析","className":"text-green-600/text-red-500/text-orange-500"}},
    {{"name":"临床病史","status":"已提供/部分缺失/缺失","className":"text-green-600/text-orange-500/text-red-500"}}
  ]}},
  {{"type":"warning","title":"风险提示","content":"...","className":"text-red-600"}},
  {{"type":"suggestions","title":"下一步建议","items":["...","..."]}}
]}}

要求：
- items 里 MRI、PET/CT、CT、临床病史都要出现。
- status 要依据 modalities 和 clinicalHistoryStatus 生成。
- 如果分析证据不足，请明确提示“不能形成明确术前结论”。
""".strip()

    data = _ensure_dict_key(
        await _generate_json_with_ollama(prompt, "推理", lang, model),
        "reasoning",
        "推理",
    )
    return _save_json(_localized_file(patient_id, "reasoning", "reasoning", lang), data)


async def generate_aireportdraft_with_ollama_and_save(
    patient_id: str,
    language: Optional[str] = "zh",
    model: Optional[str] = None,
) -> dict:
    """生成并保存 AI 报告草稿：static/patient/{id}/aireportdraft/aireportdraft_{lang}.json"""
    lang = normalize_language(language)
    ctx = _patient_context(patient_id, lang)

    prompt = f"""
根据下面病人信息，生成前端“AI 生成报告草稿”模块 JSON 对象。
语言：{lang}
病人信息：{json.dumps(ctx, ensure_ascii=False)}

必须严格返回 JSON 对象，格式为 {{"aireportdraft": [...]}}，其中 aireportdraft 数组固定 3 项：
{{"aireportdraft": [
  {{"title":"盆腔淋巴结评估：","content":"...","titleClassName":"text-red-500 或 text-orange-500 或 text-green-600"}},
  {{"title":"宫旁浸润评估：","content":"...","titleClassName":"text-red-500 或 text-orange-500 或 text-green-600"}},
  {{"title":"最终建议：","content":"...","titleClassName":"text-blue-600"}}
]}}

要求：
- content 写成可放进报告草稿的自然段。
- 证据不足时要建议补充检查/人工复核，不要写成确定诊断。
""".strip()

    data = _ensure_dict_key(
        await _generate_json_with_ollama(prompt, "AI 报告草稿", lang, model),
        "aireportdraft",
        "AI 报告草稿",
    )
    return _save_json(_localized_file(patient_id, "aireportdraft", "aireportdraft", lang), data)


async def generate_keyevidence_with_ollama_and_save(
    patient_id: str,
    language: Optional[str] = "zh",
    model: Optional[str] = None,
) -> dict:
    """生成并保存关键证据：static/patient/{id}/keyevidence/keyevidence_{lang}.json"""
    lang = normalize_language(language)
    ctx = _patient_context(patient_id, lang)

    prompt = f"""
根据下面病人信息，生成前端“关键证据”模块 JSON 对象。
语言：{lang}
病人信息：{json.dumps(ctx, ensure_ascii=False)}

必须严格返回 JSON 对象，格式为 {{"keyevidence": [...]}}，其中 keyevidence 数组建议 4 项左右。每项字段：
{{
  "title": "例如 MRI T2WI / MRI DWI / PET/CT 缺失 / CT 已提供",
  "color": "orange/blue/gray/green/red",
  "status": "已提供/缺失/部分缺失/等待分析 或 Provided/Missing/Partially missing/Pending",
  "highlight": true 或 false，可省略,
  "missing": true 或 false，可省略
}}

要求：
- 根据 modalities、mriSequences、clinicalHistoryStatus 生成。
- 缺失证据必须设置 missing:true。
- 至少包含一个 MRI 相关证据项。
""".strip()

    data = _ensure_dict_key(
        await _generate_json_with_ollama(prompt, "关键证据", lang, model),
        "keyevidence",
        "关键证据",
    )
    return _save_json(_localized_file(patient_id, "keyevidence", "keyevidence", lang), data)


async def generate_all_patient_outputs_with_ollama(
    patient_id: str,
    language: Optional[str] = "zh",
    model: Optional[str] = None,
) -> dict:
    """一次生成评估、证据状态/推理、AI 报告草稿、关键证据四个模块。"""
    lang = normalize_language(language)

    assessment = await generate_assessment_with_ollama_and_save(patient_id, lang, model)
    reasoning = await generate_reasoning_with_ollama_and_save(patient_id, lang, model)
    aireportdraft = await generate_aireportdraft_with_ollama_and_save(patient_id, lang, model)
    keyevidence = await generate_keyevidence_with_ollama_and_save(patient_id, lang, model)

    return {
        "assessment": assessment,
        "reasoning": reasoning,
        "aireportdraft": aireportdraft,
        "keyevidence": keyevidence,
    }
