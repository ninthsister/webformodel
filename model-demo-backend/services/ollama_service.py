import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, List, Optional

import httpx
import base64
from core.config import OLLAMA_BASE_URL, OLLAMA_MODEL, PATIENT_ROOT, MODEL_API_URL
from schemas.llm_schema import ChatMessage
from services.file_service import normalize_language
from services.patient_service import read_patient_info
from services.result_raw_processor import save_patient_outputs_from_result_raw

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


async def generate_all_patient_outputs_with_ollama_test(
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
MODEL_TIMEOUT = 180.0


def _infer_modal_from_path(image_path: Path) -> str:
    """
    根据图片路径自动判断 modal。

    例子：
    static/patient/11111/img/ct/slice_004.png        -> ct
    static/patient/11111/img/pet/slice_004.png       -> pet
    static/patient/11111/img/mri/t2/slice_004.png    -> t2
    static/patient/11111/img/mri/t1/slice_004.png    -> t1
    static/patient/11111/img/mri/t1ce/slice_004.png  -> t1ce
    """
    s = str(image_path).replace("\\", "/").lower()
    parts = [p for p in s.split("/") if p]

    # 注意顺序：t1ce 必须放在 t1 前面
    if "t1ce" in parts:
        return "t1ce"

    if "t1" in parts:
        return "t1"

    if "t2" in parts:
        return "t2"

    if "petct" in parts or "pet-ct" in parts or "pet_ct" in parts:
        return "petct"

    if "ct" in parts:
        return "ct"

    if "pet" in parts:
        return "pet"

    # 如果只有 mri，没有具体序列，默认按 t2 处理
    if "mri" in parts or "mr" in parts:
        return "t2"

    # 兜底
    return "t2"


def _find_patient_all_images(patient_id: str) -> list[Path]:
    """
    从当前病人目录下寻找全部可用图片。

    支持目录：
      static/patient/{patient_id}/img
      static/patient/{patient_id}/images

    支持后缀：
      png / jpg / jpeg / webp
    """
    patient_dir = PATIENT_ROOT / patient_id

    candidate_roots = [
        patient_dir / "img",
    ]

    valid_suffixes = {".png", ".jpg", ".jpeg", ".webp"}

    image_paths: list[Path] = []

    for root in candidate_roots:
        if not root.exists():
            continue

        for path in root.rglob("*"):
            if not path.is_file():
                continue

            if path.suffix.lower() in valid_suffixes:
                image_paths.append(path)

    # 去重 + 排序，保证每次顺序稳定
    image_paths = sorted(set(image_paths), key=lambda p: str(p))

    if not image_paths:
        raise RuntimeError(
            f"未找到病人 {patient_id} 的可用图像文件。"
            f"请检查 {patient_dir}/img 或 {patient_dir}/images 下是否存在 png/jpg/jpeg/webp。"
        )

    return image_paths


def _build_slices_from_patient_images(patient_id: str) -> tuple[list[dict], list[dict]]:
    """
    将当前病人的全部图片转成模型服务需要的 slices。

    返回：
      slices: 给模型 /decide 用
      source_images: 保存到 result_raw，方便前端或调试查看
    """
    image_paths = _find_patient_all_images(patient_id)

    slices = []
    source_images = []

    for image_path in image_paths:
        image_bytes = image_path.read_bytes()
        image_b64 = base64.b64encode(image_bytes).decode("utf-8")
        modal = _infer_modal_from_path(image_path)

        slices.append({
            "modal": modal,
            "image_b64": image_b64,
        })

        source_images.append({
            "path": str(image_path),
            "filename": image_path.name,
            "modal": modal,
        })

    return slices, source_images


async def _decide_with_model_api(
    slices: list[dict],
    task: str,
    patient_id: str,
    stage: str = "mr",
) -> dict:
    """
    调用外部模型服务 /decide。

    现在支持一次传入多张图片：
      slices = [
        {"modal": "ct", "image_b64": "..."},
        {"modal": "t2", "image_b64": "..."},
        ...
      ]
    """
    payload = {
        "patient_id": patient_id,
        "task": task,
        "stage": stage,
        "slices": slices,
        "use_qwen": True,
    }

    url = f"{MODEL_API_URL}/decide"

    try:
        async with httpx.AsyncClient(timeout=MODEL_TIMEOUT, trust_env=False) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            return response.json()

    except httpx.ConnectError:
        raise RuntimeError(f"无法连接模型服务：{url}，请确认模型服务已启动。")

    except httpx.HTTPStatusError as e:
        raise RuntimeError(
            f"模型服务请求失败，状态码：{e.response.status_code}，内容：{e.response.text}"
        )

    except Exception as e:
        raise RuntimeError(f"模型服务调用异常：{str(e)}")


async def generate_result_raw_with_model_and_save(
    patient_id: str,
    language: Optional[str] = "zh",
    model: Optional[str] = None,
) -> dict:
    """
    调用外部模型服务，生成并保存 result_raw。

    现在会读取当前病人目录下全部图片，而不是只读取第一张。

    保存路径：
      static/patient/{id}/result_raw/result_raw_{lang}.json

    返回格式：
    {
      "result_raw": {
        "patient_id": "...",
        "num_images": 10,
        "source_images": [...],
        "evidence_status": "sufficient/insufficient/error",
        "lymph": 原始 lymph 返回,
        "parametrium": 原始 parametrium 返回,
        "generated_at": "..."
      }
    }
    """
    lang = normalize_language(language)

    try:
        slices, source_images = _build_slices_from_patient_images(patient_id)

        lymph = await _decide_with_model_api(
            slices=slices,
            task="lymph",
            patient_id=patient_id,
            stage="mr",
        )

        para = await _decide_with_model_api(
            slices=slices,
            task="parametrium",
            patient_id=patient_id,
            stage="mr",
        )

        evidence_status = (
            "sufficient"
            if lymph.get("trust") and para.get("trust")
            else "insufficient"
        )

        data = {
            "result_raw": {
                "patient_id": patient_id,
                "num_images": len(source_images),
                "source_images": source_images,
                "evidence_status": evidence_status,
                "lymph": lymph,
                "parametrium": para,
                "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
        }

    except Exception as e:
        data = {
            "result_raw": {
                "patient_id": patient_id,
                "num_images": 0,
                "source_images": [],
                "evidence_status": "error",
                "error": str(e),
                "lymph": None,
                "parametrium": None,
                "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
        }

    return _save_json(
        _localized_file(patient_id, "result_raw", "result_raw", lang),
        data,
    )
async def generate_all_patient_outputs_with_ollama(
    patient_id: str,
    language: Optional[str] = "zh",
    model: Optional[str] = None,
) -> dict:
    """
    一次生成中英文两套结果。

    会生成：

      result_raw/result_raw_zh.json
      result_raw/result_raw_en.json

      assessment/assessment_zh.json
      assessment/assessment_en.json

      reasoning/reasoning_zh.json
      reasoning/reasoning_en.json

      aireportdraft/aireportdraft_zh.json
      aireportdraft/aireportdraft_en.json

      keyevidence/keyevidence_zh.json
      keyevidence/keyevidence_en.json

    注意：
      模型服务只调用一次。
      英文 result_raw 直接复制中文 result_raw。
      前端四个模块由 result_raw_processor 根据 zh/en 分别生成。
    """
    lang = normalize_language(language)

    # 1. 模型只调用一次，先生成中文 result_raw
    result_raw_zh = await generate_result_raw_with_model_and_save(
        patient_id=patient_id,
        language="zh",
        model=model,
    )

    # 2. result_raw 是原始模型结果，不需要重复调用模型，直接保存一份 en
    result_raw_en = _save_json(
        _localized_file(patient_id, "result_raw", "result_raw", "en"),
        result_raw_zh,
    )

    # 3. 根据同一个 result_raw 生成中文前端模块
    generated_zh = save_patient_outputs_from_result_raw(
        patient_id=patient_id,
        result_raw=result_raw_zh,
        language="zh",
    )

    # 4. 根据同一个 result_raw 生成英文前端模块
    generated_en = save_patient_outputs_from_result_raw(
        patient_id=patient_id,
        result_raw=result_raw_en,
        language="en",
    )

    current_result_raw = result_raw_en if lang == "en" else result_raw_zh
    current_generated = generated_en if lang == "en" else generated_zh

    return {
        "result_raw": current_result_raw,
        **current_generated,
        "all_languages": {
            "zh": {
                "result_raw": result_raw_zh,
                **generated_zh,
            },
            "en": {
                "result_raw": result_raw_en,
                **generated_en,
            },
        },
    }