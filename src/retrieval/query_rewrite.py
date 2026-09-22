"""Query 改写：把口语化 / 模糊的提问改写成更适合向量检索的规范查询短语。

参考 rag-from-zero 第 7 章「Query 理解与改写」。针对中学语文教学场景：
- 学生口语提问 → 补全篇目 / 学段 / 知识点维度
- 文言实词 / 虚词提问 → 展开为「篇目 + 词 + 含义用法」
- 缩写 / 指代不明 → 补全为书面、具体的检索短语

注意：改写结果**只用于检索**，不影响生成阶段——生成仍然拿到用户的原始提问，
改写只是为了让召回更准。
"""
from __future__ import annotations

from ..config import api_key_ready
from ..llm.deepseek import get_chat_llm

_SYSTEM = """你是中学语文检索查询改写器。把老师或学生的口语化提问，改写成更适合向量检索的规范查询短语。

改写规则：
1. 补全篇目/课文名：若提问引用了某篇课文原句或提到某篇目（如"乃不知有汉"出自《桃花源记》），补上《篇目名》。
2. 补全知识点维度：把"乃是什么意思"改写为"文言虚词'乃'的含义和用法"；把"怎么赏析"改写为"现代文赏析/写作手法"。
3. 口语化、指代不明 → 改成书面、具体、完整。例如"那个虚词怎么用"→ 补全所指的虚词与篇目。
4. 只补关键检索信息，不要展开成完整问题，不要无中生有（不确定篇目不要硬加）。
5. 输出一句改写后的检索短语（中文），不要引号、不要解释、不要多余文字。"""


def rewrite_query(query: str) -> str:
    """返回改写后的检索查询；未配置 key、改写失败或结果异常时，原样返回以保证不中断检索。"""
    q = (query or "").strip()
    if not q or not api_key_ready():
        return query
    try:
        llm = get_chat_llm(temperature=0.0)
        resp = llm.invoke([
            {"role": "system", "content": _SYSTEM},
            {"role": "user", "content": q},
        ])
        out = (resp.content or "").strip()
        # 基本 sanity：长度不能异常暴涨，也不能是空
        if 2 <= len(out) <= max(len(q) * 4, 60):
            return out
        return query
    except Exception:  # noqa: BLE001
        return query
