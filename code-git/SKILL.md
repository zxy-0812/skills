---
description: 帮助进行 Git 代码提交、分支管理和版本控制的工作流。适用于提交代码、创建分支、编写提交消息、处理合并冲突，以及遵循最佳实践的 Git 操作。
alwaysApply: false
---
# Git 代码提交助手

帮助您高效、规范地进行 Git 代码提交和版本控制。

## 何时使用

**在以下情况使用此 skill:**
- 需要提交代码到 Git 仓库
- 创建和管理分支
- 编写规范的提交消息
- 处理合并冲突
- 进行代码审查前的准备
- 需要遵循团队 Git 工作流

**改用其他方案当:**
- 需要复杂的 Git 历史重写（rebase、cherry-pick 等）
- 需要处理大型二进制文件
- 需要 Git LFS 相关操作

## 快速开始

### 检查当前状态

```bash
# 查看工作区状态
git status

# 查看详细的变更内容
git diff

# 查看已暂存的变更
git diff --staged

# 查看提交历史
git log --oneline -10
```

### 基本提交流程

```bash
# 1. 查看变更
git status

# 2. 添加文件到暂存区
git add <文件路径>
# 或添加所有变更
git add .

# 3. 提交变更
git commit -m "提交消息"

# 4. 推送到远程仓库
git push
```

## 核心功能

### 提交消息规范

遵循约定式提交（Conventional Commits）格式：

```
<类型>(<范围>): <主题>

<正文>

<脚注>
```

**类型（Type）**:
- `feat`: 新功能
- `fix`: 修复 bug
- `docs`: 文档变更
- `style`: 代码格式（不影响代码运行）
- `refactor`: 重构（既不是新功能也不是 bug 修复）
- `perf`: 性能优化
- `test`: 测试相关
- `chore`: 构建过程或辅助工具的变动
- `ci`: CI 配置文件和脚本的变更

**示例**:

```bash
# 新功能
git commit -m "feat(api): 添加用户认证接口"

# 修复 bug
git commit -m "fix(parser): 修复 JSON 解析空值错误"

# 文档更新
git commit -m "docs(readme): 更新安装说明"

# 性能优化
git commit -m "perf(cache): 优化缓存命中率"

# 重构
git commit -m "refactor(utils): 重构字符串处理函数"
```

### 多行提交消息

```bash
git commit -m "feat(api): 添加用户认证接口" \
           -m "- 实现 JWT token 生成和验证" \
           -m "- 添加用户登录和注册接口" \
           -m "- 更新 API 文档"
```

或使用编辑器：

```bash
git commit
# 在打开的编辑器中编写多行消息
```

### 提交特定文件

```bash
# 提交单个文件
git add src/api/auth.py
git commit -m "feat(api): 添加认证模块"

# 提交多个特定文件
git add src/api/auth.py src/models/user.py
git commit -m "feat: 添加用户认证功能"

# 交互式选择要提交的代码块
git add -p
```

### 修改最后一次提交

```bash
# 修改提交消息
git commit --amend -m "新的提交消息"

# 添加遗漏的文件到上次提交
git add forgotten_file.py
git commit --amend --no-edit

# 修改提交并保持原消息
git add more_changes.py
git commit --amend --no-edit
```

## 分支管理

### 创建和切换分支

```bash
# 创建新分支
git checkout -b feature/user-authentication

# 或使用新语法
git switch -c feature/user-authentication

# 切换到已有分支
git checkout main
# 或
git switch main

# 查看所有分支
git branch -a
```

### 提交到分支

```bash
# 1. 确保在正确的分支上
git branch  # 查看当前分支

# 2. 创建或切换到功能分支
git checkout -b feature/my-feature

# 3. 进行开发和提交
git add .
git commit -m "feat: 实现新功能"

# 4. 推送到远程（首次推送需要设置上游）
git push -u origin feature/my-feature

# 后续推送
git push
```

### 合并分支

```bash
# 切换到主分支
git checkout main

# 拉取最新代码
git pull

# 合并功能分支
git merge feature/my-feature

# 推送合并结果
git push
```

## 常见工作流

### 工作流 1: 提交新功能

```bash
# 1. 创建功能分支
git checkout -b feature/add-login

# 2. 开发并提交
git add src/auth/login.py
git commit -m "feat(auth): 实现用户登录功能"

git add tests/test_login.py
git commit -m "test(auth): 添加登录功能测试"

# 3. 推送到远程
git push -u origin feature/add-login

# 4. 创建 Pull Request（在 GitLab/GitHub 上）
```

### 工作流 2: 修复 Bug

```bash
# 1. 从主分支创建修复分支
git checkout main
git pull
git checkout -b fix/parser-null-error

# 2. 修复并提交
git add src/parser.py
git commit -m "fix(parser): 修复空值解析错误

- 添加空值检查
- 更新错误处理逻辑"

# 3. 推送到远程
git push -u origin fix/parser-null-error
```

### 工作流 3: 更新文档

```bash
# 1. 创建文档分支
git checkout -b docs/update-api-docs

# 2. 更新文档
git add docs/api.md
git commit -m "docs(api): 更新 API 接口文档

- 添加认证接口说明
- 更新请求示例
- 修正参数描述"

# 3. 推送
git push -u origin docs/update-api-docs
```

### 工作流 4: 代码重构

```bash
# 1. 创建重构分支
git checkout -b refactor/utils-cleanup

# 2. 重构并提交
git add src/utils/
git commit -m "refactor(utils): 重构工具函数

- 提取公共逻辑
- 改进函数命名
- 添加类型注解"

# 3. 确保测试通过
# 运行测试...

# 4. 推送
git push -u origin refactor/utils-cleanup
```

## 提交前检查

### 检查清单

在提交前，确保：

```bash
# 1. 检查工作区状态
git status

# 2. 查看所有变更
git diff

# 3. 运行测试（如果项目有）
# pytest 或 npm test 等

# 4. 检查代码格式（如果项目有）
# black . 或 prettier --check 等

# 5. 检查是否有敏感信息
git diff | grep -i "password\|secret\|key\|token"

# 6. 确认提交的文件正确
git diff --staged
```

### 撤销操作

```bash
# 撤销工作区的修改（未暂存）
git checkout -- <文件>
# 或
git restore <文件>

# 取消暂存（已 add 但未 commit）
git reset HEAD <文件>
# 或
git restore --staged <文件>

# 撤销最后一次提交（保留修改）
git reset --soft HEAD~1

# 撤销最后一次提交（丢弃修改）
git reset --hard HEAD~1  # 谨慎使用！
```

## 高级功能

### 提交部分文件变更

```bash
# 交互式选择要暂存的代码块
git add -p

# 这会显示每个变更块，您可以选择：
# y - 暂存此块
# n - 不暂存此块
# q - 退出
# s - 分割更大的块
# e - 手动编辑块
```

### 查看提交历史

```bash
# 简洁的单行显示
git log --oneline -10

# 图形化显示分支
git log --oneline --graph --all -20

# 查看特定文件的提交历史
git log --oneline -- <文件路径>

# 查看提交的详细变更
git show <commit-hash>
```

### 比较变更

```bash
# 比较工作区和暂存区
git diff

# 比较暂存区和最后一次提交
git diff --staged

# 比较两个提交
git diff <commit1> <commit2>

# 比较两个分支
git diff main..feature-branch
```

### 暂存当前工作（Stash）

```bash
# 暂存当前修改
git stash

# 暂存并添加描述
git stash save "正在开发的功能，临时保存"

# 查看所有暂存
git stash list

# 恢复最近的暂存
git stash pop

# 恢复指定的暂存
git stash apply stash@{0}

# 删除暂存
git stash drop stash@{0}
```

## 最佳实践

### 提交频率

- ✅ **频繁提交**: 每完成一个小功能或修复就提交
- ✅ **原子性提交**: 每个提交应该是一个完整的、可工作的变更
- ❌ **避免**: 一次提交包含多个不相关的变更

### 提交消息

- ✅ **清晰明确**: 说明做了什么，为什么做
- ✅ **使用现在时**: "添加功能" 而不是 "添加了功能"
- ✅ **首字母大写**: 主题行首字母大写
- ✅ **限制长度**: 主题行不超过 50 字符，正文每行不超过 72 字符
- ❌ **避免**: 模糊的消息如 "修复 bug"、"更新代码"

### 分支命名

- ✅ `feature/功能名称` - 新功能
- ✅ `fix/问题描述` - Bug 修复
- ✅ `docs/文档内容` - 文档更新
- ✅ `refactor/重构内容` - 代码重构
- ✅ `test/测试内容` - 测试相关
- ✅ `chore/任务内容` - 杂项任务

### 提交前检查

1. ✅ 运行测试确保通过
2. ✅ 检查代码格式和 lint
3. ✅ 确认没有提交敏感信息
4. ✅ 确认提交的文件正确
5. ✅ 编写清晰的提交消息

## 常见问题

**问题: 提交了错误的文件怎么办？**

```bash
# 如果还没推送，可以修改最后一次提交
git reset --soft HEAD~1
# 重新选择要提交的文件
git add <正确的文件>
git commit -m "正确的提交消息"
```

**问题: 提交消息写错了怎么办？**

```bash
# 修改最后一次提交的消息
git commit --amend -m "正确的提交消息"

# 如果已推送，需要强制推送（谨慎使用）
git push --force-with-lease
```

**问题: 如何撤销已推送的提交？**

```bash
# 创建新的提交来撤销更改（推荐）
git revert <commit-hash>
git push

# 或回退到指定提交（需要团队协调）
git reset --hard <commit-hash>
git push --force-with-lease  # 谨慎使用！
```

**问题: 如何查看某个文件的提交历史？**

```bash
git log --oneline -- <文件路径>
git log -p -- <文件路径>  # 包含变更内容
```

**问题: 如何查看两个版本之间的差异？**

```bash
git diff <commit1> <commit2>
git diff <commit1>..<commit2>  # 等价写法
```

## 参考资料

- **[Git 工作流详解](references/workflows.md)** - 详细的分支策略和工作流
- **[提交消息指南](references/commit-messages.md)** - 提交消息的完整指南和示例
- **[冲突解决](references/conflict-resolution.md)** - 处理合并冲突的步骤和技巧

## 资源

- **Git 官方文档**: https://git-scm.com/doc
- **约定式提交**: https://www.conventionalcommits.org/
- **Git 教程**: https://git-scm.com/book