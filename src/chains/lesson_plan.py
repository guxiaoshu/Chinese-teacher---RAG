"""写教案：私有库优先 + 公共库补充，基于老师历年沉淀迭代出新版教案。"""
from __future__ import annotations

from ..retrieval.retriever import retrieve
from ..llm.deepseek import get_reason_llm
from ..ingestion.generated import save_generated
from .common import ChainResult, build_context

_SYSTEM = """你是一位资深中学语文教研员，为一位有多年教学沉淀的老师做「针对性备课」。

你会拿到老师自己历年沉淀的资料（【私有知识库】）+ 教材课标（【公共基准库】），
基于这些资料生成**新版教案**，而不是从零编写。

硬性规则：
1. 优先复用老师过去同篇教案的课堂框架、提问、板书、话术，保持其教学风格，只做更新调整。
2. 自动提取往届学生痛点（来自历史错题/作答样本），写进本课「重难点」和「课堂预设」。
3. 课堂探究问题优先选用老师之前验证过有效的问题；没有现成的才新设计，并标注「新设计」。
4. 输出结构：新版教案（课时、教学目标、重难点、教学流程、课堂提问、板书设计）+ 课堂预设（预判学生哪里容易出错，必须注明依据来自历史学生错题）。
5. 所有引用材料用 [n] 标注；引用时说明来自【私有知识库】还是【公共基准库】。
6. 若私有资料之间冲突，以教师手写批注版本为准。
7. 用 Markdown 输出，语言贴合一线教学，不空谈理论、不套模板话术。
"""


def run(query: str) -> ChainResult:
    docs = retrieve(query)  # 私有优先 + 公共补充
    ctx, citations = build_context(docs)
    user = f"备课需求：{query}\n\n检索到的参考材料：\n{ctx}"
    llm = get_reason_llm()
    resp = llm.invoke([
        {"role": "system", "content": _SYSTEM},
        {"role": "user", "content": user},
    ])
    content = resp.content
    save_generated("写教案", query, content)
    return ChainResult(content=content, citations=citations)
