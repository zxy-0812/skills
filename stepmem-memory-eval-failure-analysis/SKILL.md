---
name: stepmem-memory-eval-failure-analysis
description: 对记忆系统（StepMem/Dream 等）的评测结果做失败归因分析。用 BGE/Qwen3 等 embedding 判"该召回的记忆在不在库里"，把 correctness=0 的失败逐条分成四类（A 召回错位/答错、B 欠召回、C 状态不可召回、D 真缺失），并对 B 类深挖病因（4a top-k截断/4b 检索未命中/4c eval未对齐/4d 决策拒召/病因3 时序）、分析 memory_type 错位、top-1 命中率，输出 CSV + HTML/MD 报告。Triggers on "失败归因"、"欠召回分析"、"召回失败分析"、"评测失败分析"、"四类归因"、"memory eval analysis"、"recall failure analysis"、"类型错位"、"在不在记忆库"。
allowed-tools: Bash, Read, Write, Edit
metadata:
  domain: memory-system-eval
---

# ABOUTME: 记忆系统评测失败归因分析方法与脚本（四类归因 + B类病因 + 类型错位 + top1命中 + 单条联查）
# ABOUTME: 依赖本地 embedding（bge-small-zh / Qwen3-Embedding-0.6B）判"在不在库"，阈值须按模型重标定

# 记忆系统评测失败归因分析

对一次记忆系统评测（eval 输出 + 记忆库 dump + dream 日志）做系统化的失败归因。核心问题：**correctness=0 的失败，究竟是"记忆没生成"，还是"生成了却没召回/召回了却答错/评测没对齐"？**

## 数据三件套与关联

分析需要三份数据，通过 **`user_id`（== 文件名 stem，常含 `ep_xxxxxx`）** 相互关联：

| 数据 | 内容 | 关键字段 |
|---|---|---|
| **eval 输出** `eval_*.json` | 每题 QA + 判分 | `user_id` · `qa_eval_results[]`（`query/ground_truth/gpt_answer/correctness_score/recalled_memories/expected_recall_memories(=GT)/recall_eval.match_details`） |
| **记忆库 dump** `<user_id>.json` | 该用户全量记忆 | `memories[]`（`content/summary/memory_type/status/committed_at_ms`） |
| **dream 日志** `<user_id>.ndjson` | 三段式 `ts\t[channel]\t{json}` | `/auto_capture_v1`（capture）·`/auto_recall`（含 `retrieval_result_snapshot`）·`dream.light/deep/rem` |

**QA 与 GT 的区别**：QA 是"一道题"；GT（`expected_recall_memories`）是"这题应召回的记忆"，一题可多条。归因**按 GT 逐条**统计；"召回为0"等按 QA 统计。

## 关键事实（先确认，可能随版本变）

- **只有 `status=active` 的记忆会被召回**（用 `recalled_memories` 的 status 分布验证；其余 rem_processed/pending/review_required 不可召回）。
- **命中判定以 eval 的 `recall_eval.match_details` 为权威**（`gt_index`↔`sys_index`，`sys_index` 是 `recalled_memories` 下标）。
- `recalled_memories` 按 `rerank_score` 降序，**top-1 = 下标 0**。
- recall 日志 `retrieval_result_snapshot`：`retrieved_memory_ids` 是 **rerank 后**最终集；`retrieved_by_type_counts` 是 **rerank 前**按类型候选计数（**不含候选 ID**）；配置有 `rerank_top_n / top_k_per_type / score_threshold`。

## 四类归因（核心方法，A/B/C/D）

对每条 `correctness_score==0` 的 GT，用 embedding 对**全量库(所有状态)** 检索语义最相似记忆 **M\***：

| 类 | 判定 | 含义 |
|---|---|---|
| **A 召回错位/答错** | GT 在 `match_details` 里（命中）但整题 correctness=0 | 记忆召回对了，答题/生成错 |
| **B 欠召回** | 未命中 且 `sim(GT,M*)≥PRESENT_TH` 且 `M*.status=active` | 库里有、可召回，却没召回 → 检索/排序/决策 |
| **C 状态不可召回** | 未命中 且 sim≥TH 且 M\* 状态非 active | 状态流转导致不进召回 |
| **D 真缺失** | 未命中 且 sim<PRESENT_TH | 库里根本没有 → 追 log 定位丢在哪 |

**D 的 log 追踪**：capture 调用数 / evidence / signal——signal=0 且有 capture → 抽取漏；无 capture → 录入漏；有 signal → 抽取粒度/占位空壳。

## 🚨 阈值必须按 embedding 模型重标定（最易错的一步）

`PRESENT_TH` 不能跨模型/跨语言照搬。标定法：**用"eval 已判命中(库里确有)的 GT"的 M\* 相似度分布，取其 p5 作为 PRESENT_TH**（约 95% 已知在库记忆被正确判为存在）。

实测：bge-small-zh 全中文 ≈0.72；Qwen3-Embedding-0.6B 英文/中英混杂 ≈0.66。**照搬旧阈值会把已知在库记忆大量误判成 D 真缺失**（英文用 zh 模型时 D 虚高到 7~12%，标定后回落到 <1%）。

**语言不匹配时换多语言 embedding**（Qwen3-Embedding-0.6B / bge-m3），别用中文模型跑英文。判"在不在库"务必用**语义相似度**而非字面子串（记忆是改写存储的，子串会假阴性）。

## B 类病因深挖（判别树，需 recall 日志）

对每条 B 类 GT（M\* 未进最终召回集）：

1. `M*.committed_at > 该QA召回时刻` → **病因3 时序**（召回早于写入）
2. `need_recall=False` → **4d 决策拒召**（整题没检索）
3. `M*.record_id ∈ recalled_memories` → **4c eval未对齐**（其实召回了，eval 结构化匹配没判命中 → 评测口径）
4. 否则 `retrieved_total≥rerank_top_n` → **4a 疑 top-k 截断**
5. 否则（`<rerank_top_n`）→ **4b 检索未命中**（关键词/向量 miss）

注：`recalled==检索候选集`时，rerank 前候选 ID 不可得，只能用 `retrieved_by_type_counts` 给"rerank错杀 vs 检索漏"的**上界**（该类型 pre>fin 才可能是 rerank 裁掉）。

## 类型错位分析（仅当 GT 与库用同一 memory_type 词表时才做）

比较 `GT.memory_type` vs `M*.memory_type`，统计错位率与方向。**HaluMem 等用自有词表（Persona/Event/Relationship）时跳过此项**（与库内 stepmem 类型 user_identity/episodic/... 不可比，会 trivially 100% 错位）。StepMem agent_centric 数据里此项曾达 ~60%（method/knowledge 被降级成 identity）。

## 工作流

1. **探数据**：确认 eval/记忆/日志三者目录、`user_id` 关联、GT/recalled 字段、memory_type 词表、status 分布、日志 endpoint 格式。**格式可能随数据集变，先看再跑。**
2. **选模型 + 标定阈值**：语言匹配就 bge-small-zh，不匹配换 Qwen3/bge-m3；跑一遍拿到 sim，用命中GT的 p5 定 `PRESENT_TH`。
3. **四类归因**：`scripts/analyze_situation.py`（analyze_situation.py 风格 + 结论列）→ `*_situation.csv/md`。
4. **B 类深挖**（可选）：`scripts/analyze_underrecall.py` → 病因分布。
5. **辅助**：`scripts/analyze_top1hit.py`（recall@1）、`scripts/locate_info.py`（单条信息三处联查）。
6. **报告**：四类占比表 + caveat（模型/语言/阈值）+ 例子 + 优化方向。**所有占比标注分母（全量 GT / 失败 GT / QA），换模型对比时并列。**

详细字段格式、脚本参数、踩坑见 `references/methodology.md`。脚本用法见各脚本 `--help` 或文件头 docstring。

## 常见坑

- **rglob 在不稳定挂载盘上会 EMFILE**：脚本一律用 `os.listdir` 扫文件、`with open` 读、必要时 cwd 切到 `/tmp` 跑。
- **GPU 被占**：Qwen3-0.6B 用 `--batch-size 8` + `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True` + 指定空闲卡 `CUDA_VISIBLE_DEVICES`。
- **产出易随挂载回滚丢失**：脚本副本同时留一份到产出目录 / `/tmp`。
- **时间字段名叫 `_ms` 实为秒级字符串**（`2026-07-12 16:23:44`），解析时兼容。
