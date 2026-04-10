# Git 工作流详解

详细说明各种 Git 工作流策略和使用场景。

## Git Flow

经典的 Git Flow 工作流，适合有明确发布周期的项目。

### 分支结构

```
main (master)
  └── develop
       ├── feature/user-auth
       ├── feature/payment
       ├── release/v1.2.0
       └── hotfix/critical-bug
```

### 分支说明

- **main**: 生产环境代码，只接受来自 release 或 hotfix 的合并
- **develop**: 开发主分支，所有功能分支从此创建
- **feature/***: 功能分支，从 develop 创建，完成后合并回 develop
- **release/***: 发布分支，从 develop 创建，用于准备新版本
- **hotfix/***: 紧急修复分支，从 main 创建，修复后合并到 main 和 develop

### 工作流示例

```bash
# 1. 创建功能分支
git checkout develop
git pull
git checkout -b feature/user-authentication

# 2. 开发和提交
git add .
git commit -m "feat(auth): 实现用户认证"

# 3. 完成功能，合并回 develop
git checkout develop
git pull
git merge feature/user-authentication
git push

# 4. 创建发布分支
git checkout -b release/v1.2.0
# 进行版本号更新、测试等
git commit -m "chore: 更新版本号到 1.2.0"
git push

# 5. 发布后合并到 main
git checkout main
git merge release/v1.2.0
git tag v1.2.0
git push --tags

# 6. 合并回 develop
git checkout develop
git merge release/v1.2.0
git push
```

## GitHub Flow

简化的 Git Flow，适合持续部署的项目。

### 分支结构

```
main
  ├── feature/login
  ├── feature/dashboard
  └── fix/bug-123
```

### 工作流

1. 从 main 创建功能分支
2. 在分支上开发和提交
3. 创建 Pull Request
4. 代码审查通过后合并到 main
5. 立即部署

```bash
# 1. 创建分支
git checkout main
git pull
git checkout -b feature/new-feature

# 2. 开发
git add .
git commit -m "feat: 新功能"

# 3. 推送并创建 PR
git push -u origin feature/new-feature

# 4. PR 合并后，删除本地分支
git checkout main
git pull
git branch -d feature/new-feature
```

## GitLab Flow

结合环境分支的 Git Flow 变体。

### 分支结构

```
production
  └── pre-production
       └── main
            ├── feature/feature-1
            └── feature/feature-2
```

### 工作流

```bash
# 1. 从 main 创建功能分支
git checkout main
git pull
git checkout -b feature/new-feature

# 2. 开发和提交
git commit -m "feat: 新功能"
git push

# 3. 合并到 main（通过 Merge Request）
# 4. 合并到 pre-production（测试环境）
# 5. 合并到 production（生产环境）
```

## 单分支工作流

适合小型项目或个人项目。

```bash
# 直接在 main 分支上工作
git checkout main
git pull

# 开发
git add .
git commit -m "feat: 新功能"
git push
```

## 功能分支工作流

每个功能使用独立分支，完成后合并。

```bash
# 创建功能分支
git checkout -b feature/feature-name

# 开发
git add .
git commit -m "feat: 功能描述"

# 完成后合并
git checkout main
git merge feature/feature-name
git push

# 删除功能分支
git branch -d feature/feature-name
```

## 选择合适的工作流

**使用 Git Flow 当:**
- 项目有明确的发布周期
- 需要维护多个版本
- 团队较大，需要严格的分支管理

**使用 GitHub Flow 当:**
- 持续部署
- 团队较小
- 需要快速迭代

**使用单分支工作流当:**
- 个人项目
- 小型团队
- 不需要复杂的分支管理

## 最佳实践

### 分支命名

```bash
# 功能分支
feature/user-authentication
feature/add-payment-gateway

# 修复分支
fix/login-error
fix/memory-leak

# 发布分支
release/v1.2.0
release/2024-01-15

# 热修复分支
hotfix/critical-security-fix
hotfix/database-connection

# 文档分支
docs/update-api-docs
docs/add-installation-guide
```

### 保持分支同步

```bash
# 定期从主分支更新功能分支
git checkout feature/my-feature
git fetch origin
git merge origin/main
# 或使用 rebase（保持线性历史）
git rebase origin/main
```

### 清理分支

```bash
# 删除已合并的本地分支
git branch --merged | grep -v "\*\|main\|develop" | xargs -n 1 git branch -d

# 删除远程已合并的分支
git branch -r --merged | grep -v "\*\|main\|develop" | sed 's/origin\///' | xargs -n 1 git push origin --delete
```