# 环境配置问题排查

详细的环境配置问题排查指南，涵盖 CUDA、依赖包、系统配置等各个方面。

## 目录

- Python 环境检查
- CUDA/GPU 环境检查
- 依赖包检查
- 系统配置检查
- 常见问题解决方案

## Python 环境检查

### 检查 Python 版本

```bash
# 检查版本
python --version
python3 --version

# 要求: Python >= 3.10
python -c "import sys; assert sys.version_info >= (3, 10), 'Python 3.10+ required'"
```

### 检查虚拟环境

```bash
# 检查是否在虚拟环境中
echo $VIRTUAL_ENV

# 激活虚拟环境（如需要）
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

# 检查 pip
pip --version
which pip
```

### 检查 Python 路径

```python
import sys
print("Python executable:", sys.executable)
print("Python version:", sys.version)
print("Python path:")
for p in sys.path:
    print(f"  {p}")
```

## CUDA/GPU 环境检查

### NVIDIA GPU 检查

```bash
# 检查 GPU 是否可见
nvidia-smi

# 检查 CUDA 驱动版本
nvidia-smi --query-gpu=driver_version --format=csv,noheader

# 检查 CUDA 工具包
nvcc --version

# 检查 CUDA_HOME
echo $CUDA_HOME
ls -la $CUDA_HOME/bin/nvcc
```

### PyTorch CUDA 检查

```python
import torch

# 检查 CUDA 可用性
print(f"CUDA available: {torch.cuda.is_available()}")

if torch.cuda.is_available():
    print(f"CUDA version: {torch.version.cuda}")
    print(f"cuDNN version: {torch.backends.cudnn.version()}")
    print(f"GPU count: {torch.cuda.device_count()}")
    
    for i in range(torch.cuda.device_count()):
        print(f"GPU {i}: {torch.cuda.get_device_name(i)}")
        print(f"  Memory: {torch.cuda.get_device_properties(i).total_memory / 1e9:.2f} GB")
        print(f"  Compute capability: {torch.cuda.get_device_capability(i)}")
```

### 环境变量检查

```bash
# 检查 CUDA 相关环境变量
env | grep -i cuda

# 常见变量
echo $CUDA_HOME
echo $CUDA_PATH
echo $LD_LIBRARY_PATH
echo $PATH

# 检查 LD_LIBRARY_PATH 是否包含 CUDA 库
echo $LD_LIBRARY_PATH | tr ':' '\n' | grep cuda
```

### CUDA 版本兼容性

| PyTorch 版本 | CUDA 版本 | cuDNN 版本 |
|-------------|----------|-----------|
| 2.0+ | 11.8+ | 8.6+ |
| 2.1+ | 11.8+, 12.1+ | 8.9+ |
| 2.2+ | 11.8+, 12.1+ | 8.9+ |

```python
# 检查版本兼容性
import torch
print(f"PyTorch: {torch.__version__}")
print(f"CUDA: {torch.version.cuda}")
print(f"cuDNN: {torch.backends.cudnn.version()}")
```

## 依赖包检查

### 使用环境检查工具

```bash
# SGLang 内置环境检查
python -m sglang.check_env

# 这会检查:
# - Python 版本
# - CUDA/GPU 信息
# - 所有依赖包版本
# - 系统配置
```

### 手动检查关键包

```bash
# 检查 SGLang 相关包
pip show sglang
pip show sgl-kernel
pip show flashinfer-python

# 检查 PyTorch
pip show torch

# 检查 transformers
pip show transformers

# 列出所有已安装包
pip list | grep -E "sglang|torch|transformers|vllm"
```

### 检查包版本兼容性

```python
# 检查关键包版本
import importlib.metadata

packages = [
    "sglang",
    "torch",
    "transformers",
    "numpy",
    "fastapi",
]

for pkg in packages:
    try:
        version = importlib.metadata.version(pkg)
        print(f"{pkg}: {version}")
    except importlib.metadata.PackageNotFoundError:
        print(f"{pkg}: NOT INSTALLED")
```

### 检查内核模块

```python
# 检查 sgl_kernel
try:
    import sgl_kernel
    print(f"sgl_kernel: {sgl_kernel.__version__}")
except ImportError as e:
    print(f"sgl_kernel import error: {e}")
    print("可能需要重新编译内核")

# 检查 flashinfer
try:
    import flashinfer_python
    print("flashinfer_python: OK")
except ImportError as e:
    print(f"flashinfer_python import error: {e}")
```

## 系统配置检查

### 检查系统资源

```bash
# 检查内存
free -h

# 检查磁盘空间
df -h

# 检查 CPU
lscpu | grep -E "Model name|CPU\(s\)"

# 检查 ulimit
ulimit -a
```

### 检查文件描述符限制

```bash
# 检查当前限制
ulimit -n

# 检查系统限制
cat /proc/sys/fs/file-max

# 临时增加限制
ulimit -n 65536

# 永久设置（需要 root）
# 编辑 /etc/security/limits.conf
```

### 检查网络配置

```bash
# 检查端口占用
lsof -i :30000
netstat -tuln | grep 30000

# 检查防火墙
sudo ufw status
sudo iptables -L
```

## 常见问题解决方案

### 问题 1: ModuleNotFoundError

**症状:**
```
ModuleNotFoundError: No module named 'sgl_kernel'
```

**诊断:**
```bash
# 检查是否安装
python -c "import sgl_kernel"

# 检查安装位置
python -c "import sys; print(sys.path)"
find . -name "sgl_kernel*" -type d
```

**解决方案:**
```bash
# 1. 重新编译内核
cd sgl-kernel
make clean
make

# 2. 重新安装
cd ..
pip install -e "python" --force-reinstall --no-cache-dir

# 3. 验证
python -c "import sgl_kernel; print('OK')"
```

### 问题 2: CUDA not available

**症状:**
```python
torch.cuda.is_available()  # False
```

**诊断:**
```bash
# 1. 检查 GPU
nvidia-smi

# 2. 检查 CUDA
nvcc --version

# 3. 检查 PyTorch CUDA 支持
python -c "import torch; print(torch.version.cuda)"
```

**解决方案:**
```bash
# 1. 安装正确的 PyTorch 版本
# 对于 CUDA 11.8
pip install torch --index-url https://download.pytorch.org/whl/cu118

# 对于 CUDA 12.1
pip install torch --index-url https://download.pytorch.org/whl/cu121

# 2. 设置环境变量
export CUDA_HOME=/usr/local/cuda
export LD_LIBRARY_PATH=$CUDA_HOME/lib64:$LD_LIBRARY_PATH

# 3. 验证
python -c "import torch; print(torch.cuda.is_available())"
```

### 问题 3: 版本冲突

**症状:**
```
ImportError: cannot import name 'XXX' from 'YYY'
```

**诊断:**
```bash
# 检查版本
pip show <package>

# 检查依赖关系
pip check
```

**解决方案:**
```bash
# 1. 创建新的虚拟环境
python -m venv venv_new
source venv_new/bin/activate

# 2. 安装正确版本
pip install sglang[all]

# 3. 或指定版本
pip install torch==2.1.0 transformers==4.35.0
```

### 问题 4: 内存不足

**症状:**
```
RuntimeError: CUDA out of memory
```

**诊断:**
```bash
# 检查 GPU 内存
nvidia-smi

# 检查进程内存使用
nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv
```

**解决方案:**
```bash
# 1. 减少 GPU 内存使用率
python -m sglang.launch_server \
    --model-path <model> \
    --gpu-memory-utilization 0.7

# 2. 减少最大序列长度
--max-model-len 4096

# 3. 使用量化
--quantization awq

# 4. 使用张量并行
--tensor-parallel-size 2
```

### 问题 5: 端口被占用

**症状:**
```
OSError: [Errno 98] Address already in use
```

**诊断:**
```bash
# 查找占用端口的进程
lsof -i :30000
# 或
netstat -tuln | grep 30000
```

**解决方案:**
```bash
# 1. 杀死占用进程
kill -9 <PID>

# 2. 或使用其他端口
python -m sglang.launch_server --port 30001

# 3. 或等待进程结束
# 检查进程状态
ps aux | grep sglang
```

## 环境诊断脚本

创建一个完整的环境诊断脚本：

```python
#!/usr/bin/env python3
"""完整的环境诊断脚本"""

import sys
import subprocess
import importlib.metadata

def check_python():
    print("=" * 50)
    print("Python 环境检查")
    print("=" * 50)
    print(f"Python 版本: {sys.version}")
    print(f"Python 路径: {sys.executable}")
    print(f"虚拟环境: {sys.prefix}")
    
    if sys.version_info < (3, 10):
        print("❌ Python 版本需要 >= 3.10")
        return False
    else:
        print("✅ Python 版本符合要求")
        return True

def check_cuda():
    print("\n" + "=" * 50)
    print("CUDA 环境检查")
    print("=" * 50)
    
    try:
        import torch
        print(f"PyTorch 版本: {torch.__version__}")
        print(f"CUDA 可用: {torch.cuda.is_available()}")
        
        if torch.cuda.is_available():
            print(f"CUDA 版本: {torch.version.cuda}")
            print(f"GPU 数量: {torch.cuda.device_count()}")
            for i in range(torch.cuda.device_count()):
                print(f"  GPU {i}: {torch.cuda.get_device_name(i)}")
            return True
        else:
            print("❌ CUDA 不可用")
            return False
    except ImportError:
        print("❌ PyTorch 未安装")
        return False

def check_packages():
    print("\n" + "=" * 50)
    print("依赖包检查")
    print("=" * 50)
    
    packages = [
        "sglang",
        "sgl_kernel",
        "torch",
        "transformers",
        "numpy",
    ]
    
    all_ok = True
    for pkg in packages:
        try:
            version = importlib.metadata.version(pkg)
            print(f"✅ {pkg}: {version}")
        except importlib.metadata.PackageNotFoundError:
            print(f"❌ {pkg}: 未安装")
            all_ok = False
    
    return all_ok

def check_sglang():
    print("\n" + "=" * 50)
    print("SGLang 功能检查")
    print("=" * 50)
    
    try:
        import sglang
        print(f"✅ sglang: {sglang.__version__}")
        
        try:
            import sgl_kernel
            print("✅ sgl_kernel: 已导入")
        except ImportError as e:
            print(f"❌ sgl_kernel: {e}")
            return False
        
        return True
    except ImportError as e:
        print(f"❌ sglang 导入失败: {e}")
        return False

def main():
    print("SGLang 环境诊断")
    print("=" * 50)
    
    results = []
    results.append(("Python", check_python()))
    results.append(("CUDA", check_cuda()))
    results.append(("依赖包", check_packages()))
    results.append(("SGLang", check_sglang()))
    
    print("\n" + "=" * 50)
    print("诊断结果")
    print("=" * 50)
    
    all_ok = True
    for name, ok in results:
        status = "✅ 通过" if ok else "❌ 失败"
        print(f"{name}: {status}")
        if not ok:
            all_ok = False
    
    if all_ok:
        print("\n✅ 所有检查通过！")
        return 0
    else:
        print("\n❌ 部分检查失败，请查看上述详细信息")
        return 1

if __name__ == "__main__":
    sys.exit(main())
```

## 快速修复命令

```bash
# 完整环境重置
python -m venv venv_clean
source venv_clean/bin/activate
pip install --upgrade pip
pip install sglang[all]

# 重新编译内核
cd sgl-kernel && make clean && make && cd ..

# 重新安装
pip install -e "python" --force-reinstall --no-cache-dir

# 验证安装
python -m sglang.check_env
```