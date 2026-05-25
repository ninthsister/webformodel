import json
from pathlib import Path
from typing import Optional

from fastapi import HTTPException, Request


SUPPORTED_LANGUAGES = {"zh", "en"}
DEFAULT_LANGUAGE = "zh"


def normalize_language(language: Optional[str] = None) -> str:
    """Normalize frontend language value to zh/en.

    Supports values such as zh, zh-CN, en, en-US.
    Unknown values fall back to zh.
    """
    if not language:
        return DEFAULT_LANGUAGE

    value = language.strip().lower().replace("_", "-")

    if value.startswith("en"):
        return "en"
    if value.startswith("zh"):
        return "zh"

    return DEFAULT_LANGUAGE


def get_request_language(
    request: Optional[Request] = None,
    language: Optional[str] = None,
) -> str:
    """Get language from query/body value first, then headers.

    Frontend currently sends language in query/body and also sends
    X-Language / Accept-Language headers.
    """
    if language:
        return normalize_language(language)

    if request is not None:
        header_language = (
            request.headers.get("X-Language")
            or request.headers.get("Accept-Language")
        )
        return normalize_language(header_language)

    return DEFAULT_LANGUAGE


def get_localized_json_path(path: Path, language: Optional[str] = None) -> Path:
    """Resolve a JSON path according to the strict suffix rule.

    Rule:
      source file name + _{language}.json

    Examples:
      info.json           -> info_zh.json / info_en.json
      assessment.json     -> assessment_zh.json / assessment_en.json
      reasoning.json      -> reasoning_zh.json / reasoning_en.json
      aireportdraft.json  -> aireportdraft_zh.json / aireportdraft_en.json

    The original path is only used to provide the base name; it is not used as
    a fallback. This makes the requested language explicit and predictable.
    """
    lang = normalize_language(language)
    return path.with_name(f"{path.stem}_{lang}{path.suffix}")


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


def read_localized_json_file(
    path: Path,
    error_name: str,
    language: Optional[str] = None,
):
    lang = normalize_language(language)
    localized_path = get_localized_json_path(path, lang)

    if not localized_path.exists():
        raise HTTPException(
            status_code=404,
            detail=(
                f"未找到{error_name}{lang}语言文件: {localized_path}。"
                f"请按 源文件名_{lang}.json 命名，例如 {path.stem}_{lang}{path.suffix}"
            ),
        )

    return read_json_file(localized_path, error_name)


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
