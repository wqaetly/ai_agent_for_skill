"""
模型完整性检查和自动下载脚本
在启动服务前确保 Qwen3-Embedding-0.6B 模型完整
"""

import os
import sys
from pathlib import Path

# 设置UTF-8编码输出（Windows兼容）
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def check_model_completeness(model_dir: str) -> tuple[bool, str]:
    """
    检查模型是否完整

    Returns:
        (is_complete, message)
    """
    model_path = Path(model_dir)

    # 检查目录是否存在
    if not model_path.exists():
        return False, f"模型目录不存在: {model_dir}"

    # 检查必需文件
    required_files = {
        'model.safetensors': 1.0 * 1024 * 1024 * 1024,  # 至少1GB
        'config.json': 100,  # 至少100字节
        'tokenizer.json': 1024 * 1024,  # 至少1MB
    }

    missing_files = []
    incomplete_files = []

    for filename, min_size in required_files.items():
        file_path = model_path / filename
        if not file_path.exists():
            missing_files.append(filename)
        elif file_path.stat().st_size < min_size:
            incomplete_files.append(f"{filename} (< {min_size / (1024*1024):.1f}MB)")

    if missing_files:
        return False, f"缺少文件: {', '.join(missing_files)}"

    if incomplete_files:
        return False, f"文件不完整: {', '.join(incomplete_files)}"

    return True, "模型完整"


def download_model(model_dir: str, repo_id: str = "Qwen/Qwen3-Embedding-0.6B"):
    """
    从 HuggingFace 下载模型
    """
    print(f"\n{'='*60}")
    print(f"开始下载模型: {repo_id}")
    print(f"目标目录: {model_dir}")
    print(f"{'='*60}\n")

    try:
        from huggingface_hub import snapshot_download

        print("正在下载模型文件...")
        print("提示: Qwen3-Embedding-0.6B 约 1.3GB，预计需要 3-10 分钟")
        print("进度条会在下方显示\n")

        snapshot_download(
            repo_id=repo_id,
            local_dir=model_dir,
            local_dir_use_symlinks=False
        )

        print(f"\n{'='*60}")
        print("模型下载完成！")
        print(f"{'='*60}\n")
        return True

    except ImportError:
        print("错误: 缺少 huggingface-hub 依赖")
        print("正在安装...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-U", "huggingface-hub"])
        print("依赖安装完成，重新下载...")
        return download_model(model_dir, repo_id)

    except Exception as e:
        print(f"\n错误: 模型下载失败")
        print(f"原因: {e}")
        print(f"\n手动下载方法:")
        print(f"1. 访问: https://huggingface.co/{repo_id}")
        print(f"2. 下载所有文件到: {model_dir}")
        return False


def main():
    """主函数"""
    # 获取模型目录
    script_dir = Path(__file__).parent
    model_dir = script_dir / "Data" / "models" / "Qwen3-Embedding-0.6B"

    print(f"\n{'='*60}")
    print("Qwen3 嵌入模型检查")
    print(f"{'='*60}\n")

    # 检查模型完整性
    is_complete, message = check_model_completeness(str(model_dir))

    if is_complete:
        print(f"[OK] {message}")
        print(f"  模型路径: {model_dir}")

        # 显示模型文件大小
        model_file = model_dir / "model.safetensors"
        if model_file.exists():
            size_mb = model_file.stat().st_size / (1024 * 1024)
            print(f"  权重大小: {size_mb:.1f} MB")

        print(f"\n{'='*60}\n")
        return 0

    # 模型不完整，需要下载
    print(f"[WARN] {message}")
    print(f"  模型路径: {model_dir}\n")

    # 确认下载
    print("是否自动下载完整模型？")
    print("  [Y] 是，自动下载 (推荐)")
    print("  [N] 否，手动处理")
    print()

    # 在批处理脚本中自动选择 Y
    if len(sys.argv) > 1 and sys.argv[1] == "--auto":
        choice = "Y"
        print("启动脚本模式: 自动下载")
    else:
        choice = input("请选择 [Y/N]: ").strip().upper()

    if choice != "Y":
        print("\n已取消自动下载")
        print("请手动下载模型后重新启动")
        return 1

    # 创建目录
    model_dir.mkdir(parents=True, exist_ok=True)

    # 下载模型
    success = download_model(str(model_dir))

    if not success:
        return 1

    # 再次检查
    is_complete, message = check_model_completeness(str(model_dir))
    if is_complete:
        print(f"[OK] 验证成功: {message}\n")
        return 0
    else:
        print(f"[FAIL] 验证失败: {message}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
