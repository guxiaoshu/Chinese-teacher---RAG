"""把某类（默认「其他」）已入库文件删旧切片、清记录，用最新分类提示词重新入库。

用途：改了分类提示词后，把之前被误分类的文件重新跑一遍。

用法（在项目根目录）：
    python scripts/reclassify.py            # 重分类所有 doc_type == 其他 的文件
    python scripts/reclassify.py 文言笔记   # 只重分类 doc_type == 文言笔记 的文件
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.pipeline import process_file  # noqa: E402
from src.ingestion.state import list_files, get_sha, clear_record  # noqa: E402
from src.vectorstore.store import delete_by_source_hash  # noqa: E402


def main() -> None:
    target = sys.argv[1] if len(sys.argv) > 1 else "其他"
    files = [f for f in list_files() if f.get("doc_type") == target]
    print(f"找到 {len(files)} 个 doc_type == {target} 的文件，重新分类入库……\n")
    for f in files:
        p = Path(f["path"])
        if not p.exists():
            print(f"[跳过] {p.name}（文件不存在）")
            continue
        sha = get_sha(p)
        if sha:
            delete_by_source_hash(f["library"], sha)
        clear_record(p)
        r = process_file(p)
        if r.get("status") == "processed":
            print(f"[OK]  {p.name} -> {r.get('doc_type')} ({r.get('chunks')} chunks)")
        else:
            print(f"[失败] {p.name} -> {r.get('error', r.get('status'))}")
    print("\n完成。")


if __name__ == "__main__":
    main()
