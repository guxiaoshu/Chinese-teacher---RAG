"""文言笔记切片：以单个实词 / 虚词、特殊句式切片。

边界识别依据：
- 【之】【而】等词条括号
- 1. 之 / 之： 等词条起头
- 特殊句式（判断句/被动句/倒装句/省略句等）
"""
from __future__ import annotations

import re

from .base import Chunk, split_by_headings, _sub_split_long

# 常见文言实虚词（用于识别"单个词条"起头）
_FUNCTION_CHARS = "之乎者也而其以于乃则焉为所与若因且何诸孰安耳矣乎哉遂复即既虽"
_PATTERNS = [
    r"^【[^】]{1,8}】",                          # 【之】
    r"^\d+[.、．]\s*[" + _FUNCTION_CHARS + r"]",  # 1. 之
    r"^[" + _FUNCTION_CHARS + r"][，,、：:\s]",   # 之：
    r"^(判断句|被动句|倒装句|宾语前置|状语后置|定语后置|省略句|固定句式|主谓倒置)[：:，,]",
]


class ClassicalChunker:
    doc_type = "文言笔记"

    def split(self, text: str) -> list[Chunk]:
        segments = split_by_headings(text, _PATTERNS)
        chunks: list[Chunk] = []
        for heading, body in segments:
            body = body.strip()
            if not body and not heading:
                continue
            entry = re.sub(r"[【】\s]", "", heading)[:16] if heading else ""
            # 过长正文二次细分，避免单块超过 embedding 的 512 token 上限被截断
            for sub in _sub_split_long(body):
                sub = sub.strip()
                if not sub:
                    continue
                meta = {}
                if entry:
                    meta["词条"] = entry
                chunks.append(Chunk(text=sub, meta=meta))
        return chunks
