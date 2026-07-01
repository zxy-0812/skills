---
name: code-daily-analysis
description: 分析某个 Git 仓库当天（或指定日期/区间）的工作新增内容，自动归纳成结构化日报并写入仓库的 daily/YYYY-MM-DD.md。适用于总结每天的代码改动、生成工作日报、盘点新增文件与关键变更。Triggers on "每天工作分析"、"今天做了什么"、"生成日报"、"工作日报"、"daily analysis"、"总结今天的改动"、"新增内容分析"。
---

# ABOUTME: 分析 Git 仓库每日工作新增内容并生成结构化日报的助手
# ABOUTME: 采集当天 git 改动、按主题归纳、写入 daily/YYYY-MM-DD.md

# 每日工作新增内容分析

读取一个 Git 仓库在指定时间范围内的改动，归纳成结构化日报，写入 `daily/YYYY-MM-DD.md`。

## 何时使用

**在以下情况使用此 skill：**
- 想总结「我今天在这个仓库里做了哪些新增和改动」
- 需要生成每天/每周的工作日报
- 盘点新增文件、改动量、关键变更点与遗留 TODO

**改用其他方案当：**
- 只是要提交代码或管理分支 —— 用 `code-git`
- 需要跨多个无关仓库的全局统计 —— 本 skill 一次针对一个仓库，逐个运行

## 前置约定

- 目标仓库需为 Git 仓库；日报默认写入该仓库的 `daily/` 目录（不存在则创建）。
- 默认分析对象为「今天」（本地时区 00:00 至现在）。可指定日期或提交区间。
- 日报是分析产出，不是代码；提交时可与代码分开成一条 `docs(daily): ...`。

## 工作流程

### 第 1 步：确定仓库与时间范围

```bash
# 进入目标仓库（示例）
cd /path/to/repo

# 确认是 git 仓库、看当前分支
git rev-parse --is-inside-work-tree && git branch --show-current
```

时间范围三选一：
- **今天**（默认）：`--since=midnight`
- **指定某天**：`--since="2026-07-01 00:00" --until="2026-07-02 00:00"`
- **自上次某提交/昨天**：`@{yesterday}` 或 `<commit>..HEAD`

### 第 2 步：采集当天改动

```bash
# 今天的提交列表（含改动统计）
git log --since=midnight --stat --date=short \
  --pretty=format:'%h %ad %an %s'

# 今天相对昨天同一时刻的总体差异统计（分组看改动量）
git diff --stat "@{yesterday}" HEAD

# 新增文件（今天新加入版本库的）
git log --since=midnight --diff-filter=A --name-only --pretty=format: | sort -u | sed '/^$/d'

# 尚未提交的工作区改动（今天还没 commit 的部分也要纳入分析）
git status --short
git diff --stat
```

如需看具体内容而非仅统计，去掉 `--stat` 换 `-p`，或对单个文件 `git diff @{yesterday} HEAD -- <file>`。

### 第 3 步：归纳分析

从上一步输出中提炼，**不要逐行罗列 diff**，而是按主题归纳：
- **今日新增**：新增了哪些功能/文件/模块（一句话说清「做了什么、为什么」）
- **改动摘要**：修改了哪些已有部分，关键逻辑变化
- **改动量**：文件数、+/- 行数（来自 `--stat` 汇总行）
- **遗留 / TODO**：未完成项、临时方案、需要后续跟进的点（可扫 `git diff` 里的 `TODO`/`FIXME`）

### 第 4 步：写入日报

写入 `daily/YYYY-MM-DD.md`（日期用目标日期，非运行日期）。模板见
**[references/report-template.md](references/report-template.md)**。

若当天日报已存在：追加一个带时间戳的小节，不要覆盖既有内容。

### 第 5 步（可选）：提交日报

```bash
git add daily/YYYY-MM-DD.md
git commit -m "docs(daily): YYYY-MM-DD 工作日报"
```

## 使用示例

**「分析我今天在 men_harness 里做了什么」**
1. `cd .../dev/code/men_harness`
2. 跑第 2 步的四条命令
3. 按第 3 步归纳
4. 写入 `daily/2026-07-01.md`（用模板）

**「补一份 6 月 30 号的日报」**
- 第 2 步命令的时间范围改成
  `--since="2026-06-30 00:00" --until="2026-07-01 00:00"`，其余相同。

## 注意事项

- 日期一律用**目标日期**命名文件，避免跨天运行时错位。
- 分析要**归纳**而非搬运 diff；读者要的是「今天推进了什么」，不是逐行代码。
- 涉及敏感信息（密钥/token）不要写进日报。
- 只读采集为主；除第 5 步外不改动代码。
