import requests
from core.config import OLLAMA_BASE_URL,OLLAMA_MODEL


def test_ollama_connection():
    # 1. 测试 Ollama 服务是否启动
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        response.raise_for_status()
    except Exception as e:
        print("❌ 无法连接 Ollama 服务")
        print("请确认已经启动 Ollama：")
        print("  ollama serve")
        print("错误信息：", e)
        return

    print("✅ Ollama 服务连接成功")

    # 2. 查看本地已有模型
    data = response.json()
    models = data.get("models", [])

    if not models:
        print("⚠️ 当前没有下载任何模型")
        print(f"请先执行：ollama pull {OLLAMA_MODEL}")
        return

    print("当前已下载模型：")
    for m in models:
        print(" -", m.get("name"))

    # 3. 测试模型是否能正常回答
    payload = {
        "model": OLLAMA_MODEL,
        "messages": [
            {
                "role": "user",
                "content": "我现在只是测试输入，如果成功就返回，成功连接到ollama。"
            }
        ],
        "stream": False
    }

    try:
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/chat",
            json=payload,
            timeout=120
        )
        response.raise_for_status()
    except Exception as e:
        print(f"❌ 模型 {OLLAMA_MODEL} 调用失败")
        print(f"如果没有这个模型，请先执行：ollama pull {OLLAMA_MODEL}")
        print("错误信息：", e)
        return

    result = response.json()
    answer = result.get("message", {}).get("content", "")

    print("\n✅ 模型调用成功")
    print("模型回答：")
    print(answer)


if __name__ == "__main__":
    test_ollama_connection()