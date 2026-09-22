"""按文档类型分流的智能切片器。

切片策略（适配语文教学场景，不做一刀切均分）：
- 教案/课堂笔记 -> 按课时、教学环节切
- 学生错题/学生作答样本/习题 -> 单道题 = 最小切片单元
- 文言笔记 -> 单个实词/虚词/特殊句式
- 作文材料 -> 按主题、学生典型立意（偏题/平庸/深刻）
- 其他 -> 兜底语义切片
"""
from __future__ import annotations

from .base import Chunk, split_by_headings, fallback_split
from .lesson_plan import LessonPlanChunker
from .wrong_answer import WrongAnswerChunker
from .classical import ClassicalChunker
from .composition import CompositionChunker

# 文档类型 -> 切片器
_CHUNKERS = {
    "教案": LessonPlanChunker(),
    "课堂笔记": LessonPlanChunker(),
    "学生错题": WrongAnswerChunker(),
    "学生作答样本": WrongAnswerChunker(),
    "习题": WrongAnswerChunker(),
    "文言笔记": ClassicalChunker(),
    "作文材料": CompositionChunker(),
}


def chunk_for(doc_type: str, text: str) -> list[Chunk]:
    chunker = _CHUNKERS.get(doc_type)
    if chunker is None:
        # 兜底：语义切片
        return [Chunk(text=t) for t in fallback_split(text)]
    return chunker.split(text)


__all__ = ["Chunk", "split_by_headings", "fallback_split", "chunk_for"]
