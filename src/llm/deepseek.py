from __future__ import annotations

import json
import re
from typing import Any

from langchain_openai import ChatOpenAI

from ..config import CONFIG, DEEPSEEK_API_KEY

_BASE_URL = CONFIG["llm"]["base_url"]
_CHAT_MODEL = CONFIG["llm"]["chat_model"]
_REASON_MODEL = CONFIG["llm"]["reason_model"]
_TEMPERATURE = CONFIG["llm"]["temperature"]
_MAX_RETRIES = CONFIG["llm"]["max_retries"]

def _base_kwargs(temperature: float | None = None) -> dict[str, Any]:
    return dict(
        base_url=_BASE_URL,
        api_key=DEEPSEEK_API_KEY,
        temperature=_TEMPERATURE if temperature is None else temperature,
        max_retries=_MAX_RETRIES,
        timeout=120,
    )

def get_chat_llm(temperature: float | None = None, streaming: bool = False) -> ChatOpenAI:
    return ChatOpenAI(model=_CHAT_MODEL, streaming=streaming, **_base_kwargs(temperature))

def get_reason_llm(temperature: float | None = None, streaming: bool = False) -> ChatOpenAI:
    return ChatOpenAI(model=_REASON_MODEL, streaming=streaming, **_base_kwargs(temperature))

def get_json_llm(temperature: float = 0.0) -> ChatOpenAI:
    kwargs = _base_kwargs(temperature)
    kwargs["model_kwargs"] = {"response_format": {"type": "json_object"}}
    return ChatOpenAI(model=_CHAT_MODEL, **kwargs)

def extract_json(text: str) -> Any:
    if text is None:
        raise ValueError("空输出")
    text = re.sub(r"```(?:json)?", "", text).strip()
    for open_c, close_c in (("{", "}"), ("[", "]")):
        start = text.find(open_c)
        if start == -1:
            continue
        depth = 0
        for i in range(start, len(text)):
            if text[i] == open_c:
                depth += 1
            elif text[i] == close_c:
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(text[start : i + 1])
                    except json.JSONDecodeError:
                        break
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"无法解析 JSON: {e}\n原始输出片段: {text[:500]}")

def invoke_json(messages: list[dict], temperature: float = 0.0, retries: int = 3) -> Any:
    llm = get_json_llm(temperature=temperature)
    last_err: Exception | None = None
    for _ in range(retries):
        try:
            resp = llm.invoke(messages)
            return extract_json(resp.content)
        except Exception as e:
            last_err = e
    raise RuntimeError(f"JSON 结构化调用失败（重试 {retries} 次）: {last_err}")
