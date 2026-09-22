"""向量库：ChromaDB 持久化，双 collection 隔离公共库与私有库。

- public  -> collection "public_base"
- private -> collection "private_kb"

元数据规则：Chroma 只接受 str/int/float/bool，列表/字典会先 JSON 序列化。
每个 chunk 的 id = "{source_hash}-{chunk_index}"，按 source_hash 可整文件删除（重新入库用）。
"""
from __future__ import annotations

import json

from ..config import CHROMA_DIR

LIBRARY_COLLECTION = {"public": "public_base", "private": "private_kb"}

_client = None
_collections: dict[str, object] = {}


def get_client():
    global _client
    if _client is None:
        import chromadb

        _client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    return _client


def get_collection(library: str):
    if library not in LIBRARY_COLLECTION:
        raise ValueError(f"未知库类型: {library}")
    if library not in _collections:
        _collections[library] = get_client().get_or_create_collection(
            LIBRARY_COLLECTION[library], metadata={"hnsw:space": "cosine"}
        )
    return _collections[library]


def _flatten_meta(meta: dict) -> dict:
    out: dict = {}
    for k, v in meta.items():
        if v is None:
            out[k] = ""
        elif isinstance(v, (list, dict)):
            out[k] = json.dumps(v, ensure_ascii=False)
        elif isinstance(v, bool):
            out[k] = v
        elif isinstance(v, (int, float)):
            out[k] = v
        else:
            out[k] = str(v)
    return out


def upsert_chunks(library: str, ids: list[str], texts: list[str],
                  embeddings: list[list[float]], metas: list[dict]) -> None:
    col = get_collection(library)
    col.upsert(
        ids=ids,
        documents=texts,
        embeddings=embeddings,
        metadatas=[_flatten_meta(m) for m in metas],
    )


def delete_by_source_hash(library: str, source_hash: str) -> None:
    """删除某个文件来源的全部 chunk（重新入库前调用）。"""
    col = get_collection(library)
    col.delete(where={"source_hash": source_hash})


def get_all_documents(library: str) -> dict:
    """取库内全部文档（不取 embeddings，供 BM25 索引构建）。"""
    col = get_collection(library)
    return col.get(include=["documents", "metadatas"])


def count_documents(library: str | None = None) -> dict[str, int]:
    libs = [library] if library else list(LIBRARY_COLLECTION.keys())
    return {lib: get_collection(lib).count() for lib in libs}
