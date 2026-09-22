"""切片基础设施：Chunk 数据结构 + 标题切分 / 兜底语义切片工具。"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from langchain_text_splitters import RecursiveCharacterTextSplitter

from ..config import CONFIG


@dataclass
class Chunk:
    """最小切片单元。

    text: 切片正文
    meta: 结构信息（如环节/题号/题干/学生答案/批注/词条等），后续与标签、来源合并成完整元数据。
    """
    text: str
    meta: dict = field(default_factory=dict)


def fallback_split(text: str) -> list[str]:
    """兜底语义切片（按句子边界，控制块大小与重叠）。"""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CONFIG["chunking"]["max_chunk_chars"],
        chunk_overlap=CONFIG["chunking"]["overlap_chars"],
        separators=["\n\n", "\n", "。", "！", "？", "；", "，", " ", ""],
    )
    return [t for t in splitter.split_text(text) if t.strip()]


def split_by_headings(text: str, patterns: list[str]) -> list[tuple[str, str]]:
    """按「标题行」切分成若干 (标题, 正文) 段。

    标题行 = 整行（strip 后）能匹配任意 pattern。
    无标题时返回 [("", 全文)]。
    """
    lines = text.split("\n")
    compiled = [re.compile(p) for p in patterns]

    heading_idx: list[int] = []
    for i, line in enumerate(lines):
        s = line.strip()
        if s and any(c.match(s) for c in compiled):
            heading_idx.append(i)

    if not heading_idx:
        return [("", text.strip())]

    segments: list[tuple[str, str]] = []
    for j, idx in enumerate(heading_idx):
        start = idx
        end = heading_idx[j + 1] if j + 1 < len(heading_idx) else len(lines)
        heading = lines[idx].strip()
        body = "\n".join(lines[start:end]).strip()
        segments.append((heading, body))
    return segments


def _sub_split_long(body: str, max_chars: int | None = None) -> list[str]:
    """正文过长时用兜底语义切片细分，避免单块过长。"""
    limit = max_chars or CONFIG["chunking"]["max_chunk_chars"]
    if len(body) <= limit:
        return [body]
    return fallback_split(body)
