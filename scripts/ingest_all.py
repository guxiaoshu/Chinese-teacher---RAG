from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import PRIVATE_DIR, PUBLIC_DIR
from src.pipeline import process_file
from src.ingestion.state import count_by_library

def _all_files() -> list[Path]:
    files: list[Path] = []
    for base in (PUBLIC_DIR, PRIVATE_DIR):
        for p in sorted(base.rglob("*")):
            if p.is_file() and p.suffix.lower() in (".pdf", ".txt", ".docx", ".doc"):
                files.append(p)
    return files

def main() -> None:
    files = _all_files()
    print(f"共发现 {len(files)} 个文件，开始摄入……\n")
    t0 = time.time()
    ok = skipped = failed = 0
    for p in files:
        r = process_file(p)
        status = r.get("status")
        if status == "processed":
            ok += 1
            line = f"[OK]   {p.name}  -> {r.get('chunks', 0)} chunks ({r.get('doc_type', '?')})"
        elif status == "skipped":
            skipped += 1
            line = f"[跳过] {p.name}  -> {r.get('reason', '')}"
        else:
            failed += 1
            line = f"[失败] {p.name}  -> {r.get('error', '')}"
        print(line)
    dt = time.time() - t0
    print(f"\n完成：成功 {ok} / 跳过 {skipped} / 失败 {failed}，耗时 {dt:.1f}s")
    print("当前各库已入库文件数：", count_by_library())

if __name__ == "__main__":
    main()
