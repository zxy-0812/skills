---
description: 深入分析和排查 SGLang 项目中的各种问题，包括环境配置、SGLang 报错、vLLM 报错、脚本报错等。通过系统化的诊断流程、代码分析和测试验证来定位和修复问题。
alwaysApply: false
---
# 问题排查与调试

系统化的问题排查和调试技能，帮助您深入分析并解决 SGLang 项目中的各种问题。

## 何时使用

**在以下情况使用此 skill:**
- 环境配置异常（CUDA、依赖包、系统配置等）
- SGLang 运行时错误（服务器启动失败、推理错误、内存问题等）
- vLLM 相关错误（兼容性问题、性能问题等）
- Python 脚本执行错误（导入错误、语法错误、运行时异常等）
- 需要深入代码分析定位根本原因
- 修复后需要编写测试验证

**改用其他方案当:**
- 需要性能优化（使用性能分析 skill）
- 需要代码重构（使用重构 skill）
- 需要添加新功能（使用开发 skill）

## 快速开始

### 问题排查工作流

```
1. 收集错误信息
   ↓
2. 环境诊断
   ↓
3. 代码分析
   ↓
4. 定位根本原因
   ↓
5. 实施修复
   ↓
6. 编写测试
   ↓
7. 验证修复
```

### 基本诊断命令

```bash
# 检查环境配置
python -m sglang.check_env

# 检查 Python 版本
python --version

# 检查已安装的包
pip list | grep sglang
pip list | grep vllm

# 检查 CUDA 环境
nvidia-smi
python -c "import torch; print(torch.cuda.is_available())"

# 检查日志
tail -f /path/to/logfile
```

## 核心功能

### 1. 环境配置问题排查

#### 检查清单

**Python 环境:**
- [ ] Python 版本 >= 3.10
- [ ] 虚拟环境已激活（如使用）
- [ ] 依赖包版本正确

**CUDA/GPU 环境:**
- [ ] CUDA 驱动已安装
- [ ] CUDA 版本兼容
- [ ] GPU 可见且可用
- [ ] PyTorch 能检测到 CUDA

**依赖包:**
- [ ] sglang 已正确安装
- [ ] sgl_kernel 已编译
- [ ] flashinfer 相关包正常
- [ ] transformers 版本兼容

#### 诊断步骤

```bash
# 1. 运行环境检查工具
python -m sglang.check_env

# 2. 检查特定包版本
python -c "import sglang; print(sglang.__version__)"
python -c "import torch; print(torch.__version__, torch.cuda.is_available())"

# 3. 检查 CUDA 环境
nvidia-smi
nvcc --version

# 4. 检查环境变量
env | grep -E "CUDA|PATH|LD_LIBRARY"

# 5. 验证安装
python -c "import sglang; from sglang import Runtime"
```

#### 常见问题

**问题: ModuleNotFoundError: No module named 'sgl_kernel'**

```bash
# 诊断
python -c "import sgl_kernel" 2>&1

# 解决方案
# 1. 重新编译内核
cd sgl-kernel
make clean && make

# 2. 重新安装
pip install -e "python" --force-reinstall --no-cache-dir
```

**问题: CUDA not available**

```bash
# 诊断
python -c "import torch; print(torch.cuda.is_available())"
nvidia-smi

# 解决方案
# 1. 检查驱动
nvidia-smi

# 2. 检查 CUDA_HOME
echo $CUDA_HOME
export CUDA_HOME=/usr/local/cuda

# 3. 重新安装 PyTorch（如需要）
pip install torch --index-url https://download.pytorch.org/whl/cu118
```

### 2. SGLang 报错排查

#### 错误分类

**启动错误:**
- 模型加载失败
- 端口占用
- 配置错误
- 内存不足

**运行时错误:**
- 推理失败
- 内存溢出（OOM）
- 超时错误
- 序列长度超限

**API 错误:**
- 请求格式错误
- 参数验证失败
- 连接错误

#### 诊断流程

```bash
# 1. 启用详细日志
export SGLANG_LOGGING_LEVEL=DEBUG
python -m sglang.launch_server --model-path <model> --port 30000

# 2. 检查服务器状态
curl http://localhost:30000/health

# 3. 查看错误堆栈
# 在日志中查找完整的 traceback

# 4. 检查资源使用
watch -n 1 nvidia-smi
```

#### 代码分析步骤

1. **定位错误位置**
   - 查看完整堆栈跟踪
   - 找到错误发生的文件和行号
   - 检查相关函数调用链

2. **分析错误上下文**
   - 查看错误发生时的输入参数
   - 检查相关配置
   - 查看相关代码逻辑

3. **检查依赖关系**
   - 检查调用的其他模块
   - 验证数据流
   - 检查边界条件

4. **查找类似问题**
   - 搜索代码库中的类似错误处理
   - 查看测试用例
   - 检查文档和 issue

#### 示例：分析 OOM 错误

```python
# 错误信息
# RuntimeError: CUDA out of memory

# 1. 定位代码位置
# 在 sglang/srt/ 中搜索内存分配相关代码

# 2. 分析内存使用
import torch
print(f"GPU memory allocated: {torch.cuda.memory_allocated() / 1e9:.2f} GB")
print(f"GPU memory reserved: {torch.cuda.memory_reserved() / 1e9:.2f} GB")

# 3. 检查配置
# 查看 --gpu-memory-utilization 参数
# 查看 --max-model-len 参数

# 4. 修复方案
# - 减少 gpu-memory-utilization
# - 减少 max-model-len
# - 启用量化
# - 使用张量并行
```

### 3. vLLM 报错排查

#### 常见错误类型

**兼容性错误:**
- API 不兼容
- 模型格式不兼容
- 版本冲突

**性能问题:**
- 吞吐量低
- 延迟高
- 资源利用率低

#### 诊断方法

```bash
# 1. 检查 vLLM 版本
pip show vllm

# 2. 检查兼容性
python -c "import vllm; print(vllm.__version__)"

# 3. 对比 SGLang 和 vLLM 的行为
# 使用相同的模型和参数分别测试

# 4. 查看 vLLM 日志
export VLLM_LOGGING_LEVEL=DEBUG
```

### 4. 脚本报错排查

#### Python 脚本错误

**导入错误:**
```python
# 诊断
python -c "import <module>"

# 检查 PYTHONPATH
import sys
print(sys.path)

# 解决方案
export PYTHONPATH=/path/to/project:$PYTHONPATH
# 或
pip install -e .
```

**语法错误:**
```bash
# 使用 linter 检查
ruff check <file>
black --check <file>

# 使用 Python 编译器检查
python -m py_compile <file>
```

**运行时错误:**
```python
# 启用详细错误信息
import traceback
try:
    # 你的代码
    pass
except Exception as e:
    traceback.print_exc()
    print(f"Error type: {type(e).__name__}")
    print(f"Error message: {str(e)}")
```

## 深入代码分析

### 代码分析工作流

1. **理解错误上下文**
   ```python
   # 查看错误发生的完整调用栈
   import traceback
   traceback.print_exc()
   ```

2. **定位相关代码**
   ```bash
   # 使用 grep 搜索相关代码
   grep -r "function_name" python/sglang/
   
   # 使用 codebase_search 进行语义搜索
   # 在 Cursor 中使用代码搜索功能
   ```

3. **分析数据流**
   - 追踪输入数据
   - 检查中间状态
   - 验证输出结果

4. **检查边界条件**
   - 空值处理
   - 类型检查
   - 范围验证

5. **查看测试用例**
   ```bash
   # 查找相关测试
   find test/ -name "*test*.py" -exec grep -l "related_function" {} \;
   ```

### 使用调试工具

```python
# 使用 pdb 调试
import pdb
pdb.set_trace()

# 使用 logging
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.debug("Debug message")

# 使用断言验证假设
assert condition, "Error message"
```

## 修复与测试

### 修复流程

1. **理解问题根源**
   - 确认根本原因
   - 理解影响范围
   - 评估修复方案

2. **实施修复**
   - 修改代码
   - 保持代码风格一致
   - 添加必要的注释

3. **编写测试**
   - 创建最小复现用例
   - 编写单元测试
   - 编写集成测试（如需要）

4. **验证修复**
   - 运行测试
   - 确保测试通过
   - 验证没有引入回归

### 测试编写指南

#### 单元测试示例

```python
import unittest
from sglang import Runtime

class TestFix(unittest.TestCase):
    def setUp(self):
        """设置测试环境"""
        self.runtime = Runtime()
    
    def test_fixed_issue(self):
        """测试修复的问题"""
        # 最小复现用例
        result = self.runtime.some_function(input_data)
        
        # 验证结果
        self.assertIsNotNone(result)
        self.assertEqual(result.expected_field, expected_value)
    
    def test_edge_cases(self):
        """测试边界情况"""
        # 测试空值
        result = self.runtime.some_function(None)
        self.assertIsNone(result)
        
        # 测试边界值
        result = self.runtime.some_function(edge_case_value)
        self.assertIsNotNone(result)
    
    def tearDown(self):
        """清理测试环境"""
        self.runtime.cleanup()
```

#### 运行测试

```bash
# 运行单个测试文件
python test/test_fix.py

# 运行特定测试
python test/test_fix.py TestFix.test_fixed_issue

# 运行测试套件
python test/run_suite.py --suite per-commit-1-gpu

# 使用 pytest
pytest test/test_fix.py -v
```

#### 测试验证清单

- [ ] 测试能够复现原始问题
- [ ] 修复后测试通过
- [ ] 没有引入新的错误
- [ ] 边界情况已覆盖
- [ ] 测试代码清晰易懂
- [ ] 测试运行时间合理

## 最佳实践

### 问题排查

1. **系统化方法**
   - 从简单到复杂
   - 逐步缩小问题范围
   - 记录排查过程

2. **充分利用工具**
   - 使用环境检查工具
   - 启用详细日志
   - 使用调试器

3. **文档化**
   - 记录错误信息
   - 记录排查步骤
   - 记录解决方案

### 代码分析

1. **深入理解**
   - 阅读相关代码
   - 理解设计意图
   - 查看相关文档

2. **验证假设**
   - 使用断言
   - 添加日志
   - 编写测试

3. **保持简洁**
   - 最小化修改
   - 保持代码风格
   - 添加必要注释

### 测试编写

1. **测试驱动**
   - 先写测试复现问题
   - 修复后验证测试通过
   - 确保测试覆盖关键路径

2. **测试质量**
   - 测试应该独立
   - 测试应该可重复
   - 测试应该快速

3. **测试维护**
   - 保持测试更新
   - 删除过时测试
   - 改进测试覆盖

## 参考资料

- **[环境配置排查](references/environment-troubleshooting.md)** - 详细的环境配置问题排查指南
- **[SGLang 错误分析](references/sglang-errors.md)** - SGLang 常见错误和解决方案
- **[代码分析技巧](references/code-analysis.md)** - 深入代码分析的技巧和方法
- **[测试编写指南](references/testing-guide.md)** - 编写高质量测试的完整指南

## 资源

- **SGLang 文档**: https://sglang.readthedocs.io/
- **GitHub Issues**: https://github.com/sgl-project/sglang/issues
- **环境检查工具**: `python -m sglang.check_env`
- **测试文档**: `test/README.md`