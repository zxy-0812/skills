# 代码分析技巧

深入代码分析的技巧和方法，帮助您快速定位问题根源。

## 目录

- 代码搜索策略
- 调用链分析
- 数据流追踪
- 依赖关系分析
- 边界条件检查
- 调试工具使用

## 代码搜索策略

### 1. 基于错误信息搜索

```bash
# 搜索错误消息
grep -r "error message" python/sglang/

# 搜索错误类型
grep -r "RuntimeError\|ValueError\|TypeError" python/sglang/

# 搜索函数名
grep -r "function_name" python/sglang/
```

### 2. 基于文件路径搜索

```bash
# 从堆栈跟踪中找到文件
# 例如: File "python/sglang/srt/engine.py", line 123

# 查看相关文件
cat python/sglang/srt/engine.py

# 查看相关函数
grep -A 20 "def function_name" python/sglang/srt/engine.py
```

### 3. 语义搜索

在 Cursor 中使用代码搜索功能：

```python
# 搜索问题: "How does SGLang handle memory allocation?"
# 搜索问题: "Where is the OOM error raised?"
# 搜索问题: "How are sequences batched together?"
```

### 4. 基于导入关系搜索

```python
# 找到导入的模块
# 例如: from sglang.srt.engine import Engine

# 搜索使用该模块的地方
grep -r "from sglang.srt.engine import\|import.*Engine" python/
```

## 调用链分析

### 1. 理解调用关系

```python
# 示例：追踪函数调用
def function_a():
    function_b()

def function_b():
    function_c()

def function_c():
    raise ValueError("Error here")

# 使用 traceback 查看调用链
import traceback
try:
    function_a()
except Exception as e:
    traceback.print_exc()
```

### 2. 绘制调用图

```python
# 使用工具分析调用关系
# 1. 阅读代码，手动追踪
# 2. 使用 IDE 的"查找引用"功能
# 3. 使用静态分析工具

# 示例：分析函数调用
def analyze_calls(function_name):
    # 查找所有调用该函数的地方
    import ast
    import os
    
    calls = []
    for root, dirs, files in os.walk('python/sglang'):
        for file in files:
            if file.endswith('.py'):
                path = os.path.join(root, file)
                with open(path, 'r') as f:
                    try:
                        tree = ast.parse(f.read())
                        for node in ast.walk(tree):
                            if isinstance(node, ast.Call):
                                if isinstance(node.func, ast.Name):
                                    if node.func.id == function_name:
                                        calls.append(path)
                    except:
                        pass
    return calls
```

### 3. 运行时追踪

```python
# 使用装饰器追踪函数调用
import functools
import traceback

def trace_calls(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        print(f"Calling {func.__name__} with args={args}, kwargs={kwargs}")
        try:
            result = func(*args, **kwargs)
            print(f"{func.__name__} returned: {result}")
            return result
        except Exception as e:
            print(f"{func.__name__} raised: {e}")
            traceback.print_exc()
            raise
    return wrapper

# 使用
@trace_calls
def my_function(x, y):
    return x + y
```

## 数据流追踪

### 1. 追踪数据变化

```python
# 添加日志追踪数据
def process_data(data):
    print(f"Input data: {data}")
    
    # 步骤 1
    data = step1(data)
    print(f"After step1: {data}")
    
    # 步骤 2
    data = step2(data)
    print(f"After step2: {data}")
    
    return data
```

### 2. 检查中间状态

```python
# 在关键点检查数据
def critical_function(input_data):
    # 检查输入
    assert input_data is not None, "Input is None"
    assert isinstance(input_data, dict), "Input must be dict"
    
    # 处理
    intermediate = process(input_data)
    
    # 检查中间结果
    assert intermediate is not None, "Intermediate result is None"
    print(f"Intermediate: {intermediate}")
    
    # 继续处理
    result = finalize(intermediate)
    
    return result
```

### 3. 验证数据格式

```python
# 验证数据结构
def validate_data(data, schema):
    """验证数据是否符合预期格式"""
    if not isinstance(data, dict):
        raise TypeError(f"Expected dict, got {type(data)}")
    
    for key, expected_type in schema.items():
        if key not in data:
            raise KeyError(f"Missing key: {key}")
        if not isinstance(data[key], expected_type):
            raise TypeError(
                f"Key '{key}' expected {expected_type}, "
                f"got {type(data[key])}"
            )
    
    return True
```

## 依赖关系分析

### 1. 分析模块依赖

```python
# 查看模块导入
import ast
import os

def analyze_imports(file_path):
    """分析文件的导入依赖"""
    with open(file_path, 'r') as f:
        tree = ast.parse(f.read())
    
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            module = node.module
            for alias in node.names:
                imports.append(f"{module}.{alias.name}")
    
    return imports
```

### 2. 检查循环依赖

```python
# 检测循环依赖
def check_circular_dependency(module_graph):
    """检查模块图中是否有循环依赖"""
    visited = set()
    rec_stack = set()
    
    def has_cycle(node):
        visited.add(node)
        rec_stack.add(node)
        
        for neighbor in module_graph.get(node, []):
            if neighbor not in visited:
                if has_cycle(neighbor):
                    return True
            elif neighbor in rec_stack:
                return True
        
        rec_stack.remove(node)
        return False
    
    for node in module_graph:
        if node not in visited:
            if has_cycle(node):
                return True
    return False
```

### 3. 理解依赖版本

```bash
# 检查依赖版本
pip show <package>

# 检查依赖树
pip list --format=tree

# 检查版本冲突
pip check
```

## 边界条件检查

### 1. 空值处理

```python
# 检查空值
def safe_function(data):
    if data is None:
        raise ValueError("Data cannot be None")
    
    if isinstance(data, (list, dict, str)) and len(data) == 0:
        raise ValueError("Data cannot be empty")
    
    # 处理数据
    return process(data)
```

### 2. 类型检查

```python
# 使用类型提示和检查
from typing import List, Dict, Optional

def typed_function(
    items: List[str],
    config: Dict[str, int],
    optional: Optional[str] = None
) -> str:
    # 运行时类型检查
    if not isinstance(items, list):
        raise TypeError(f"Expected list, got {type(items)}")
    
    if not all(isinstance(item, str) for item in items):
        raise TypeError("All items must be strings")
    
    # 处理
    return process(items, config, optional)
```

### 3. 范围验证

```python
# 验证数值范围
def validate_range(value, min_val, max_val):
    if not (min_val <= value <= max_val):
        raise ValueError(
            f"Value {value} out of range [{min_val}, {max_val}]"
        )
    return value

# 验证序列长度
def validate_sequence_length(seq, max_len):
    if len(seq) > max_len:
        raise ValueError(
            f"Sequence length {len(seq)} exceeds maximum {max_len}"
        )
    return seq
```

### 4. 边界测试

```python
# 测试边界条件
def test_boundaries():
    # 最小值
    result = function(0)
    assert result is not None
    
    # 最大值
    result = function(MAX_VALUE)
    assert result is not None
    
    # 空值
    try:
        result = function(None)
        assert False, "Should raise error"
    except ValueError:
        pass
    
    # 负值
    try:
        result = function(-1)
        assert False, "Should raise error"
    except ValueError:
        pass
```

## 调试工具使用

### 1. 使用 pdb

```python
import pdb

def debug_function():
    # 设置断点
    pdb.set_trace()
    
    # 执行代码
    result = process_data()
    
    return result

# pdb 常用命令:
# n (next): 执行下一行
# s (step): 进入函数
# c (continue): 继续执行
# l (list): 显示代码
# p variable: 打印变量
# pp variable: 美化打印
# w (where): 显示调用栈
# u (up): 向上移动栈帧
# d (down): 向下移动栈帧
```

### 2. 使用 logging

```python
import logging

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('debug.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def debug_function():
    logger.debug("Entering function")
    logger.debug(f"Input: {input_data}")
    
    try:
        result = process(input_data)
        logger.debug(f"Result: {result}")
        return result
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        raise
```

### 3. 使用断言

```python
def validated_function(data):
    # 前置条件
    assert data is not None, "Data cannot be None"
    assert isinstance(data, dict), "Data must be dict"
    assert 'key' in data, "Data must contain 'key'"
    
    # 处理
    result = process(data)
    
    # 后置条件
    assert result is not None, "Result cannot be None"
    assert isinstance(result, str), "Result must be string"
    
    return result
```

### 4. 使用性能分析

```python
import cProfile
import pstats
import io

def profile_function():
    profiler = cProfile.Profile()
    profiler.enable()
    
    # 你的代码
    result = expensive_function()
    
    profiler.disable()
    
    # 分析结果
    s = io.StringIO()
    stats = pstats.Stats(profiler, stream=s)
    stats.sort_stats('cumulative')
    stats.print_stats(20)
    
    print(s.getvalue())
    
    return result
```

## 代码阅读技巧

### 1. 自顶向下阅读

```python
# 从入口点开始
# 1. 找到主函数或入口点
# 2. 理解整体流程
# 3. 深入细节

# 示例
def main():
    # 1. 初始化
    engine = Engine()
    
    # 2. 处理请求
    result = engine.process(request)
    
    # 3. 返回结果
    return result
```

### 2. 自底向上阅读

```python
# 从具体实现开始
# 1. 找到核心函数
# 2. 理解实现细节
# 3. 向上理解调用关系

# 示例
def core_function(data):
    # 核心逻辑
    return processed_data

def wrapper_function(data):
    # 包装核心函数
    return core_function(data)

def main():
    # 使用包装函数
    return wrapper_function(data)
```

### 3. 关注关键路径

```python
# 识别关键执行路径
# 1. 正常流程
# 2. 错误处理
# 3. 边界情况

def key_function():
    # 正常路径
    if condition:
        return normal_process()
    
    # 错误处理
    elif error_condition:
        return handle_error()
    
    # 边界情况
    else:
        return handle_edge_case()
```

## 理解代码意图

### 1. 阅读注释和文档

```python
def function_with_docstring(param1, param2):
    """
    函数说明
    
    Args:
        param1: 参数1的说明
        param2: 参数2的说明
    
    Returns:
        返回值的说明
    
    Raises:
        ValueError: 当参数无效时
    
    Example:
        >>> function_with_docstring("value1", "value2")
        "result"
    """
    # 实现
    pass
```

### 2. 查看测试用例

```python
# 测试用例展示了函数的预期行为
def test_function():
    # 正常情况
    result = function("input")
    assert result == "expected_output"
    
    # 边界情况
    result = function("")
    assert result == "empty_output"
    
    # 错误情况
    with pytest.raises(ValueError):
        function(None)
```

### 3. 查看相关 Issue 和 PR

```bash
# 在 GitHub 上搜索相关 Issue
# 查看代码变更历史
git log --oneline --grep="keyword"
git show <commit-hash>
```

## 实践建议

### 1. 系统化方法

- 从错误信息开始
- 追踪到具体代码
- 理解上下文
- 验证假设

### 2. 记录分析过程

```python
# 记录分析过程
"""
问题: OOM 错误
位置: python/sglang/srt/engine.py:123
分析:
  1. 检查内存分配代码
  2. 发现批次大小过大
  3. 检查配置参数
  4. 发现 max-num-seqs 设置过高
解决方案:
  减少 max-num-seqs 参数
"""
```

### 3. 验证理解

```python
# 通过测试验证理解
def test_understanding():
    # 测试你的理解是否正确
    result = function(input)
    assert result == expected
```

### 4. 寻求帮助

- 查看文档
- 搜索 Issues
- 询问社区
- 阅读相关代码