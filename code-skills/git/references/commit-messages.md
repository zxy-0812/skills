# 提交消息指南

编写清晰、规范的 Git 提交消息的完整指南。

## 提交消息格式

### 标准格式

```
<类型>(<范围>): <主题>

<正文>

<脚注>
```

### 各部分说明

**类型（Type）**: 必填，说明提交的性质
**范围（Scope）**: 可选，说明影响的范围
**主题（Subject）**: 必填，简短描述（50 字符以内）
**正文（Body）**: 可选，详细说明（72 字符换行）
**脚注（Footer）**: 可选，关联 issue、breaking changes 等

## 类型（Type）

### 主要类型

- **feat**: 新功能
  ```bash
  git commit -m "feat(auth): 添加 JWT 认证"
  ```

- **fix**: Bug 修复
  ```bash
  git commit -m "fix(parser): 修复空值解析错误"
  ```

- **docs**: 文档变更
  ```bash
  git commit -m "docs(readme): 更新安装说明"
  ```

- **style**: 代码格式（不影响代码运行）
  ```bash
  git commit -m "style: 格式化代码，统一缩进"
  ```

- **refactor**: 重构（既不是新功能也不是 bug 修复）
  ```bash
  git commit -m "refactor(utils): 重构字符串处理函数"
  ```

- **perf**: 性能优化
  ```bash
  git commit -m "perf(cache): 优化缓存命中率"
  ```

- **test**: 测试相关
  ```bash
  git commit -m "test(auth): 添加登录功能测试"
  ```

- **chore**: 构建过程或辅助工具的变动
  ```bash
  git commit -m "chore(deps): 更新依赖包版本"
  ```

- **ci**: CI 配置文件和脚本的变更
  ```bash
  git commit -m "ci: 添加 GitHub Actions 工作流"
  ```

### 特殊类型

- **build**: 构建系统或外部依赖的变更
- **revert**: 撤销之前的提交
  ```bash
  git commit -m "revert: 撤销 feat(auth): 添加 JWT 认证"
  ```

## 范围（Scope）

范围应该是受影响的模块或组件。

### 常见范围

```bash
# 按模块
feat(api): 添加用户接口
fix(database): 修复连接池问题
docs(auth): 更新认证文档

# 按文件
feat(login.py): 添加登录功能
fix(parser.py): 修复解析错误

# 按功能
feat(user): 添加用户管理
fix(payment): 修复支付流程
```

## 主题（Subject）

### 规则

1. **使用祈使句，现在时**
   - ✅ "添加功能"
   - ❌ "添加了功能" 或 "添加功能了"

2. **首字母大写**
   - ✅ "Add user authentication"
   - ❌ "add user authentication"

3. **不以句号结尾**
   - ✅ "添加用户认证"
   - ❌ "添加用户认证。"

4. **长度限制在 50 字符以内**

5. **清晰描述做了什么**

### 好的示例

```bash
feat(auth): 添加 JWT token 验证
fix(api): 修复空指针异常
docs(readme): 更新安装步骤
refactor(utils): 提取公共函数
perf(cache): 优化查询性能
```

### 不好的示例

```bash
# 太模糊
fix: 修复 bug
update: 更新代码
change: 修改

# 太长
feat(auth): 添加了一个新的用户认证系统，支持 JWT token 和 refresh token，包括登录、注册、登出功能

# 使用过去时
feat(auth): 添加了 JWT 认证
fix(api): 修复了空指针异常
```

## 正文（Body）

### 何时需要正文

- 提交比较复杂，需要详细说明
- 需要解释"为什么"而不仅仅是"做了什么"
- 有多个相关的变更

### 正文格式

```bash
git commit -m "feat(auth): 添加 JWT 认证" \
           -m "" \
           -m "实现基于 JWT 的用户认证系统：" \
           -m "- 添加 token 生成和验证逻辑" \
           -m "- 实现登录和注册接口" \
           -m "- 添加 token 刷新机制" \
           -m "- 更新 API 文档"
```

### 正文规则

1. **每行不超过 72 字符**
2. **使用空行分隔段落**
3. **使用列表说明多个变更**
4. **解释"为什么"和"如何"**

### 示例

```bash
feat(api): 添加用户认证接口

实现基于 JWT 的用户认证系统，包括：

- 用户登录接口，返回 access token 和 refresh token
- 用户注册接口，支持邮箱和手机号注册
- Token 刷新接口，用于更新过期的 access token
- Token 验证中间件，保护需要认证的接口

这些变更解决了之前缺少统一认证机制的问题，
现在所有需要认证的接口都可以使用统一的中间件。

相关 issue: #123
```

## 脚注（Footer）

### Breaking Changes

```bash
feat(api): 重构用户接口

BREAKING CHANGE: 用户接口 URL 从 /api/users 改为 /api/v2/users
旧的接口将在下个版本中移除。
```

### 关联 Issue

```bash
fix(parser): 修复空值解析错误

修复了当输入为空时导致的解析异常。

Closes #456
Fixes #789
Related to #123
```

### 签名

```bash
feat(auth): 添加 JWT 认证

Signed-off-by: John Doe <john@example.com>
```

## 完整示例

### 示例 1: 简单功能

```bash
feat(auth): 添加用户登录功能
```

### 示例 2: 带正文的功能

```bash
feat(api): 添加用户认证接口

实现基于 JWT 的用户认证系统：
- 添加登录接口，返回 access token
- 添加注册接口，支持邮箱注册
- 实现 token 验证中间件

Closes #123
```

### 示例 3: Bug 修复

```bash
fix(parser): 修复 JSON 解析空值错误

当 JSON 中包含 null 值时，解析器会抛出异常。
现在正确处理 null 值，返回 None。

Fixes #456
```

### 示例 4: 重构

```bash
refactor(utils): 重构字符串处理函数

提取公共的字符串处理逻辑到独立的工具函数：
- 创建 string_utils.py 模块
- 将重复的字符串处理代码提取为函数
- 更新所有调用处使用新函数

这提高了代码的可维护性和复用性。
```

### 示例 5: 性能优化

```bash
perf(cache): 优化缓存命中率

- 实现 LRU 缓存策略
- 增加缓存预热机制
- 优化缓存键的生成算法

性能提升：缓存命中率从 60% 提升到 85%。
```

### 示例 6: Breaking Change

```bash
feat(api): 重构用户接口

将用户相关的所有接口迁移到新的路由结构：
- /api/users -> /api/v2/users
- 更新所有相关的中间件和权限检查
- 添加迁移指南文档

BREAKING CHANGE: 旧的 /api/users 接口将在 v2.0.0 中移除。
请参考迁移指南更新客户端代码。

Migration guide: docs/migration/v2.md
```

## 多文件提交

当一次提交涉及多个文件时，确保提交消息能概括所有变更：

```bash
feat(auth): 实现用户认证系统

包含以下变更：
- 添加认证模型和数据库迁移
- 实现登录和注册接口
- 添加 JWT token 生成和验证
- 创建认证中间件
- 添加单元测试和集成测试
- 更新 API 文档
```

## 提交消息检查清单

在提交前检查：

- [ ] 类型是否正确（feat/fix/docs 等）
- [ ] 范围是否明确（如果有）
- [ ] 主题是否清晰（50 字符以内）
- [ ] 是否使用祈使句、现在时
- [ ] 首字母是否大写
- [ ] 是否以句号结尾（不应该）
- [ ] 正文是否解释了"为什么"（如果需要）
- [ ] 是否关联了相关 issue（如果有）
- [ ] 是否有 breaking changes 说明（如果有）

## 工具和自动化

### Commitizen

使用 Commitizen 交互式生成提交消息：

```bash
# 安装
pip install commitizen

# 使用
cz commit
```

### Git Hooks

使用 pre-commit hook 验证提交消息：

```bash
# .git/hooks/commit-msg
#!/bin/sh
commit_msg=$(cat "$1")
if ! echo "$commit_msg" | grep -qE "^(feat|fix|docs|style|refactor|perf|test|chore|ci|build|revert)(\(.+\))?: .{1,50}$"; then
    echo "提交消息格式不正确！"
    echo "格式: <类型>(<范围>): <主题>"
    exit 1
fi
```

## 参考资源

- **约定式提交规范**: https://www.conventionalcommits.org/
- **Angular 提交指南**: https://github.com/angular/angular/blob/main/CONTRIBUTING.md#commit
- **Commitizen**: https://commitizen-tools.github.io/commitizen/