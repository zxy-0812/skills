# ABOUTME: 记忆系统评测失败归因分析的详细方法学、字段格式与踩坑
# ABOUTME: SKILL.md 的按需展开参考，含脚本参数与阈值标定细节

# 方法学与字段参考

## 一、探数据 checklist（每次先做，格式随数据集会变）

```python
# eval 文件（flat 目录，用 os.listdir 避免 rglob 在挂载盘 EMFILE）
# 每个 eval JSON: user_id + qa_eval_results[]
#   QA: query, ground_truth, gpt_answer, correctness_score(1/0/"skip"/None),
#       tag, difficulty, should_recall,
#       recalled_memories[]  (record_id/memory_id, memory_type, status, rerank_score, content/summary),
#       expected_recall_memories[] = GT (memory_content, memory_type),
#       recall_eval.match_details[] (gt_index, sys_index, method, score),
#       recall_eval.recall_rate_at_n4, recall_memory_score, qa_timing.started_at
# 记忆库 dump: <_safe(user_id)>.json -> memories[] (content/summary/memory_type/status/committed_at_ms)
# 日志: <user_id>.ndjson, 行= "ts\t[channel]\t{json}"
```

必查项：
- `recalled_memories` 的 status 分布 → 确认"可召回状态"集合（通常只有 active）。
- GT 的 `memory_type` 词表 vs 库内 `memory_type` 词表是否一致 → 决定是否做类型错位分析。
- correctness 取值（可能有 "skip"/None，排序/统计要兼容）。
- 日志 endpoint：`/auto_capture_v1`、`/auto_recall`、`dream.light/deep/rem`。
- 时间字段 `committed_at_ms/updated_at_ms` 常是秒级字符串 `YYYY-MM-DD HH:MM:SS`，需兼容解析。

## 二、四类归因判定（伪码）

```
sim, Mstar = max_cosine(GT, all_memories_in_bank)   # 全量库，所有状态
hit = (gt_index in match_details)
if hit:                                   concl = A 召回错位/答错
elif sim>=PRESENT_TH and Mstar.status=='active':  concl = B 欠召回
elif sim>=PRESENT_TH and Mstar.status!='active':  concl = C 状态不可召回(status)
else:                                     concl = D 真缺失   # 追 log 诊断
```

## 三、阈值标定（关键）

```python
# 用 eval 已判命中(hit=True)的 GT 的 sim(GT, Mstar) 分布
hit_sims = [sim for r in rows if r.hit]
PRESENT_TH = percentile(hit_sims, 5)   # p5，约95%已知在库被正确判"存在"
```
- 换 embedding / 换语言必须重标定，不可照搬。
- 经验值：bge-small-zh 中文≈0.72；Qwen3-Embedding-0.6B 英文/混杂≈0.66。
- 语言不匹配（如英文语料）→ 换多语言模型（Qwen3-Embedding-0.6B / bge-m3）。

## 四、B 类病因判别树（需 recall 日志 join，按 query 文本）

```
join: recall_log[query] -> need_recall, retrieved_by_type_counts, retrieved_total
if Mstar.committed > qa.recall_started:      病因3 时序（召回早于写入）
elif need_recall is False:                   4d 决策拒召
elif Mstar.id in recalled_ids:               4c eval未对齐（评测口径，非系统没召回）
elif retrieved_total >= rerank_top_n:        4a 疑 top-k 截断
else:                                        4b 检索未命中（关键词/向量 miss）
```
rerank错杀上界：仅 `retrieved_by_type_counts[Mstar.type] > 最终该类型条数` 时才可能是 rerank 裁掉（日志无 rerank 前候选 ID，无法精确点名）。

## 五、top-1 命中（recall@1）

`recalled_memories` 已按 rerank_score 降序 → top-1=下标0。命中 = 存在 `sys_index==0` 的 match_detail。按 QA 统计比例；可再按 top-1 的 memory_type 拆分。

## 六、单条信息三处联查（locate_info）

给定 user_id + 一段信息，语义匹配查 benchmark / 记忆库 / 日志三处：
- 三处都在 → 非丢失，多为类型错位/召回匹配问题
- benchmark 有、库无、有 capture 但 signal 少 → 抽取丢
- benchmark 有、库无、无 capture → 录入丢
- benchmark 无 → 推断型 GT，非丢失
判"有没有"务必语义相似度，不用字面子串。

## 七、报告要点

- 四类占比表，**每个占比标注分母**（全量 GT / 失败 GT / QA 各是多少），换模型对比时并列。
- caveat 置顶：用了什么 embedding、语言是否匹配、阈值如何标定。
- 每类配 1~2 个真实例子（GT vs M\* 内容对照）。
- 分清"可靠 vs 待复核"：A（用 eval match_details）与向量无关，恒可靠；B/D 切分依赖 embedding 与阈值。
- 优化方向按病因给（4d 召回决策、4b 关键词/向量、4a top-k/配额/去重、4c eval口径/多对一、类型错位→抽取分类）。

## 八、脚本参数速查

所有脚本：`--eval-dir --memories-dir --out-prefix --model`，多数还有 `--log-dir`。用 `os.listdir` 扫 `eval_*.json`（跳过 `eval_summary_*`）。

- `analyze_situation.py`：四类归因 + 语义分档 + log诊断(D)。`--present-th`（不传则用默认，建议先跑再按 p5 重标定）、`--all-qa`（分析全部QA而非仅失败）。
- `analyze_underrecall.py`：B 类病因深挖，需 `--log-dir`。
- `analyze_top1hit.py`：recall@1，只需 `--eval-dir --out-prefix`（不用 embedding）。
- `locate_info.py`：`--user-id --info`，单条三处联查。

GPU 紧张时（Qwen3）：`CUDA_VISIBLE_DEVICES=<空闲卡> PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True ... --batch-size 8`。
