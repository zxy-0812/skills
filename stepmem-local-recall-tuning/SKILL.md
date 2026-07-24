---
name: stepmem-local-recall-tuning
description: 在 DSW 本地起 StepMem 服务，用别人（如 alex）已写入线上 memstore 的 user_id 做只读回放召回（recall_replay），测召回、调参、打分。处理服务启动、512d embedding 维度对齐、只读回放、三口径打分与调参循环。Triggers on "本地起服务调参"、"本地召回调参"、"起 stepmem 服务测召回"、"recall_replay"、"回放召回"、"召回调参"、"local recall tuning"、"召回全空"、"recall_path=None"。
allowed-tools: Read, Write, Edit, Bash
---

# ABOUTME: 在本地起 StepMem 服务对线上 memstore 做只读召回回放与调参的操作 skill
# ABOUTME: 关键依赖 conda env stepmem_local_test、官方 deploy/local/up.sh、512d embedding

# StepMem 本地召回调参

在 DSW 本地起 StepMem 服务，用已写入线上 `cloud-mem-store-dream` 的 user_id 做**只读回放召回**，测召回率、调参数、对比口径。全程不写不删线上记忆。

## 🚨 安全边界（先读）

- ✅ `tools/recall_replay.py` 只调 `/auto_recall`（只读检索），不 capture/不 cleanup/不写/不删。可安全打在别人（alex 等）已写入的 user_id 上。
- 🚨 **绝对禁止**对别人/线上 user_id 跑 `dream_eval eval`（带 cleanup=hard，会**硬删记忆**）。只走 recall_replay 只读路径。
- ⚠️ 用 `--minimal` 只起 api + light_dream，不起 rem/deep/feature/sweeper 写路径 worker，进一步降低误写风险。

## 关键路径与事实

| 项 | 值 |
|---|---|
| 服务代码 | `/mnt/workspace/zhiyue-L3-TerminalPerceptiveMemory/workspace/zhongxinyu/stepmem` |
| 评测/工具 | `/mnt/workspace/zhiyue-L3-TerminalPerceptiveMemory/workspace/zhongxinyu/stepmem_eval` |
| API | `http://127.0.0.1:18687` |
| memstore | `https://biz-gw-in.zyql.com/cloud-mem-store-dream`（线上共享） |
| Python 环境 | conda env `/opt/miniconda3/envs/stepmem_local_test`（依赖全 + jieba + 本仓库 editable） |
| Embedding 维度 | 必须 512d（与 memstore 一致） |

## 最容易踩的坑：embedding 必须 512d

memstore 里记忆是 512d 写入。本地若用 256d 查询 → 检索被拒（`code=40001: embedding dimension must be 512, got 256`）→ **召回全空、`recall_path=None`、`n_retrieved=0`**，极像"记忆被删/被门控"，实为维度不匹配。

- 官方 `deploy/local/env.defaults.sh` 默认已 512；仓库 `.env.local` 也显式固定 512。
- 仓库根 `DSW本地化部署指南.html` 写的"256 MRL"已过时，以脚本默认 512 为准。
- 排查：`grep TRUNCATE_DIM .stepmem_local/runtime.env` 必须是 512；不对就查 `.env.local` 后 `up.sh --restart`。
- 调参时绝不要改 `STEPMEM_BGE_*_DIM`。

## 工作流

### Step 1 — 启动服务

用 conda env `stepmem_local_test`（依赖全 + jieba + 本仓库 editable 已装好）。**别手写 `nohup bash start.sh &`**（会被终端信号打断，exit 144，端口起不来）。

**首选：`up.sh --minimal`**

```bash
cd /mnt/workspace/zhiyue-L3-TerminalPerceptiveMemory/workspace/zhongxinyu/stepmem
conda activate stepmem_local_test      # 或 source deploy/local/tune_env.sh（设 STEPMEM_VENV）
bash deploy/local/up.sh --minimal      # 仅 api + light_dream；改配置用 up.sh --restart --minimal
bash deploy/local/status.sh --check    # 验收：三接口 200 + api/light_dream 有 pid
```

**⚠️ 若 `up.sh` 卡在 `pip install -e .`（"Preparing editable metadata still running" / `error: No such file or directory`）**：
editable 包早已装好（`python -c "import stepmem"` 能过），这步 setup 无必要且会阻断启动。跳过 setup，复用已生成的 `.stepmem_local/runtime.env`（512d），直接 nohup 起 api + worker：

```bash
cd /mnt/workspace/zhiyue-L3-TerminalPerceptiveMemory/workspace/zhongxinyu/stepmem
PY=/opt/miniconda3/envs/stepmem_local_test/bin/python
mkdir -p .stepmem_local/pids .stepmem_local/logs
nohup bash -c "set -a; source .stepmem_local/runtime.env; set +a; exec $PY run_server.py --host 127.0.0.1 --port 18687" \
  >> .stepmem_local/logs/api.log 2>&1 & echo $! > .stepmem_local/pids/api.pid
nohup bash -c "set -a; source .stepmem_local/runtime.env; set +a; exec $PY -m stepmem.dream.main --role light_dream" \
  >> .stepmem_local/logs/worker-light_dream.log 2>&1 & echo $! > .stepmem_local/pids/worker-light_dream.pid
# 等 ~15s，确认端口：ss -ltn | grep 18687
```

- 用 `Bash` 的 `run_in_background` 起（首次含模型 warmup 约 10s），完成后验收。
- 前提：`.stepmem_local/runtime.env` 必须已存在且 `TRUNCATE_DIM=512`（`up.sh` 至少跑到 `_write_runtime_env` 才会生成；没有就先 `up.sh` 一次让它生成，卡在 pip 时再走跳过 setup 的方式）。
- 起不来查 `.stepmem_local/logs/api.log`。

### Step 2 — 只读回放召回

```bash
cd /mnt/workspace/zhiyue-L3-TerminalPerceptiveMemory/workspace/zhongxinyu/stepmem_eval
PY=/opt/miniconda3/envs/stepmem_local_test/bin/python

# 冒烟（前 N 个 user_id，先跑通）
$PY tools/recall_replay.py --results-dir <eval结果JSON目录> \
    --api http://127.0.0.1:18687 --label smoke --limit 10 --concurrency 6

# 全量（去掉 --limit）
$PY tools/recall_replay.py --results-dir <eval结果JSON目录> \
    --api http://127.0.0.1:18687 --label full --concurrency 8
```

- `--results-dir` 必须指向**含 `qa_eval_results` 的 eval 结果 JSON 目录**（如 `outputs/analysis/BMK700_agent/output/`），**不是** `logs/by_user/*.ndjson`（那是 API 访问日志，无 query/gold，会报 `no result files found`）。
- `--limit N` = 前 N 个结果文件（= N 个 user_id）。
- 输出：`outputs/recall_replay/replay_<label>_<时间戳>.json`（含完整 expected + retrieved，支持离线重算）。
- summary 的 `recall_at_k` 是宽松 token 重合口径，只作体检；正式口径见 Step 3。

### Step 3 — 三口径打分

```bash
RUN=outputs/recall_replay/replay_<label>_<时间戳>.json
$PY tools/score_official.py $RUN          # 官方结构化 0.55；headline=recall@(n+4)
$PY tools/score_semantic.py $RUN          # 结构化 OR 余弦≥0.65（需服务在跑）；可调 --struct --cos
```

| 口径 | 判命中 | 特点 |
|---|---|---|
| 官方结构化 | 字符 composite≥0.55 | 最严；同事实被合并成长段落会判负 |
| 语义 | 结构化 OR 余弦≥0.65 | 宽；吃换表述/换粒度；有少量话题误判 |
| any-hit | token 重合≥0.5 | 最宽，仅体检 |

经验：真实召回率落在结构化与语义之间、偏语义端；结构化偏低主因是 gold（原子单事实）vs dream 库（合并多事实长段落）的粒度分布差异。

### Step 4 — 调参循环

召回旋钮写**项目根 `.env.local`**（`up.sh` 自动 source），改完重启生效：

```bash
cd /mnt/workspace/zhiyue-L3-TerminalPerceptiveMemory/workspace/zhongxinyu/stepmem
# 编辑 .env.local 里带 ★ 的核心旋钮，如：
#   STEPMEM_AUTO_RECALL_SCORE_THRESHOLD / _EPISODIC_SCORE_THRESHOLD  粗排阈值
#   STEPMEM_RERANK_SCORE_THRESHOLD / _TOP_N / _REL_EMB_WEIGHT        精排
#   不要改 STEPMEM_BGE_*_DIM（保持 512）
source deploy/local/tune_env.sh && bash deploy/local/up.sh --restart --minimal
# 再跑 recall_replay（换新 --label）+ score，对比不同 label
```

停止服务：`bash deploy/local/down.sh`

## 故障速查

| 现象 | 原因 | 处理 |
|---|---|---|
| 召回全空、`recall_path=None`、`n=0` | 维度 256 vs 512 | 查 runtime.env `TRUNCATE_DIM=512`；改 `.env.local` 后 `up.sh --restart` |
| 日志 `code=40001 ... must be 512, got 256` | 同上 | 同上 |
| `No module named 'jieba'` | 缺 jieba | `/opt/miniconda3/envs/stepmem_local_test/bin/pip install jieba` |
| `up.sh` 报 `.venv/bin/pip 没有那个文件` | `.venv` 损坏 | `source tune_env.sh` 让 STEPMEM_VENV 指 conda env |
| 手写 nohup 起服务 exit 144、端口起不来 | 后台被终端信号打断 | 改用官方 `up.sh` 或 Step 1 里跳过 setup 的 nohup 起法 |
| `up.sh` 卡在 `pip install -e .` / `Preparing editable metadata still running` / `error: No such file or directory` | 每次 setup 重跑 editable install，卡住/临时目录异常 | 包已装好无需 setup，用 Step 1 的"跳过 setup 直接起 api+worker" |
| recall_replay `no result files found` | `--results-dir` 指到了 ndjson 日志目录 | 指向含 `qa_eval_results` 的 eval 结果 JSON 目录 |

## 参考

完整手册（同源）：`stepmem_eval/tools/本地召回调参操作手册.md`
