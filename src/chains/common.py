from __future__ import annotations

from dataclasses import dataclass, field

from ..retrieval.retriever import RetrievedDoc

@dataclass
class ChainResult:
    content: str
    citations: list[dict] = field(default_factory=list)
    data: dict | None = None

def build_context(docs: list[RetrievedDoc]) -> tuple[str, list[dict]]:
    if not docs:
        return "（未检索到相关内容，请先上传资料入库）", []
    parts: list[str] = []
    citations: list[dict] = []
    for i, d in enumerate(docs, 1):
        parts.append(f"[{i}] 来源：{d.source_label()}｜类型：{d.doc_type}\n{d.text}")
        citations.append({
            "index": i,
            "source_file": d.source_file,
            "library": d.library,
            "doc_type": d.doc_type,
        })
    return "\n\n---\n\n".join(parts), citations
