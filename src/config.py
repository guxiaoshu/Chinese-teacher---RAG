"""全局配置加载：.env + config.yaml + 路径常量。

所有模块从这里读取配置，避免散落魔法值。
"""
from __future__ import annotations

import os
from pathlib import Path

import yaml
from dotenv import load_dotenv

# 项目根目录 = src 的上一级
BASE_DIR = Path(__file__).resolve().parent.parent

# 先加载 .env（幂等）
load_dotenv(BASE_DIR / ".env")

_CONFIG_PATH = BASE_DIR / "config.yaml"


def load_config() -> dict:
    with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


CONFIG = load_config()

# ---------------- 路径常量 ----------------
DATA_DIR = BASE_DIR / CONFIG["paths"]["data_dir"]
CHROMA_DIR = BASE_DIR / CONFIG["paths"]["chroma_dir"]
DB_PATH = BASE_DIR / CONFIG["paths"]["sqlite_db"]
INGEST_DIR = BASE_DIR / CONFIG["paths"]["ingest_dir"]
PRIVATE_DIR = INGEST_DIR / "private"
PUBLIC_DIR = INGEST_DIR / "public"

for _d in (DATA_DIR, CHROMA_DIR, INGEST_DIR, PRIVATE_DIR, PUBLIC_DIR):
    _d.mkdir(parents=True, exist_ok=True)

# ---------------- 环境变量 ----------------
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "").strip()

# HuggingFace 镜像（国内下载 embedding 模型加速）。必须在导入 sentence-transformers 前设置。
_HF_ENDPOINT = os.getenv("HF_ENDPOINT", "").strip()
if _HF_ENDPOINT:
    os.environ.setdefault("HF_ENDPOINT", _HF_ENDPOINT)


def api_key_ready() -> bool:
    """key 是否已填真实值（用于前端给出友好提示）。"""
    return bool(DEEPSEEK_API_KEY) and "你的API key" not in DEEPSEEK_API_KEY and DEEPSEEK_API_KEY.startswith("sk-")


# ---------------- 便捷访问配置 ----------------
def authority_weight_map() -> dict[str, int]:
    """权威等级 -> 权重。"""
    return {item["name"]: int(item["weight"]) for item in CONFIG["tagging"]["authority"]}


def allowed_doc_types() -> list[str]:
    return CONFIG["tagging"]["doc_types"]


def allowed_grades() -> list[str]:
    return CONFIG["tagging"]["grades"]


def allowed_knowledge_points() -> list[str]:
    return CONFIG["tagging"]["knowledge_points"]


def allowed_learning_tags() -> list[str]:
    return CONFIG["tagging"]["learning_tags"]
