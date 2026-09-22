"""重新切片已入库文件（不重新分类，保留原标签），用于切片器逻辑更新后重跑受影响文件。

与 reclassify.py 的区别：这里**跳过 LLM 分类**，直接用库里的 doc_type/标签，
只重新执行「解析 → 切片 → 向量化 → 入库 → 重建索引」。

用法（在项目根目录）：
    python scripts/rechunk.py            # 重切所有已入库文件
    python scripts/rechunk.py 文言笔记   # 只重切 doc_type == 文言笔记
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.pipeline import build_meta, detect_library  # noqa: E402
from src.ingestion.loader import extract_text  # noqa: E402
from src.ingestion.state import list_files, get_sha, sha256_of, mark_processed, clear_record  # noqa: E402
from src.chunking import chunk_for  # noqa: E402
from src.llm.embeddings import embed_documents  # noqa: E402
from src.vectorstore.store import delete_by_source_hash, upsert_chunks  # noqa: E402
from src.retrieval.retriever import rebuild_index  # noqa: E402
from src.tagging.classifier import DocTags  # noqa: E402


def main() -> None:
    target = sys.argv[1] if len(sys.argv) > 1 else None
    files = list_files()
    if target:
        files = [f for f in files if f.get("doc_type") == target]
    print(f"重新切片 {len(files)} 个文件（保留原分类标签）……\n")
    for f in files:
        p = Path(f["path"])
        if not p.exists():
            print(f"[跳过] {p.name}（文件不存在）")
            continue
        try:
            tags = DocTags(**json.loads(f["tags"] or "{}"))
        except Exception:  # noqa: BLE001
            print(f"[跳过] {p.name}（标签解析失败）")
            continue
        library = f["library"] or detect_library(p)
        sha = get_sha(p) or sha256_of(p)
        try:
            delete_by_source_hash(library, sha)
            text = extract_text(p)
            chunks = chunk_for(tags.doc_type, text)
            ids, texts, metas = [], [], []
            for i, c in enumerate(chunks):
                if not c.text.strip():
                    continue
                ids.append(f"{sha}-{i}")
                texts.append(c.text)
                metas.append(build_meta(p, library, sha, tags, c.meta, i))
            embs = embed_documents(texts)
            upsert_chunks(library, ids, texts, embs, metas)
            rebuild_index(library)
            mark_processed(p, sha, library, len(texts), tags.doc_type, tags.to_metadata())
            print(f"[OK]  {p.name} -> {tags.doc_type} ({len(texts)} chunks)")
        except Exception as e:  # noqa: BLE001
            print(f"[失败] {p.name} -> {e}")
    print("\n完成。")


if __name__ == "__main__":
    main()
