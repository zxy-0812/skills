# SGLang 错误分析与解决

SGLang 常见错误类型、原因分析和解决方案。

## 目录

- 启动错误
- 运行时错误
- API 错误
- 内存错误
- 性能问题
- 错误分析流程

## 启动错误

### 错误 1: 模型加载失败

**错误信息:**
```
OSError: Can't load tokenizer for 'model-name'
ValueError: Model not found
```

**原因分析:**
1. 模型路径不正确
2. 模型文件不完整
3. 网络问题导致下载失败
4. 权限问题

**诊断步骤:**
```bash
# 1. 检查模型路径
ls -la /path/to/model

# 2. 检查模型文件
ls -la /path/to/model/ | grep -E "config.json|tokenizer"

# 3. 尝试手动加载
python -c "from transformers import AutoTokenizer; AutoTokenizer.from_pretrained('/path/to/model')"

# 4. 检查 HuggingFace 连接
huggingface-cli login
```

**解决方案:**
```bash
# 1. 使用完整路径
python -m sglang.launch_server \
    --model-path /absolute/path/to/model

# 2. 重新下载模型
python -c "from transformers import AutoModelForCausalLM; AutoModelForCausalLM.from_pretrained('model-name')"

# 3. 使用信任标志（自定义模型）
python -m sglang.launch_server \
    --model-path model-name \
    --trust-remote-code
```

### 错误 2: 端口占用

**错误信息:**
```
OSError: [Errno 98] Address already in use
```

**诊断:**
```bash
# 查找占用端口的进程
lsof -i :30000
# 或
netstat -tulpn | grep 30000
```

**解决方案:**
```bash
# 1. 杀死占用进程
kill -9 <PID>

# 2. 使用其他端口
python -m sglang.launch_server --port 30001

# 3. 检查是否有残留进程
ps aux | grep sglang
pkill -f sglang
```

### 错误 3: 配置错误

**错误信息:**
```
ValueError: Invalid configuration
KeyError: 'missing_key'
```

**诊断:**
```python
# 检查配置文件
import json
with open('config.json', 'r') as f:
    config = json.load(f)
    print(json.dumps(config, indent=2))
```

**解决方案:**
```bash
# 1. 使用默认配置
python -m sglang.launch_server --model-path model

# 2. 检查环境变量
env | grep SGLANG

# 3. 验证参数
python -m sglang.launch_server --help
```

## 运行时错误

### 错误 1: CUDA Out of Memory (OOM)

**错误信息:**
```
RuntimeError: CUDA out of memory. Tried to allocate X.XX GiB.
```

**原因分析:**
1. 模型太大，超出 GPU 内存
2. 批次大小太大
3. 序列长度太长
4. KV 缓存占用过多内存

**诊断:**
```python
import torch

# 检查内存使用
print(f"Allocated: {torch.cuda.memory_allocated() / 1e9:.2f} GB")
print(f"Reserved: {torch.cuda.memory_reserved() / 1e9:.2f} GB")
print(f"Max allocated: {torch.cuda.max_memory_allocated() / 1e9:.2f} GB")

# 检查 GPU 信息
for i in range(torch.cuda.device_count()):
    props = torch.cuda.get_device_properties(i)
    print(f"GPU {i}: {props.name}, {props.total_memory / 1e9:.2f} GB")
```

**解决方案:**
```bash
# 1. 减少 GPU 内存使用率
python -m sglang.launch_server \
    --model-path model \
    --gpu-memory-utilization 0.7

# 2. 减少最大序列长度
--max-model-len 4096

# 3. 减少批次大小
--max-num-seqs 64

# 4. 启用量化
--quantization awq

# 5. 使用张量并行
--tensor-parallel-size 2
```

### 错误 2: 序列长度超限

**错误信息:**
```
ValueError: Sequence length exceeds maximum model length
```

**诊断:**
```python
# 检查序列长度
input_length = len(tokenizer.encode(prompt))
max_length = model.config.max_position_embeddings
print(f"Input length: {input_length}, Max: {max_length}")
```

**解决方案:**
```bash
# 1. 增加最大长度
python -m sglang.launch_server \
    --model-path model \
    --max-model-len 8192

# 2. 或减少输入长度
# 在客户端截断 prompt

# 3. 使用分块预填充
--enable-chunked-prefill
```

### 错误 3: 推理失败

**错误信息:**
```
RuntimeError: Error during inference
AssertionError: Assertion failed
```

**诊断步骤:**
```bash
# 1. 启用详细日志
export SGLANG_LOGGING_LEVEL=DEBUG
python -m sglang.launch_server --model-path model

# 2. 检查完整堆栈跟踪
# 查看日志文件中的完整错误信息

# 3. 简化输入测试
# 使用最简单的 prompt 测试
```

**代码分析:**
```python
# 定位错误发生的位置
# 1. 查看堆栈跟踪中的文件和行号
# 2. 阅读相关代码
# 3. 检查输入数据
# 4. 验证假设

# 示例：检查输入
import sglang as sgl

@sgl.function
def test_function(s, prompt):
    s += prompt
    s += sgl.gen("output", max_tokens=10)

try:
    result = test_function.run(prompt="Hello")
    print(result)
except Exception as e:
    import traceback
    traceback.print_exc()
    print(f"Error type: {type(e).__name__}")
    print(f"Error message: {str(e)}")
```

## API 错误

### 错误 1: 请求格式错误

**错误信息:**
```
400 Bad Request
{"detail": "Invalid request format"}
```

**诊断:**
```python
# 检查请求格式
import requests

response = requests.post(
    "http://localhost:30000/v1/completions",
    json={
        "model": "model-name",
        "prompt": "Hello",
        "max_tokens": 10
    }
)
print(response.status_code)
print(response.json())
```

**解决方案:**
```python
# 正确的请求格式
import requests

# Completions API
response = requests.post(
    "http://localhost:30000/v1/completions",
    json={
        "model": "model-name",
        "prompt": "Hello",
        "max_tokens": 10,
        "temperature": 0.7
    },
    headers={"Content-Type": "application/json"}
)

# Chat API
response = requests.post(
    "http://localhost:30000/v1/chat/completions",
    json={
        "model": "model-name",
        "messages": [
            {"role": "user", "content": "Hello"}
        ],
        "max_tokens": 10
    }
)
```

### 错误 2: 参数验证失败

**错误信息:**
```
422 Unprocessable Entity
{"detail": [{"loc": ["body", "max_tokens"], "msg": "value must be positive"}]}
```

**解决方案:**
```python
# 验证参数
def validate_request(request):
    assert request.max_tokens > 0, "max_tokens must be positive"
    assert 0 <= request.temperature <= 2, "temperature must be between 0 and 2"
    assert request.top_p > 0, "top_p must be positive"
    # ... 其他验证
```

### 错误 3: 连接错误

**错误信息:**
```
ConnectionRefusedError: [Errno 111] Connection refused
```

**诊断:**
```bash
# 1. 检查服务器是否运行
curl http://localhost:30000/health

# 2. 检查端口
netstat -tuln | grep 30000

# 3. 检查防火墙
sudo ufw status
```

**解决方案:**
```bash
# 1. 启动服务器
python -m sglang.launch_server --model-path model

# 2. 绑定到所有接口
python -m sglang.launch_server \
    --model-path model \
    --host 0.0.0.0 \
    --port 30000

# 3. 检查网络连接
ping localhost
telnet localhost 30000
```

## 内存错误

### 错误分析流程

1. **收集错误信息**
   ```python
   import traceback
   try:
       # 你的代码
       pass
   except RuntimeError as e:
       print(f"Error: {e}")
       traceback.print_exc()
   ```

2. **分析内存使用**
   ```python
   import torch
   
   # 记录内存快照
   torch.cuda.reset_peak_memory_stats()
   
   # 执行操作
   # ...
   
   # 检查峰值内存
   peak = torch.cuda.max_memory_allocated() / 1e9
   print(f"Peak memory: {peak:.2f} GB")
   ```

3. **定位内存分配**
   ```python
   # 使用内存分析工具
   import torch.profiler
   
   with torch.profiler.profile(
       activities=[torch.profiler.ProfilerActivity.CUDA],
       record_shapes=True,
       profile_memory=True
   ) as prof:
       # 你的代码
       pass
   
   print(prof.key_averages().table(sort_by="cuda_memory_usage"))
   ```

### 常见内存问题

**问题 1: KV 缓存过大**

```python
# 诊断
cache_size = num_sequences * max_seq_len * hidden_size * 2 * dtype_size
print(f"Estimated cache size: {cache_size / 1e9:.2f} GB")

# 解决方案
# 减少 max-num-seqs
# 减少 max-model-len
# 使用更激进的量化
```

**问题 2: 批次过大**

```python
# 诊断
batch_memory = batch_size * seq_len * hidden_size * dtype_size
print(f"Batch memory: {batch_memory / 1e9:.2f} GB")

# 解决方案
# 减少批次大小
# 使用连续批处理
```

## 性能问题

### 问题 1: 吞吐量低

**诊断:**
```bash
# 1. 检查 GPU 利用率
watch -n 1 nvidia-smi

# 2. 检查批处理
# 查看日志中的批次大小

# 3. 检查序列长度分布
# 分析请求的序列长度
```

**解决方案:**
```bash
# 1. 增加并发
--max-num-seqs 512

# 2. 启用优化
--enable-prefix-caching
--enable-chunked-prefill

# 3. 使用张量并行
--tensor-parallel-size 4
```

### 问题 2: 延迟高

**诊断:**
```python
import time

start = time.time()
# 执行推理
result = model.generate(...)
end = time.time()

print(f"Latency: {end - start:.2f}s")
print(f"Tokens: {len(result)}")
print(f"Tokens/s: {len(result) / (end - start):.2f}")
```

**解决方案:**
```bash
# 1. 减少序列长度
# 2. 启用前缀缓存
--enable-prefix-caching
# 3. 使用更小的模型
# 4. 优化提示词长度
```

## 错误分析流程

### 系统化分析方法

1. **收集信息**
   ```bash
   # 错误消息
   # 完整堆栈跟踪
   # 环境信息
   python -m sglang.check_env
   
   # 日志文件
   tail -100 /path/to/logfile
   ```

2. **重现问题**
   ```python
   # 创建最小复现用例
   def minimal_reproduce():
       # 最简单的代码能重现问题
       pass
   ```

3. **定位代码**
   ```bash
   # 使用 grep 搜索
   grep -r "error_message" python/sglang/
   
   # 使用代码搜索
   # 在 Cursor 中使用语义搜索
   ```

4. **分析原因**
   - 检查输入数据
   - 检查配置
   - 检查依赖关系
   - 检查边界条件

5. **验证假设**
   ```python
   # 添加断言
   assert condition, "Error message"
   
   # 添加日志
   import logging
   logging.debug("Debug info")
   ```

6. **实施修复**
   - 修改代码
   - 保持代码风格
   - 添加注释

7. **测试验证**
   ```bash
   # 运行测试
   python test/test_fix.py
   
   # 验证修复
   # 确保测试通过
   ```

## 调试技巧

### 使用日志

```python
import logging

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# 使用日志
logger.debug("Debug message")
logger.info("Info message")
logger.warning("Warning message")
logger.error("Error message")
```

### 使用断点

```python
# 使用 pdb
import pdb
pdb.set_trace()

# 使用 ipdb (需要安装)
import ipdb
ipdb.set_trace()

# 使用 IDE 断点
# 在代码中设置断点，使用调试器
```

### 使用性能分析

```python
import cProfile
import pstats

# 性能分析
profiler = cProfile.Profile()
profiler.enable()

# 你的代码
# ...

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(20)  # 打印前 20 个最耗时的函数
```

## 常见错误模式

### 模式 1: 类型错误

```python
# 错误
result = function(str_value)  # 期望 int

# 修复
result = function(int(str_value))
```

### 模式 2: 空值错误

```python
# 错误
value = data['key']  # KeyError if 'key' not exists

# 修复
value = data.get('key', default_value)
```

### 模式 3: 索引错误

```python
# 错误
item = list[10]  # IndexError if len(list) <= 10

# 修复
if len(list) > 10:
    item = list[10]
```

## 获取帮助

1. **查看文档**: https://sglang.readthedocs.io/
2. **搜索 Issues**: https://github.com/sgl-project/sglang/issues
3. **检查日志**: 启用 DEBUG 级别日志
4. **社区支持**: GitHub Discussions