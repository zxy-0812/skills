# 测试编写指南

编写高质量测试的完整指南，确保修复后的代码正确且稳定。

## 目录

- 测试类型
- 测试结构
- 编写测试
- 运行测试
- 测试最佳实践
- 测试示例

## 测试类型

### 1. 单元测试

测试单个函数或方法：

```python
import unittest

class TestFunction(unittest.TestCase):
    def test_basic_functionality(self):
        result = my_function("input")
        self.assertEqual(result, "expected")
```

### 2. 集成测试

测试多个组件协作：

```python
class TestIntegration(unittest.TestCase):
    def test_end_to_end(self):
        # 测试完整流程
        engine = Engine()
        result = engine.process(request)
        self.assertIsNotNone(result)
```

### 3. 回归测试

测试修复的问题不再出现：

```python
class TestRegression(unittest.TestCase):
    def test_fixed_issue(self):
        # 复现原始问题
        # 验证修复后不再出现
        result = fixed_function(problematic_input)
        self.assertIsNotNone(result)
```

## 测试结构

### 基本结构

```python
import unittest
from sglang import Runtime

class TestFeature(unittest.TestCase):
    """测试功能描述"""
    
    def setUp(self):
        """每个测试前的设置"""
        self.runtime = Runtime()
        # 初始化测试环境
    
    def tearDown(self):
        """每个测试后的清理"""
        self.runtime.cleanup()
        # 清理资源
    
    def test_case_1(self):
        """测试用例1描述"""
        # 测试代码
        pass
    
    def test_case_2(self):
        """测试用例2描述"""
        # 测试代码
        pass

if __name__ == "__main__":
    unittest.main()
```

### 使用 pytest

```python
import pytest

class TestFeature:
    @pytest.fixture
    def runtime(self):
        """测试 fixture"""
        runtime = Runtime()
        yield runtime
        runtime.cleanup()
    
    def test_case_1(self, runtime):
        """测试用例1"""
        result = runtime.function()
        assert result is not None
```

## 编写测试

### 1. 最小复现用例

```python
def test_minimal_reproduce():
    """最小复现原始问题"""
    # 使用最简单的输入复现问题
    input_data = "minimal_input"
    
    # 执行操作
    result = function(input_data)
    
    # 验证结果
    assert result is not None
    assert result == expected_output
```

### 2. 正常情况测试

```python
def test_normal_case(self):
    """测试正常情况"""
    # 正常输入
    input_data = {
        "prompt": "Hello",
        "max_tokens": 10
    }
    
    # 执行
    result = self.runtime.generate(input_data)
    
    # 验证
    self.assertIsNotNone(result)
    self.assertIn("text", result)
    self.assertGreater(len(result["text"]), 0)
```

### 3. 边界情况测试

```python
def test_edge_cases(self):
    """测试边界情况"""
    # 空输入
    result = self.runtime.generate({"prompt": ""})
    self.assertIsNotNone(result)
    
    # 最大长度
    long_prompt = "A" * 10000
    result = self.runtime.generate({
        "prompt": long_prompt,
        "max_tokens": 1
    })
    self.assertIsNotNone(result)
    
    # 最小值
    result = self.runtime.generate({
        "prompt": "Hello",
        "max_tokens": 1
    })
    self.assertIsNotNone(result)
```

### 4. 错误情况测试

```python
def test_error_cases(self):
    """测试错误情况"""
    # None 输入
    with self.assertRaises(ValueError):
        self.runtime.generate(None)
    
    # 无效参数
    with self.assertRaises(ValueError):
        self.runtime.generate({
            "prompt": "Hello",
            "max_tokens": -1
        })
    
    # 缺少必需参数
    with self.assertRaises(KeyError):
        self.runtime.generate({})
```

### 5. 性能测试

```python
import time

def test_performance(self):
    """测试性能"""
    start = time.time()
    
    # 执行操作
    result = self.runtime.generate({
        "prompt": "Hello",
        "max_tokens": 100
    })
    
    elapsed = time.time() - start
    
    # 验证性能
    self.assertLess(elapsed, 1.0, "Should complete in < 1 second")
    self.assertIsNotNone(result)
```

## 运行测试

### 运行单个测试文件

```bash
# 使用 unittest
python test/test_feature.py

# 使用 pytest
pytest test/test_feature.py

# 运行特定测试
python test/test_feature.py TestFeature.test_case_1
pytest test/test_feature.py::TestFeature::test_case_1
```

### 运行测试套件

```bash
# SGLang 测试套件
cd test/srt
python run_suite.py --suite per-commit-1-gpu

# 运行所有测试
pytest test/

# 运行特定目录
pytest test/srt/
```

### 测试选项

```bash
# 详细输出
pytest -v test/

# 显示打印输出
pytest -s test/

# 只运行失败的测试
pytest --lf test/

# 运行到第一个失败
pytest -x test/

# 并行运行
pytest -n auto test/
```

## 测试最佳实践

### 1. 测试独立性

```python
# ✅ 好的：每个测试独立
class TestIndependent(unittest.TestCase):
    def setUp(self):
        self.runtime = Runtime()  # 每个测试创建新实例
    
    def test_1(self):
        # 不依赖其他测试
        pass
    
    def test_2(self):
        # 不依赖其他测试
        pass

# ❌ 避免：测试之间依赖
class TestDependent(unittest.TestCase):
    def test_1(self):
        self.result = function()  # 设置状态
    
    def test_2(self):
        # 依赖 test_1 的结果
        use(self.result)  # 可能失败如果 test_1 失败
```

### 2. 测试可重复性

```python
# ✅ 好的：使用固定输入
def test_deterministic(self):
    input_data = "fixed_input"
    result = function(input_data)
    self.assertEqual(result, "expected_output")

# ❌ 避免：使用随机数据
def test_random(self):
    import random
    input_data = random.randint(0, 100)  # 每次不同
    result = function(input_data)
    # 结果可能不同
```

### 3. 测试清晰性

```python
# ✅ 好的：清晰的测试名称和结构
def test_generate_with_valid_prompt_returns_text(self):
    """测试：使用有效提示生成文本"""
    result = self.runtime.generate({
        "prompt": "Hello",
        "max_tokens": 10
    })
    self.assertIn("text", result)
    self.assertGreater(len(result["text"]), 0)

# ❌ 避免：模糊的测试
def test_1(self):
    # 不清楚测试什么
    result = function()
    assert result
```

### 4. 测试覆盖

```python
# 覆盖主要路径
def test_main_path(self):
    # 正常流程
    pass

# 覆盖错误路径
def test_error_path(self):
    # 错误处理
    pass

# 覆盖边界情况
def test_boundary(self):
    # 边界值
    pass
```

### 5. 测试速度

```python
# ✅ 好的：快速测试
def test_fast(self):
    # 使用小模型或模拟
    result = function(small_input)
    assert result

# ❌ 避免：慢速测试（除非必要）
def test_slow(self):
    # 使用大模型，需要很长时间
    result = function(large_input)
    assert result
```

## 测试示例

### 示例 1: 修复 OOM 问题

```python
import unittest
from sglang import Runtime

class TestOOMFix(unittest.TestCase):
    """测试 OOM 问题修复"""
    
    def setUp(self):
        self.runtime = Runtime(
            model_path="small_model",  # 使用小模型测试
            gpu_memory_utilization=0.7,
            max_model_len=4096
        )
    
    def test_no_oom_with_reduced_memory(self):
        """测试：减少内存使用后不再 OOM"""
        # 之前会导致 OOM 的输入
        prompt = "A" * 1000  # 长提示
        
        # 应该不再 OOM
        result = self.runtime.generate({
            "prompt": prompt,
            "max_tokens": 100
        })
        
        self.assertIsNotNone(result)
        self.assertIn("text", result)
    
    def test_batch_processing(self):
        """测试：批处理不会导致 OOM"""
        prompts = ["Hello"] * 10
        
        results = []
        for prompt in prompts:
            result = self.runtime.generate({
                "prompt": prompt,
                "max_tokens": 10
            })
            results.append(result)
        
        self.assertEqual(len(results), 10)
        self.assertTrue(all(r is not None for r in results))
```

### 示例 2: 修复序列长度问题

```python
class TestSequenceLengthFix(unittest.TestCase):
    """测试序列长度问题修复"""
    
    def setUp(self):
        self.runtime = Runtime(
            model_path="model",
            max_model_len=8192  # 增加最大长度
        )
    
    def test_long_sequence(self):
        """测试：长序列不再报错"""
        long_prompt = "A" * 5000
        
        # 之前会报错，现在应该成功
        result = self.runtime.generate({
            "prompt": long_prompt,
            "max_tokens": 100
        })
        
        self.assertIsNotNone(result)
    
    def test_sequence_length_validation(self):
        """测试：序列长度验证"""
        # 超过最大长度应该报错
        too_long = "A" * 10000
        
        with self.assertRaises(ValueError):
            self.runtime.generate({
                "prompt": too_long,
                "max_tokens": 100
            })
```

### 示例 3: 修复 API 错误

```python
class TestAPIFix(unittest.TestCase):
    """测试 API 错误修复"""
    
    def setUp(self):
        self.runtime = Runtime(model_path="model")
    
    def test_valid_request(self):
        """测试：有效请求"""
        result = self.runtime.generate({
            "prompt": "Hello",
            "max_tokens": 10,
            "temperature": 0.7
        })
        
        self.assertIsNotNone(result)
        self.assertIn("text", result)
    
    def test_invalid_parameters(self):
        """测试：无效参数处理"""
        # 负数 max_tokens
        with self.assertRaises(ValueError):
            self.runtime.generate({
                "prompt": "Hello",
                "max_tokens": -1
            })
        
        # 无效 temperature
        with self.assertRaises(ValueError):
            self.runtime.generate({
                "prompt": "Hello",
                "max_tokens": 10,
                "temperature": -1
            })
    
    def test_missing_required_fields(self):
        """测试：缺少必需字段"""
        with self.assertRaises(KeyError):
            self.runtime.generate({
                "max_tokens": 10
                # 缺少 prompt
            })
```

### 示例 4: 修复环境配置问题

```python
import unittest
import os

class TestEnvironmentFix(unittest.TestCase):
    """测试环境配置问题修复"""
    
    def test_cuda_available(self):
        """测试：CUDA 可用"""
        import torch
        self.assertTrue(torch.cuda.is_available())
    
    def test_required_packages(self):
        """测试：必需包已安装"""
        import importlib
        
        required = ["sglang", "torch", "transformers"]
        for pkg in required:
            with self.subTest(package=pkg):
                try:
                    importlib.import_module(pkg)
                except ImportError:
                    self.fail(f"Package {pkg} not installed")
    
    def test_environment_variables(self):
        """测试：环境变量设置"""
        # 检查 CUDA_HOME（如果使用 CUDA）
        if os.environ.get("CUDA_HOME"):
            self.assertTrue(os.path.exists(os.environ["CUDA_HOME"]))
```

## 测试验证清单

在提交修复前，确保：

- [ ] 测试能够复现原始问题
- [ ] 修复后测试通过
- [ ] 没有引入新的错误
- [ ] 边界情况已覆盖
- [ ] 错误情况已测试
- [ ] 测试代码清晰易懂
- [ ] 测试运行时间合理
- [ ] 测试独立且可重复

## 持续集成

### 在 CI 中运行测试

```yaml
# .github/workflows/test.yml
name: Test

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: |
          pip install -e "python[test]"
      - name: Run tests
        run: |
          pytest test/ -v
```

## 测试工具

### 1. 覆盖率工具

```bash
# 安装
pip install pytest-cov

# 运行并生成报告
pytest --cov=sglang --cov-report=html test/

# 查看报告
open htmlcov/index.html
```

### 2. 性能测试

```python
import time
import statistics

def benchmark_function(func, inputs, iterations=100):
    """性能基准测试"""
    times = []
    for _ in range(iterations):
        start = time.time()
        func(inputs)
        times.append(time.time() - start)
    
    return {
        "mean": statistics.mean(times),
        "median": statistics.median(times),
        "std": statistics.stdev(times),
        "min": min(times),
        "max": max(times)
    }
```

### 3. 压力测试

```python
def test_stress(self):
    """压力测试"""
    # 大量并发请求
    import concurrent.futures
    
    def make_request():
        return self.runtime.generate({
            "prompt": "Hello",
            "max_tokens": 10
        })
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
        futures = [executor.submit(make_request) for _ in range(1000)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]
    
    self.assertEqual(len(results), 1000)
    self.assertTrue(all(r is not None for r in results))
```

## 总结

编写好的测试需要：

1. **清晰的目标**: 知道测试什么
2. **完整的覆盖**: 正常、边界、错误情况
3. **独立性**: 测试之间不依赖
4. **可重复性**: 结果一致
5. **快速执行**: 不阻塞开发
6. **易于维护**: 代码清晰易懂

通过遵循这些指南，您可以编写出高质量的测试，确保修复后的代码正确且稳定。