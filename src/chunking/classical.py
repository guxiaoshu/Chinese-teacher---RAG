from __future__ import annotations

import re

from .base import Chunk, split_by_headings, _sub_split_long

_FUNCTION_CHARS = "之乎者也而其以于乃则焉为所与若因且何诸孰安耳矣乎哉遂复即既虽"
_PATTERNS = [
    r"^【[^】]{1,8}】",
    r"^\d+[.、．]\s*[" + _FUNCTION_CHARS + r"]",
    r"^[" + _FUNCTION_CHARS + r"][，,、：:\s]",
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
            for sub in _sub_split_long(body):
                sub = sub.strip()
                if not sub:
                    continue
                meta = {}
                if entry:
                    meta["词条"] = entry
                chunks.append(Chunk(text=sub, meta=meta))
        return chunks
