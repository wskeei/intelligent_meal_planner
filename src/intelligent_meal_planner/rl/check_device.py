"""
检查训练设备配置
查看 PyTorch 是否可以使用 GPU
"""

import sys
import io

# 设置 UTF-8 编码，避免 Windows 控制台乱码
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import torch
import stable_baselines3 as sb3


def check_device():
    """检查可用的计算设备"""
    print("="*60)
    print("训练设备配置检查")
    print("="*60)
    
    print(f"\n🐍 Python 版本: {sys.version}")
    print(f"🔥 PyTorch 版本: {torch.__version__}")
    print(f"🤖 Stable-Baselines3 版本: {sb3.__version__}")
    
    print("\n" + "="*60)
    print("GPU 可用性检查")
    print("="*60)
    
    # 检查 CUDA（NVIDIA GPU）
    cuda_available = torch.cuda.is_available()
    print(f"\n✅ CUDA 可用: {cuda_available}")
    
    if cuda_available:
        print(f"   GPU 数量: {torch.cuda.device_count()}")
        print(f"   当前 GPU: {torch.cuda.current_device()}")
        print(f"   GPU 名称: {torch.cuda.get_device_name(0)}")
        print(f"   CUDA 版本: {torch.version.cuda}")
    else:
        print("   ⚠️  未检测到 NVIDIA GPU 或 CUDA 未安装")
    
    # 检查 MPS（Apple Silicon）
    mps_available = hasattr(torch.backends, 'mps') and torch.backends.mps.is_available()
    print(f"\n✅ MPS (Apple Silicon) 可用: {mps_available}")
    
    # 确定默认设备
    print("\n" + "="*60)
    print("默认训练设备")
    print("="*60)
    
    if cuda_available:
        device = "cuda"
        print(f"\n🚀 将使用 GPU 训练（CUDA）")
        print(f"   这会大大加快训练速度！")
    elif mps_available:
        device = "mps"
        print(f"\n🚀 将使用 GPU 训练（Apple Silicon MPS）")
        print(f"   这会大大加快训练速度！")
    else:
        device = "cpu"
        print(f"\n💻 将使用 CPU 训练")
        print(f"   ⚠️  训练速度较慢，但完全可以使用")
    
    print(f"\n   默认设备: {device}")
    
    # 性能建议
    print("\n" + "="*60)
    print("训练性能建议")
    print("="*60)
    
    if device == "cpu":
        print("\n📊 CPU 训练建议：")
        print("   • 快速训练（测试）：1万步 约 5-10 分钟")
        print("   • 标准训练：10万步 约 30-60 分钟")
        print("   • 完整训练：50万步 约 2-5 小时")
        print("\n💡 提示：")
        print("   • CPU 训练完全可行，这个项目模型很小")
        print("   • 如果有 NVIDIA GPU，可以安装 CUDA 版本的 PyTorch")
        print("   • 命令：pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118")
    else:
        print("\n📊 GPU 训练建议：")
        print("   • 快速训练：1万步 约 1-2 分钟")
        print("   • 标准训练：10万步 约 10-20 分钟")
        print("   • 完整训练：50万步 约 1-2 小时")
        print("\n💡 GPU 加速效果显著，训练速度快 5-10 倍！")
    
    print("\n" + "="*60)
    print("Stable-Baselines3 设备说明")
    print("="*60)
    
    print("\n📚 关于 Stable-Baselines3 的设备使用：")
    print("   • SB3 基于 PyTorch 构建")
    print("   • 自动检测可用设备（GPU > CPU）")
    print("   • DQN 模型会自动使用 PyTorch 的默认设备")
    print("   • 无需手动指定设备，SB3 会智能选择")
    
    print("\n✨ 如果你想强制使用特定设备：")
    print("   可以在创建模型时传入 device 参数：")
    print("   model = DQN('MlpPolicy', env, device='cuda')  # 强制使用 GPU")
    print("   model = DQN('MlpPolicy', env, device='cpu')   # 强制使用 CPU")
    
    print("\n" + "="*60)
    
    return device


if __name__ == "__main__":
    device = check_device()
    print(f"\n当前系统将默认使用: {device.upper()}")
    print("="*60)