"""本地 BGE embedding（直接用 transformers，绕开 sentence-transformers）。

背景：本机（i5-1155G7 纯 CPU）实测 sentence-transformers 6.1 的 encode() 与
transformers 5.x 存在兼容性 bug 会卡死，而裸 transformers 前向仅 188ms/条。
因此这里直接加载模型，用 BGE 的标准做法：CLS token 池化 + L2 归一化。

- 文档侧编码：不加检索指令
- 查询侧编码：加 BGE 检索指令（"为这个句子生成表示以用于检索相关文章："）
"""
from __future__ import annotations

import threading

import torch
import torch.nn.functional as F
from transformers import AutoModel, AutoTokenizer

from ..config import CONFIG

_MODEL_NAME = CONFIG["embedding"]["model_name"]
_QUERY_INSTRUCTION = CONFIG["embedding"]["query_instruction"]
_MAX_LEN = 512
_BATCH_SIZE = 32

_model = None
_tokenizer = None
_device = None
_lock = threading.Lock()


def _load():
    global _model, _tokenizer, _device
    if _model is None:
        with _lock:
            if _model is None:
                # 限制 OpenMP 线程数，避免 Windows 上 torch 线程竞争
                try:
                    torch.set_num_threads(max(1, min(4, (torch.get_num_threads() or 4))))
                except Exception:  # noqa: BLE001
                    pass
                _device = "cuda" if torch.cuda.is_available() else "cpu"
                _tokenizer = AutoTokenizer.from_pretrained(_MODEL_NAME)
                _model = AutoModel.from_pretrained(_MODEL_NAME).to(_device)
                _model.eval()
                # 预热：首次前向会触发 oneDNN 图编译（本机约 60s），提前做掉
                _enc = _tokenizer(["预热"], padding=True, truncation=True, return_tensors="pt")
                _enc = {k: v.to(_device) for k, v in _enc.items()}
                with torch.no_grad():
                    _model(**_enc)
    return _model, _tokenizer, _device


def _encode(texts: list[str], normalize: bool = True):
    model, tok, device = _load()
    enc = tok(texts, padding=True, truncation=True, max_length=_MAX_LEN, return_tensors="pt")
    enc = {k: v.to(device) for k, v in enc.items()}
    with torch.no_grad():
        out = model(**enc)
    # BGE 用 [CLS] token（位置 0）作为句向量
    cls = out.last_hidden_state[:, 0]
    if normalize:
        cls = F.normalize(cls, p=2, dim=1)
    return cls.cpu().numpy()


def embed_documents(texts: list[str]) -> list[list[float]]:
    """文档侧编码（不加检索指令），分批处理。"""
    if not texts:
        return []
    results: list[list[float]] = []
    for i in range(0, len(texts), _BATCH_SIZE):
        batch = texts[i : i + _BATCH_SIZE]
        results.extend(_encode(batch, normalize=True).tolist())
    return results


def embed_query(text: str) -> list[float]:
    """查询侧编码（加 BGE 检索指令）。"""
    return _encode([_QUERY_INSTRUCTION + text], normalize=True).tolist()[0]
