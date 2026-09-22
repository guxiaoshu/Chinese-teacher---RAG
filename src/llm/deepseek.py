"""DeepSeek 客户端封装。

DeepSeek 走 OpenAI 兼容接口，用 langchain-openai 的 ChatOpenAI 接入。
提供三个层次的工具：
1. get_chat_llm / get_reason_llm —— 常规对话模型
2. json_chat —— JSON 模式对话（用于分类、切片边界、出题等结构化输出）
3. extract_json —— 鲁棒的 JSON 解析（容忍 markdown 围栏、前后噪声）
"""
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
    """JSON 模式的 chat 模型（DeepSeek 需在 prompt 里出现 'json' 字样 + response_format）。"""
    kwargs = _base_kwargs(temperature)
    kwargs["model_kwargs"] = {"response_format": {"type": "json_object"}}
    return ChatOpenAI(model=_CHAT_MODEL, **kwargs)


def extract_json(text: str) -> Any:
    """从模型输出中鲁棒地抽取第一个合法 JSON 对象/数组。"""
    if text is None:
        raise ValueError("空输出")
    # 去掉 markdown 围栏
    text = re.sub(r"```(?:json)?", "", text).strip()
    # 优先找最外层花括号或方括号
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
    # 兜底：整个文本直接 parse
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"无法解析 JSON: {e}\n原始输出片段: {text[:500]}")


def invoke_json(messages: list[dict], temperature: float = 0.0, retries: int = 3) -> Any:
    """调用 JSON 模式并解析，带重试。"""
    llm = get_json_llm(temperature=temperature)
    last_err: Exception | None = None
    for _ in range(retries):
        try:
            resp = llm.invoke(messages)
            return extract_json(resp.content)
        except Exception as e:  # noqa: BLE001
            last_err = e
    raise RuntimeError(f"JSON 结构化调用失败（重试 {retries} 次）: {last_err}")
