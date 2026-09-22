from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.pipeline import build_meta, detect_library
from src.ingestion.loader import extract_text
from src.ingestion.state import list_files, get_sha, sha256_of, mark_processed, clear_record
from src.chunking import chunk_for
from src.llm.embeddings import embed_documents
from src.vectorstore.store import delete_by_source_hash, upsert_chunks
from src.retrieval.retriever import rebuild_index
from src.tagging.classifier import DocTags

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
        except Exception:
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
        except Exception as e:
            print(f"[失败] {p.name} -> {e}")
    print("\n完成。")

if __name__ == "__main__":
    main()
