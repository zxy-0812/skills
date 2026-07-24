---
name: stepmem-eval-run
description: >-
  在 stepmem_eval 项目对 clean_bmk 格式数据集（如 BMK_5884）跑 dream_eval 端到端评测。
  连接线上 StepMem 服务执行评测，处理数据格式识别、user_id 时间戳防覆盖、后台运行、known/gpt 模式选择、进度监控与结果收集。
  也支持用 --dump-p0 拿 capture/light 中间指标（五分类/提取/类型/episodic/gate/target_key）到 per-case JSON 的 p0_dump。
  Triggers on "线上环境跑评测"、"线上跑 dream_eval"、"线上环境评测 BMK"、"线上 stepmem 评测"、"线上环境跑 clean_bmk"、"online eval"、"dump-p0"、"p0_dump"、"capture/light 中间指标"、"跑 capture 评测"。
allowed-tools: Read, Write, Edit, Bash
---

# ABOUTME: 在 stepmem_eval 项目跑 dream_eval 评测的标准流程封装
# ABOUTME: 覆盖 BMK_5884 等 clean_bmk 数据集，含后台运行、监控、结果收集与已知坑规避

# Stepmem Eval Run

在 `stepmem_eval` 项目里对 benchmark 数据集执行 StepMem Dream 端到端评测（`python -m dream_eval eval`）。本 skill 封装了完整流程与已踩过的坑。

## Overview

对 clean_bmk 格式的数据集（如 `data/BMK_5884`）跑评测：capture 对话 → dream pipeline → QA 判分。产出每 case 明细 JSON、summary JSON、HTML 报告到 `outputs/eval/{时间戳}/`。

## When to Use

- 用户要评测 `BMK_5884` 或其他 benchmark 数据集
- 用户提到 dream_eval / stepmem 评测 / clean_bmk

## 关键前提知识

### 项目路径与命令
- 项目根：`/mnt/workspace/zhiyue-L3-TerminalPerceptiveMemory/workspace/zhongxinyu/stepmem_eval`
- 命令：`cd <项目根> && python -m dream_eval eval [options]`

### 数据格式
- **BMK_5884** 结构与内置 `clean_bmk` 完全一致（`sessions[].dialogue_turns` + `capture_memories`/`update_memories` + `QA_list[].recall_memories`），**无需转换**。
- 加载器用 `rglob` 递归扫描嵌套的类别目录，自动识别为 clean_bmk。
- BMK_5884 约 2427 个非空 JSON（user_centric ~1296 / agent_centric ~1131），大量 0 字节空文件会被安全跳过。
- 用 `--input-dir data/BMK_5884` 加载全量；`--input-file <路径>` 跑单个。

### 两种评测模式
| 模式 | 需要 LLM key | 产出指标 |
|------|-------------|----------|
| `known_response`（默认） | 否 | recall 类指标；`query_response_accuracy` / `case_response_accuracy` 为 **N/A** |
| `gpt_response` | **是** | 含完整答题准确率（LLM 作答 + judge 判分） |

要完整答题准确率必须用 `--mode gpt_response --llm-api-key <key> --llm-model <model>`。

### user_id 防覆盖（框架自动满足）
user_id 格式 `{prefix}{seq:03d}_{file_stem}_{YYYYMMDD_HHMMSS}`，时间戳后缀由框架每次 run 自动生成。**只需给带自身标识的 `--user-id-prefix`**（如 `DreamEval_BMK5884`），每次 run 时间戳不同，天然防止二次评测覆盖。

## Workflow

### Step 1：确认参数
向用户确认：数据范围（单文件冒烟 / 子类型 / 全量）、模式（known/gpt）、若 gpt 则需 LLM key 与 model。

### Step 2：先单文件冒烟（推荐）
```bash
cd /mnt/workspace/zhiyue-L3-TerminalPerceptiveMemory/workspace/zhongxinyu/stepmem_eval
nohup python -m dream_eval eval \
  --user-id-prefix DreamEval_BMK5884 \
  --input-file "data/BMK_5884/<某个非空文件>.json" \
  --mode known_response \
  > /tmp/bmk_smoke/smoke.log 2>&1 &
```
gpt 模式追加：`--mode gpt_response --llm-api-key <key> --llm-model claude-opus-4-6`

### Step 3：监控（关键：盯对 PID）
- **`nohup ... & echo $!` 返回的是 bash wrapper PID，不是 python 进程**。用 `pgrep -af "dream_eval eval"` 找真实 python PID，再 `kill -0 <pid>` 判活。
- **多 case/多 worker 时 `pgrep` 会返回多个 PID（含 bash wrapper + worker 子进程）**：盯那个 **`python -m dream_eval eval ...` 带完整参数的主进程**，别盯到 wrapper 或子 worker（曾多次盯错导致监控循环提前退出、误判"跑完了"）。
- 单 case 约 **15 分钟**（4 session × capture 间隔 30s + light dream 180s + rem/deep dream + 19 题 QA）；线上 rem/deep dream 有时会慢到 300~500s，属正常，耐心等。**必须后台运行**，前台会撞超时。
- 用后台 Bash 任务 `while kill -0 <python_pid>; do sleep 20; done` 等待完成，退出后读日志尾部与结果目录。

### Step 4：收集结果
结果在 `outputs/eval/{时间戳}/`：
- `eval_<mode>_clean_bmk_NNN_<episode>_<ts>.json`（每 case 明细，含 user_id）
- `eval_summary_<mode>_<ts>.json` + `.html`
从日志尾部提取指标：`recall_decision_accuracy` / `recall_rate_at_n4` / `query_response_accuracy` 等。

### Step 5：全量
冒烟通过后：
```bash
nohup python -m dream_eval eval \
  --input-dir data/BMK_5884 \
  --user-id-prefix DreamEval_BMK5884 \
  --dataset-subtype user_centric \
  --mode gpt_response --llm-api-key <key> --llm-model claude-opus-4-6 \
  --max-workers 5 --resume \
  > /tmp/bmk_full.log 2>&1 &
```
`--resume` 可跳过已完成 case，中途失败可续跑。

## 拿 capture/light 中间指标（`--dump-p0`）

默认评测只看端到端 QA/召回，**看不到 capture 五分类、light 提取/类型/episodic 这些中间产物**。要评这些 P0/P1 检查点，跑评测时加 `--dump-p0`：

```bash
python -m dream_eval eval \
  --input-file <file>.json --user-id-prefix <prefix> \
  --mode known_response --capture-turn-delay 5 --light-dream-wait-seconds 60 \
  --dump-p0
```

开启后，per-case JSON 顶层多出 `p0_dump`，含三块全量 dump（直连 M0 拉，不经 stepmem 服务）：

| p0_dump 里 | 对应检查点 | 关键字段 |
|------|-----------|---------|
| `evidence[]` | P0-1 capture 五分类 + P1 时间戳 | ★ `extra_json.capture_signal_label`（**不是** `extra_info`）；`extra_json.user_text`；`extra_json.timestamp_source`（content=好 / system=兜底污染）；`capture_seq`=第几轮 |
| `semantic[]` | P0-2 提取 / P0-3 类型 / P1 gate / P1 target_key | `content` / `memory_type` / `status`(active/pending/review_required) / `confidence` / `target_key` |
| `episodic[]` | P0-4 情景叙事 | `content` |

**去重提醒**：evidence 按 `extra_json.capture_id` 去重（同一轮），semantic 按 `content` 去重（同条记忆可能多版本），再统计分布。

**过度提取信号**：`唯一 semantic 数 ÷ 唯一轮次` 若达 10+ 条/轮即为过度提取（曾观测健康 case ≈1、异常 case 达 13~15），常伴随 `memory_type` 塌陷成 user_identity。

## 已知坑与规避

| 现象 | 原因 | 规避 |
|------|------|------|
| `Too many open files` (Errno 24)，写结果 JSON 时失败，产出 0 字节文件 | virtiofs 挂载层**间歇性 fd 分配抽风**（非代码泄漏：单进程 fd 峰值仅 ~100，系统总量正常）。评测其实已算完，只倒在最后写盘 | 重跑该 case；用 `--resume` 续跑；失败不代表数据/服务有问题 |
| 前台命令 exit 143（timeout 杀死） | 单 case 约 15 分钟，超过前台超时 | 一律 `nohup ... &` 后台运行 + 日志文件 |
| 监控循环立即结束/误判 | 盯的是 wrapper PID 而非 python PID | `pgrep -af "dream_eval eval"` 取真实 python PID |
| `query_response_accuracy: N/A` | 用了 known_response 模式无 LLM | 要答题准确率则用 gpt_response + key |
| LLM 预检 400 "does not support chat interface" | `claude-opus-4-6` 不支持 `/v1/chat/completions` | **正常**，客户端自动改用 `/v1/messages`，不是错误 |
| `p0_dump: {"error": "The read operation timed out"}` | evidence 的 `next_cursor` 是偏移量、服务端忽略它 → `fetch_evidence_m0` 翻页不前进死循环到超时 | 已在 `dream_eval/memory/fetcher.py` 修（cursor 去重 + max_pages 兜底）；若复现说明代码回退了 |
| p0_dump 里 evidence 数量异常大（几千条，唯一 user_text 却只有 1） | 同上翻页 bug，同一批被重复拉 | 同上；按 `capture_id` 去重后才是真实轮次数 |
| capture 五分类 label 取不到（全 None） | 找错字段：文档写 `extra_info`，线上 M0 实际在 `extra_json` | 读 `evidence[].extra_json.capture_signal_label` |

## 环境注意
- StepMem 服务 `biz-gw-in.zyql.com`（内网网关）**不校验 token**，`--stepmem-token` 留空也能连通。
- rem/deep dream worker 实际在运行（各约 5s 完成），无需 `--no-trigger-*` 关闭。
- virtiofs 挂载空间偏紧（曾观测 96% 已用）。全量约产出上千个结果 JSON（单 case 明细 ~660KB，1296 case ≈ 850MB），跑全量前用 `df -h` 确认空间。

## 完整参数
详见项目 `README.md` 与 `docs/cli-reference.md`、`docs/01-eval.md`。
