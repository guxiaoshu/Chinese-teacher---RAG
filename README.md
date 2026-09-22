# 语文教学 RAG 助手

> 一个面向中学语文老师的、基于 LangChain 的生产级 RAG 系统：**把 PDF / TXT / DOCX / DOC 拖进文件夹，自动打标签、按教学场景智能切片、双库入库，跑通「写教案 → 出题 → 答疑 → 错题沉淀」的教学闭环。**

---

## 这个系统是什么

它不是「又一个文档问答 demo」，而是**为语文教学这件事专门设计的知识系统**：

- 把你手里的教材、真题、参考书放进**公共基准库**，把你自己的教案、课堂记录、学生错题放进**私有知识库**。
- 检索时**私有优先、公共补充**——备课先调你历年同篇教案，缺的再用教材补。
- 四个场景连成闭环：**写教案 → 出题 → 答疑 → 错题沉淀**，沉淀下来的错题又反哺下一次备课与命题，越用越准。

**目标用户**：有电脑基础、会拖文件的中学语文老师（不需要会编程）。所有能力通过网页界面完成。

## 它和通用 RAG 有什么不一样

| 维度 | 通用 RAG（问答机器人） | 本系统 |
|---|---|---|
| 切片 | 一刀切均分 | **按语文场景**：教案按课时、错题按单题、文言按实词/虚词、作文按立意 |
| 入库 | 直接入库 | **先打六维标签**（学段/单元/篇目/知识点/文档类型/学情）再切片 |
| 知识库 | 单一库 | **双库隔离**：公共基准库 + 私有知识库，私有优先 |
| 排序 | 只看相似度 | 相似度 + **权威加权**（教师批注 > 教材 > 学生作答） |
| 冲突处理 | 无 | **以教师手写批注为准** |
| 输出 | 一段答案 | **结构化产出**：教案/试卷/学情报告，带 `[n]` 引用溯源 |
| 沉淀 | 无 | **错题回流**，形成教学知识资产 |

---

## 四大场景闭环

本系统为语文老师打造「备课 → 命题 → 答疑 → 沉淀」四步闭环：

1. **✍️ 写教案** — 私有库优先召回你历年教案、课堂记录、学生错题，自动提取往届痛点，迭代出保留你个人风格的新版教案与课堂预设。
2. **📝 出题** — 薄弱点必须出自私有错题库，选择题干扰项取自学生真实错误作答，对标课标不超纲。
3. **💬 答疑** — 沿用你课堂用过的例子与话术，启发式引导学生，不直接给完整答案。
4. **📊 错题沉淀** — 答疑与批改中新暴露的错题、易混淆点回流私有库，成为下次备课、命题的依据。

四步首尾相连：错题不断喂给备课与命题，系统随教学持续积累，形成真正属于自己的教学知识资产。

---

## 系统架构

系统分「离线建库」与「在线问答」两条链路，与通用 RAG 一致，但每个环节都做了语文教学定制：

```
离线建库（拖文件即触发）
  文件 → 解析(txt/pdf/docx/doc) → 六维分类打标签 → 智能切片(按文档类型)
       → 向量化(BGE 本地) → 双库入库(public/private) → 重建 BM25 索引

在线问答（四大场景）
  提问 → Query 改写 → 混合检索(向量 + BM25 → RRF 融合，私有优先 + 权威加权)
       → 场景链(DeepSeek，按场景选模型/规则) → 生成结果 + [n] 引用溯源
```

### 核心能力

- **拖文件即入库**：`ingest/private`（私有库）与 `ingest/public`（公共库）自动监听 + 网页上传 + 手动扫描兜底。
- **入库前打标签**：学段 / 单元 / 篇目 / 知识点 / 文档类型 / 学情标签，六维分类（DeepSeek JSON 模式）。
- **适配语文场景的智能切片**（不搞一刀切均分）：
  - 教案 / 课堂笔记 → 按课时、教学环节切
  - 错题 / 学生作答 → 单道题（题干 + 学生错误答案 + 教师批注）为最小单元
  - 文言笔记 → 单个实词 / 虚词 / 特殊句式
  - 作文材料 → 按主题、学生典型立意（偏题 / 平庸 / 深刻）
- **双向量库**：`public_base` 与 `private_kb` 隔离；检索时私有优先、公共补充。
- **冲突以教师手写批注为准**：authority 权重 + prompt 规则双重保证。
- **全量溯源**：生成结果标注 `[n]` 引用，区分【私有知识库】/【公共基准库】。
- **Query 改写**：口语化 / 模糊提问先自动改写为规范检索短语（补篇目 / 知识点），提升召回。
- **检索质量评估**：内置评估集 + Recall@k / MRR，量化验证每次改动。

---

## 快速开始

### 1. 环境要求

- Windows / macOS / Linux，Python 3.10+
- （可选，提速）NVIDIA GPU；无 GPU 也能跑，只是 embedding 走 CPU

### 2. 安装依赖

```bash
cd rag-teacher
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# 有 NVIDIA GPU：先装 CUDA 版 torch，再装其余
pip install torch --index-url https://download.pytorch.org/whl/cu121
pip install -r requirements.txt

# 无 GPU：直接装（torch 会装 CPU 版）
pip install -r requirements.txt
```

> 读取老格式 `.doc` 需要本机安装 MS Word 或 WPS（通过 COM 转换），并已装 pywin32（requirements 已含）。

### 3. 配置 API key

```bash
cp .env.example .env   # Windows: copy .env.example .env
```

编辑 `.env`，把 `DEEPSEEK_API_KEY` 的值改成你的真实 key（不加引号）：

```
DEEPSEEK_API_KEY=sk-xxxxxxxx
```

### 4. 启动

```bash
streamlit run app/streamlit_app.py
```

> 如果提示 `streamlit: command not found`，用 `python -m streamlit run app/streamlit_app.py`。

浏览器打开后，左侧「上传入库」或直接把文件拖进 `ingest/private`、`ingest/public` 文件夹即可。

### 5. 跑不通？常见问题

| 现象 | 原因 | 解决 |
|---|---|---|
| `streamlit: command not found` | Scripts 目录不在 PATH | 用 `python -m streamlit run app/streamlit_app.py` |
| `No module named 'jieba' / 'streamlit'` 等 | 依赖只装了一半 | 再跑一次 `pip install -r requirements.txt` |
| 第一次提问/入库很慢（约 60s） | embedding 模型首次预热（oneDNN 编译） | 正常现象，等一次就好，之后毫秒级 |
| 首次入库下载模型慢 | 国内网络拉 HuggingFace 慢 | `.env` 里已配 `HF_ENDPOINT=https://hf-mirror.com` 镜像 |
| 终端中文乱码 | Windows 控制台编码问题 | 命令行前加 `PYTHONUTF8=1` |
| `.doc` 文件读不出来 | 老格式需 Word/WPS 的 COM | 本机安装 MS Word 或 WPS |
| 某些 PDF 入库被跳过 | 扫描版 PDF 无文本层 | 需先 OCR；或换有文字层的 PDF |
| 上传后出题/学情分析提示「无相关内容」 | 私有库还是空的 | 先把教案/错题放进 `ingest/private` |

---

## 使用说明

### 准备资料：什么进哪个库

| 资料类型 | 放进 |
|---|---|
| 你的教案、课堂笔记、课件、板书 | `ingest/private`（私有知识库） |
| 学生错题、作答样本、作文 | `ingest/private` |
| 教材、真题、参考书、文言选本 | `ingest/public`（公共基准库） |
| 优质课案例、课标、教参 | `ingest/public` |

> 判断原则：**你自己沉淀的东西进私有库**，**通用的基准资料进公共库**。出题和学情分析只认私有库，所以私有库越丰富，这两个场景越强。

### 入库：三种方式任选

1. **网页上传**：左侧栏选「私有知识库」或「公共基准库」→ 拖文件进上传框。
2. **拖进文件夹**：直接把文件放进 `ingest/private` 或 `ingest/public`，自动监听入库。
3. **手动扫描**：左侧点「🔍 扫描现有文件」。

支持格式：PDF / TXT / DOCX / DOC。

### 四大场景怎么用

每个场景在网页顶部对应一个 Tab，输入一句话需求即可：

| 场景 | 输入示例 | 得到什么 |
|---|---|---|
| ✍️ 写教案 | 「帮我备《桃花源记》，八年级下，两课时」 | 新版教案（课时/目标/重难点/流程/提问/板书）+ 课堂预设（标注学生易错点依据） |
| 📝 出题 | 「给《紫藤萝瀑布》出 20 分钟随堂练，重点考象征手法」 | 试题 + 答案 + 评分细则 + 命题说明 |
| 💬 答疑 | 「学生问'乃不知有汉'的'乃'是什么意思，我该怎么引导？」 | 启发式回复（不直接给答案），并引用你库里的例句 |
| 📊 学情分析 | 「分析《桃花源记》这一课学生的整体薄弱点」 | 高频错误 / 易混淆点 / 共性错误 / 教学建议 |

每个结果下方都有「📎 引用来源」折叠面板，标注每条来自 🟢私有知识库还是 🔵公共基准库，并附文件名与文档类型。

---

## 配置说明

### config.yaml

标签体系、切片规则、模型与检索参数都集中在这里，可直接改：

- `tagging.grades / knowledge_points / doc_types / learning_tags` — 六维标签的枚举值，可增删。
- `tagging.authority` — 权威等级权重（教师批注=5 最高）。
- `llm` — DeepSeek 模型（`deepseek-chat` 快模型 / `deepseek-reasoner` 推理模型）。
- `embedding.model_name` — 本地 embedding 模型（默认 `BAAI/bge-base-zh-v1.5`）。
- `retrieval` — 私有/公共召回条数、RRF 参数、私有加权、权威加成。
- `chunking` — 兜底切片的块大小与重叠。

### .env

```
DEEPSEEK_API_KEY=sk-xxxxxxxx          # DeepSeek key（必填）
HF_ENDPOINT=https://hf-mirror.com     # 国内下载 embedding 模型镜像（可选）
```

---

## 目录结构

```
rag-teacher/
├── README.md                  # 本文件（使用说明书）
├── docs/design.md             # 详细设计说明
├── config.yaml                # 标签体系 / 切片规则 / 模型与检索参数
├── .env                       # API key（不入库）
├── requirements.txt
├── ingest/
│   ├── private/               # 私有知识库源文件（你的教案/错题）
│   └── public/                # 公共基准库源文件（教材/真题）
├── src/
│   ├── config.py              # 配置加载
│   ├── llm/                   # DeepSeek 客户端 + BGE 本地 embedding
│   ├── ingestion/             # 文档解析 / SQLite 状态库 / 文件监听
│   ├── tagging/               # 六维分类打标签
│   ├── chunking/              # 四种智能切片器
│   ├── vectorstore/           # ChromaDB 双库
│   ├── retrieval/             # 多路召回 + Query 改写 + 私有优先 + 权威加权
│   ├── chains/                # 写教案 / 出题 / 答疑 / 学情分析
│   └── pipeline.py            # 端到端入库流水线
├── app/streamlit_app.py       # 前端（四大场景 + 上传 + 文件管理）
├── scripts/                   # 运维脚本
│   ├── ingest_all.py          #   批量摄入 ingest/ 下所有文件
│   ├── reclassify.py          #   重跑某类（如"其他"）文件的新分类
│   ├── rechunk.py             #   只重切片（保留原标签，跳过分类）
│   └── eval_retrieval.py      #   检索质量评估 Recall@k / MRR
└── data/
    ├── eval_set.json          # 检索评估集（可自行增删）
    └── ...                    # 运行时生成（Chroma + SQLite）
```

---

## 运维脚本

改了分类提示词或切片逻辑后，用下面脚本重跑受影响文件（都在项目根目录执行）：

```bash
python scripts/ingest_all.py            # 批量摄入 ingest/ 下所有文件
python scripts/reclassify.py 其他       # 把误分类成「其他」的文件重新分类
python scripts/rechunk.py 文言笔记      # 只重切片（不重新分类，保留原标签）
python scripts/eval_retrieval.py        # 检索质量评估（对比 Query 改写开关）
```

## 检索质量评估

系统内置评估集（`data/eval_set.json`，可增删），用 `Recall@k` 和 `MRR` 量化检索质量：

```bash
python scripts/eval_retrieval.py
```

输出示例：

```
===== Query 改写 关闭（k=5）=====
Recall@5: 100.00%  (23/23)
MRR:       0.920
```

评估集支持两种匹配粒度：`expected`（按来源文件，粗）和 `expect_text`（按块内容关键词，细）。

---

## 安全提示

- API key 只存在于 `.env`，已加入 `.gitignore`，不会进入版本库或代码。
- 若你的 key 曾暴露在对话 / 提交记录中，建议到 DeepSeek 后台轮换。
- 本系统所有数据本地运行，文档与向量库都在你的机器上，不上传第三方。
