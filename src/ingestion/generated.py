"""生成结果自动回库：把四大场景的产出沉淀进私有知识库，形成闭环。

场景 → 文档类型映射：
  写教案 → 教案；出题 → 习题；答疑 → 课堂笔记；学情分析 → 课堂笔记

每次生成后：
1) 直接切片 + 向量化，入私有库（带 generated=True 标记，可溯源、可与原始资料区分）；
2) 同时存档一份 Markdown 到 data/generated/ 供老师随时查阅。

是否自动回库由 config.yaml 的 `ingestion.auto_save_generated` 控制（默认开）。
"""
from __future__ import annotations

import hashlib
import re
from datetime import datetime

from ..config import CONFIG, DATA_DIR
from ..tagging.classifier import DocTags
from ..chunking import chunk_for
from ..llm.embeddings import embed_documents
from ..vectorstore.store import upsert_chunks
from ..retrieval.retriever import rebuild_index

_SCENARIO_TO_TYPE = {
    "写教案": "教案",
    "出题": "习题",
    "答疑": "课堂笔记",
    "学情分析": "课堂笔记",
}

# 生成内容的权威等级：低于教师手写批注（5），高于学生作答（2）
_AUTHORITY = {
    "教案": "教师教案",
    "课堂笔记": "教师教案",
    "习题": "其他",
}

_GENERATED_DIR = DATA_DIR / "generated"


def _extract_article(query: str) -> str:
    """从需求里简单提取《篇目名》作为 article 标签（不额外调 LLM）。"""
    m = re.search(r"《([^》]{1,30})》", query)
    return m.group(1).strip() if m else ""


def save_generated(scenario: str, query: str, content: str) -> bool:
    """把生成结果沉淀回私有库。失败不抛异常（绝不影响主流程），返回是否成功。"""
    if not CONFIG.get("ingestion", {}).get("auto_save_generated", True):
        return False
    content = (content or "").strip()
    if not content:
        return False
    try:
        doc_type = _SCENARIO_TO_TYPE.get(scenario, "其他")
        tags = DocTags(
            doc_type=doc_type,
            article=_extract_article(query),
            summary=content.split("\n")[0][:100],
        )
        chunks = chunk_for(doc_type, content)
        if not chunks:
            return False

        sha = hashlib.sha256(content.encode("utf-8")).hexdigest()
        ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        source_name = f"生成-{scenario}-{ts}.md"

        ids, texts, metas = [], [], []
        for i, c in enumerate(chunks):
            if not c.text.strip():
                continue
            ids.append(f"gen-{sha[:16]}-{i}")
            texts.append(c.text)
            meta = {
                "source_file": source_name,
                "source_path": str(_GENERATED_DIR / source_name),
                "source_hash": sha,
                "library": "private",
                "doc_type": doc_type,
                "grade": tags.grade,
                "unit": tags.unit,
                "article": tags.article,
                "knowledge_points": tags.knowledge_points,
                "learning_tags": tags.learning_tags,
                "situation_note": tags.situation_note,
                "summary": tags.summary,
                "authority": _AUTHORITY.get(doc_type, "其他"),
                "generated": True,
                "scenario": scenario,
                "chunk_index": i,
            }
            meta.update(c.meta)
            metas.append(meta)

        embs = embed_documents(texts)
        upsert_chunks("private", ids, texts, embs, metas)
        rebuild_index("private")

        # 存档一份 Markdown 供查阅（不进 ingest/，避免被文件监听重复处理）
        _GENERATED_DIR.mkdir(parents=True, exist_ok=True)
        header = (
            f"# {scenario}（自动沉淀）\n\n"
            f"> 需求：{query}\n"
            f"> 时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        )
        (_GENERATED_DIR / source_name).write_text(header + content, encoding="utf-8")
        return True
    except Exception:  # noqa: BLE001
        return False
