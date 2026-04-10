# paper-skills
skills for paper

# Cursor Skills Collection

这个仓库目录用于存放可复用的 Cursor Skills，支持批量导入到 Cursor 并持续更新。

## 目录结构

每个 skill 一个文件夹，最少包含一个 `SKILL.md`：

```text
.cursor/skills/
├── innovation-summary-evaluator/
│   └── SKILL.md
└── ...more-skills/
```

## 快速开始

### 方式一：导入为全局 Skills（推荐）

全局导入后，所有项目都可用。

```powershell
powershell -ExecutionPolicy Bypass -File "$HOME\.cursor\update-skills.ps1" `
  -RepoUrl "https://github.com/<your-name>/<your-skills-repo>.git" `
  -Target global `
  -Branch main
```

导入路径：`C:\Users\<you>\.cursor\skills`

---

### 方式二：导入为项目 Skills

仅对当前项目生效。

```powershell
powershell -ExecutionPolicy Bypass -File "$HOME\.cursor\update-skills.ps1" `
  -RepoUrl "https://github.com/<your-name>/<your-skills-repo>.git" `
  -Target project `
  -ProjectRoot "D:\dev\code\your-project" `
  -Branch main
```

导入路径：`<project-root>\.cursor\skills`

## 手动安装（不使用脚本）

### 全局

```powershell
cd $HOME\.cursor
git clone https://github.com/<your-name>/<your-skills-repo>.git skills
```

### 项目

```powershell
cd <your-project>\.cursor
git clone https://github.com/<your-name>/<your-skills-repo>.git skills
```

## 如何更新

如果你已经导入过，后续更新只需再次运行同步脚本，或在对应目录执行：

```powershell
git pull --ff-only
```

## 如何编写新 Skill

1. 新建目录：`<skill-name>/`
2. 创建文件：`<skill-name>/SKILL.md`
3. 在 `SKILL.md` 中添加 frontmatter：

```markdown
---
name: your-skill-name
description: Describe what this skill does and when to use it.
---
```

## 命名规范建议

- `name` 使用小写 + 连字符，例如：`innovation-summary-evaluator`
- `description` 需要包含：
  - 该 skill 做什么
  - 什么时候触发（建议包含 `Use when ...`）

## 常见问题

### 1) 看不到新 skill

- 重启 Cursor 或切换一次工作区
- 检查路径是否正确：`~/.cursor/skills` 或 `<project>/.cursor/skills`

### 2) skill 不触发

- 检查 `description` 是否写清楚触发场景
- 提问时包含更明确触发词（如“请用 xxx skill 处理”）

### 3) 不要放到 `skills-cursor`

`skills-cursor` 是 Cursor 内置目录，不用于用户自定义 skill。
