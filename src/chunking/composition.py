"""作文材料切片：按主题、学生典型立意（偏题/平庸/深刻）拆分。

每个立意一个 chunk，meta 里记录主题与立意类型，便于「出题/作文辅导」时精准召回。
"""
from __future__ import annotations

import re

from .base import Chunk, split_by_headings, _sub_split_long

_PATTERNS = [
    r"^【[^】]{2,24}】",                          # 【主题】/【立意】
    r"^(主题|话题|题目|材料)[：:]\s*\S",          # 主题：xxx
    r"^(偏题|平庸|深刻|跑题|立意)[：:]\s*\S",      # 立意：xxx
    r"^[一二三四五六七八九十]+、",                # 一、
    r"^\d+[.、．]\s*\S",                          # 1.
]

_LEVELS = {"偏题": "偏题", "跑题": "偏题", "平庸": "平庸", "深刻": "深刻"}


class CompositionChunker:
    doc_type = "作文材料"

    def split(self, text: str) -> list[Chunk]:
        segments = split_by_headings(text, _PATTERNS)
        chunks: list[Chunk] = []
        for heading, body in segments:
            theme, level = _parse_heading(heading)
            for sub in _sub_split_long(body):
                if not sub.strip():
                    continue
                meta = {}
                if heading:
                    meta["标题"] = heading
                if theme:
                    meta["主题"] = theme
                if level:
                    meta["立意"] = level
                chunks.append(Chunk(text=sub, meta=meta))
        return chunks


def _parse_heading(heading: str) -> tuple[str, str]:
    theme, level = "", ""
    h = heading.strip("【】")
    for kw, lv in _LEVELS.items():
        if kw in h:
            level = lv
            break
    m = re.search(r"(?:主题|话题|题目)[：:]\s*(.+)", h)
    if m:
        theme = m.group(1).strip()
    else:
        theme = h
    return theme, level
