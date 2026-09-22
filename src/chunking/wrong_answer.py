from __future__ import annotations

import re

from .base import Chunk, split_by_headings

_HEADING_PATTERNS = [
    r"^第?[一二三四五六七八九十百\d]+题",
    r"^\s*\d+[.、．)]\s*\S",
    r"^\s*（\d+）",
    r"^\s*\(\d+\)",
]

_ANSWER_MARKERS = [
    "学生答", "学生答案", "学生作答", "学生回答", "学生的答案",
    "错答", "错误答案", "学生写", "学生写成", "学生误",
]
_ANNOT_MARKERS = [
    "教师批注", "批注", "教师点评", "点评", "评语",
    "错因", "错误原因", "错误分析", "订正", "教师",
]

class WrongAnswerChunker:
    doc_type = "学生错题"

    def split(self, text: str) -> list[Chunk]:
        segments = split_by_headings(text, _HEADING_PATTERNS)
        chunks: list[Chunk] = []
        for heading, body in segments:
            body = body.strip()
            if not body and not heading:
                continue
            full = body if heading in body or not heading else (heading + "\n" + body)
            meta = {"题号": heading} if heading else {}
            question, answer, annot = _structure(full)
            if question:
                meta["题干"] = question
            if answer:
                meta["学生答案"] = answer
            if annot:
                meta["批注"] = annot
            if not full.strip():
                continue
            chunks.append(Chunk(text=full.strip(), meta=meta))
        return chunks

def _structure(full: str) -> tuple[str, str, str]:
    question, answer, annot = "", "", ""
    lines = full.split("\n")
    cur = "question"
    buf = {"question": [], "answer": [], "annot": []}
    for line in lines:
        s = line.strip()
        if any(s.startswith(m) for m in _ANNOT_MARKERS):
            cur = "annot"
        elif any(s.startswith(m) for m in _ANSWER_MARKERS):
            cur = "answer"
        buf[cur].append(s)

    question = _trim_marker("\n".join(buf["question"]))
    answer = _trim_marker("\n".join(buf["answer"]))
    annot = _trim_marker("\n".join(buf["annot"]))
    return question, answer, annot

def _trim_marker(s: str) -> str:
    for m in _ANSWER_MARKERS + _ANNOT_MARKERS:
        if s.startswith(m):
            s = s[len(m):].lstrip("：:，, ")
    return s.strip()
