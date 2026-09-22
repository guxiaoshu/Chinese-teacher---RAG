from __future__ import annotations

import re

from .base import Chunk, split_by_headings, _sub_split_long

_HEADING_PATTERNS = [
    r"^第[一二三四五六七八九十百\d]+课时",
    r"^[一二三四五六七八九十]+、",
    r"^[一二三四五六七八九十]+[.．]\s*\S",
    r"^\d+、",
    r"^\d+[.．]\s*\S",
    r"^（[一二三四五六七八九十\d]+）",
    r"^\([一二三四五六七八九十\d]+\)",
    r"^【[^】]+】",
]

_STAGE_KEYWORDS = {
    "导入": "导入",
    "重难点": "重难点",
    "重点": "重难点",
    "难点": "重难点",
    "教学目标": "教学目标",
    "课堂提问": "课堂提问",
    "提问": "课堂提问",
    "问题": "课堂提问",
    "拓展": "拓展",
    "延伸": "拓展",
    "板书": "板书",
    "作业": "作业",
    "小结": "小结",
    "课堂总结": "小结",
}

class LessonPlanChunker:
    doc_type = "教案"

    def split(self, text: str) -> list[Chunk]:
        segments = split_by_headings(text, _HEADING_PATTERNS)
        chunks: list[Chunk] = []
        for heading, body in segments:
            stage = _detect_stage(heading, body)
            for sub in _sub_split_long(body):
                if not sub.strip():
                    continue
                meta = {}
                if heading:
                    meta["标题"] = heading
                if stage:
                    meta["环节"] = stage
                chunks.append(Chunk(text=sub, meta=meta))
        return chunks

def _detect_stage(heading: str, body: str) -> str:
    probe = (heading + " " + body[:80])
    for kw, stage in _STAGE_KEYWORDS.items():
        if kw in probe:
            return stage
    if "课时" in heading:
        return "课时"
    return ""
