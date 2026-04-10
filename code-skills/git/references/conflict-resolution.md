# Git 合并冲突解决指南

处理 Git 合并冲突的完整指南和最佳实践。

## 什么是合并冲突

当两个分支对同一文件的同一部分进行了不同的修改，Git 无法自动决定保留哪个版本时，就会产生合并冲突。

## 冲突发生的场景

### 场景 1: 合并分支

```bash
# 主分支修改了文件
git checkout main
# 编辑 file.py
git commit -m "feat: 在主分支添加功能 A"

# 功能分支也修改了同一文件
git checkout feature-branch
# 编辑同一个 file.py 的不同部分
git commit -m "feat: 在功能分支添加功能 B"

# 尝试合并时发生冲突
git checkout main
git merge feature-branch
# 冲突！
```

### 场景 2: 拉取远程更改

```bash
# 本地修改了文件
git add file.py
git commit -m "feat: 本地修改"

# 远程也有新的提交修改了同一文件
git pull
# 冲突！
```

### 场景 3: Rebase

```bash
git checkout feature-branch
git rebase main
# 冲突！
```

## 识别冲突

### Git 状态

```bash
git status
```

输出示例：

```
On branch main
You have unmerged paths.
  (fix conflicts and run "git commit")
  (use "git merge --abort" to abort the merge)

Unmerged paths:
  (use "git add <file>..." to mark resolution)
        both modified:   src/utils.py
        both modified:   tests/test_utils.py
```

### 冲突标记

冲突文件中的标记：

```python
<<<<<<< HEAD
# 当前分支的代码（HEAD）
def function_a():
    return "version A"
=======
# 要合并进来的代码
def function_a():
    return "version B"
>>>>>>> feature-branch
```

标记说明：
- `<<<<<<< HEAD`: 当前分支（通常是您所在的分支）的代码开始
- `=======`: 分隔符
- `>>>>>>> feature-branch`: 要合并的分支的代码结束

## 解决冲突的步骤

### 步骤 1: 查看冲突

```bash
# 查看所有冲突文件
git status

# 查看特定文件的冲突
git diff src/utils.py

# 查看冲突的详细内容
cat src/utils.py
```

### 步骤 2: 编辑冲突文件

手动编辑文件，选择要保留的代码：

**选项 1: 保留当前分支的代码**

```python
# 删除冲突标记，保留 HEAD 的代码
def function_a():
    return "version A"
```

**选项 2: 保留要合并分支的代码**

```python
# 删除冲突标记，保留 feature-branch 的代码
def function_a():
    return "version B"
```

**选项 3: 合并两者**

```python
# 保留两个版本的代码
def function_a():
    return "version A"

def function_b():
    return "version B"
```

**选项 4: 编写新代码**

```python
# 完全重写，结合两个版本的优点
def function_a():
    return "merged version"
```

### 步骤 3: 标记为已解决

```bash
# 标记单个文件为已解决
git add src/utils.py

# 或标记所有已解决的文件
git add .
```

### 步骤 4: 完成合并

```bash
# 提交合并
git commit

# 或使用默认的合并消息
git commit --no-edit
```

## 使用工具解决冲突

### VS Code

1. 打开冲突文件
2. 点击 "Accept Current Change"、"Accept Incoming Change" 或 "Accept Both Changes"
3. 保存文件
4. 运行 `git add` 和 `git commit`

### Git Merge Tool

```bash
# 使用默认的合并工具
git mergetool

# 使用特定的合并工具
git mergetool --tool=vimdiff
git mergetool --tool=meld
git mergetool --tool=kdiff3
```

### 配置合并工具

```bash
# 配置 VS Code 作为合并工具
git config --global merge.tool vscode
git config --global mergetool.vscode.cmd 'code --wait $MERGED'

# 配置 Meld
git config --global merge.tool meld
```

## 常见冲突类型

### 1. 同一行的不同修改

```python
<<<<<<< HEAD
result = calculate(a, b, c)
=======
result = compute(x, y, z)
>>>>>>> feature-branch
```

**解决**: 选择正确的版本或合并逻辑。

### 2. 相邻行的修改

```python
def function():
    line1 = "A"
<<<<<<< HEAD
    line2 = "B"
    line3 = "C"
=======
    line2 = "X"
    line3 = "Y"
>>>>>>> feature-branch
    line4 = "D"
```

**解决**: 通常可以保留两者，调整顺序。

### 3. 一方添加，另一方删除

```python
<<<<<<< HEAD
def new_function():
    return "new"
=======
>>>>>>> feature-branch
```

**解决**: 决定是否保留新函数。

### 4. 双方都添加了内容

```python
def existing_function():
    return "existing"
<<<<<<< HEAD
def function_a():
    return "A"
=======
def function_b():
    return "B"
>>>>>>> feature-branch
```

**解决**: 通常保留两者。

## 高级冲突解决

### 中止合并

如果冲突太复杂，可以中止合并：

```bash
# 中止合并，回到合并前的状态
git merge --abort

# 中止 rebase
git rebase --abort
```

### 使用策略解决冲突

```bash
# 合并时优先使用当前分支的版本
git merge -X ours feature-branch

# 合并时优先使用要合并分支的版本
git merge -X theirs feature-branch
```

### 手动选择版本

```bash
# 完全使用当前分支的版本
git checkout --ours src/utils.py
git add src/utils.py

# 完全使用要合并分支的版本
git checkout --theirs src/utils.py
git add src/utils.py
```

### 三路合并

查看共同祖先：

```bash
# 查看合并基础
git merge-base HEAD feature-branch

# 查看三个版本的差异
git diff HEAD...feature-branch
```

## 预防冲突

### 1. 频繁同步

```bash
# 定期从主分支更新功能分支
git checkout feature-branch
git fetch origin
git merge origin/main
# 或
git rebase origin/main
```

### 2. 小粒度提交

- 频繁提交，每次提交只做小的变更
- 避免长时间不合并主分支的更改

### 3. 沟通协调

- 团队成员之间沟通，避免同时修改同一文件
- 使用代码审查，提前发现潜在的冲突

### 4. 合理的文件组织

- 将相关功能组织到不同文件
- 避免在大型文件中进行大量修改

## 冲突解决最佳实践

### 1. 理解冲突

- 不要盲目选择版本
- 理解两个版本的意图
- 必要时与原作者沟通

### 2. 测试解决后的代码

```bash
# 解决冲突后
git add .
git commit

# 运行测试
pytest  # 或项目的测试命令

# 如果测试失败，继续修复
```

### 3. 保持代码质量

- 解决冲突时保持代码风格一致
- 确保解决后的代码逻辑正确
- 添加必要的注释

### 4. 提交消息

```bash
# 使用清晰的提交消息
git commit -m "merge: 解决与 feature-branch 的冲突

- 合并了用户认证相关的更改
- 保留了两个分支的功能
- 更新了相关测试"
```

## 复杂场景

### 多个文件冲突

```bash
# 逐个解决
git status  # 查看所有冲突文件

# 解决第一个
vim src/file1.py
git add src/file1.py

# 解决第二个
vim src/file2.py
git add src/file2.py

# 完成后提交
git commit
```

### Rebase 冲突

```bash
# 开始 rebase
git rebase main

# 如果发生冲突
# 1. 解决冲突
vim src/file.py
git add src/file.py

# 2. 继续 rebase
git rebase --continue

# 如果还有更多冲突，重复上述步骤

# 如果想中止
git rebase --abort
```

### 合并多个分支

```bash
# 合并多个分支时可能有多处冲突
git checkout main
git merge feature-a feature-b feature-c

# 逐个解决冲突
# ...
```

## 工具推荐

### 可视化工具

- **VS Code**: 内置冲突解决界面
- **Meld**: 跨平台的差异和合并工具
- **KDiff3**: 三路合并工具
- **Beyond Compare**: 商业合并工具

### 命令行工具

- **vimdiff**: Vim 的差异查看模式
- **emerge**: Emacs 的合并工具

## 检查清单

解决冲突后检查：

- [ ] 所有冲突标记已移除
- [ ] 代码可以正常编译/运行
- [ ] 测试通过
- [ ] 代码风格一致
- [ ] 逻辑正确
- [ ] 已标记所有冲突文件为已解决
- [ ] 已提交合并

## 参考资源

- **Git 官方文档 - 合并冲突**: https://git-scm.com/book/en/v2/Git-Tools-Advanced-Merging
- **Atlassian 冲突解决指南**: https://www.atlassian.com/git/tutorials/using-branches/merge-conflicts