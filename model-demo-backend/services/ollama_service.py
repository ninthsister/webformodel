import httpx
from typing import List, Optional

from core.config import OLLAMA_BASE_URL, OLLAMA_MODEL
from schemas.llm_schema import ChatMessage

import json
from pathlib import Path
from datetime import datetime

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
        messages.append({
            "role": "system",
            "content": system_prompt,
        })

    if history:
        for item in history:
            messages.append({
                "role": item.role,
                "content": item.content,
            })

    messages.append({
        "role": "user",
        "content": message,
    })

    payload = {
        "model": used_model,
        "messages": messages,
        "stream": False,
    }

    url = f"{OLLAMA_BASE_URL}/api/chat"

    try:
        async with httpx.AsyncClient(timeout=120.0, trust_env=False) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()

        answer = data.get("message", {}).get("content", "")

        return {
            "answer": answer,
            "model": used_model,
        }

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

    output_data = {
        "testanswer": answer,
    }

    save_path = Path(save_dir)
    save_path.mkdir(parents=True, exist_ok=True)

    file_path = save_path / filename

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    return output_data