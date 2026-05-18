import json
from pathlib import Path
from fastapi import HTTPException


def read_json_file(path: Path, error_name: str):
    if not path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"未找到{error_name}文件: {path}",
        )

    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=500,
            detail=f"{error_name}文件 JSON 格式错误: {path}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"读取{error_name}文件失败: {str(e)}",
        )


def write_json_file(path: Path, data: dict, error_name: str):
    path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"保存{error_name}失败: {str(e)}",
        )