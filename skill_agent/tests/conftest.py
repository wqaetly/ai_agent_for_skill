"""
Pytest 配置文件
在所有测试运行前加载环境变量
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到 sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 在 pytest 收集测试之前加载环境变量
from dotenv import load_dotenv
env_path = project_root / '.env'
if env_path.exists():
    load_dotenv(env_path)
    print(f"[OK] Loaded environment variables from {env_path}")
else:
    print(f"[WARN] .env file not found at {env_path}")

# 验证关键环境变量
deepseek_key = os.getenv("DEEPSEEK_API_KEY")
if deepseek_key:
    print(f"[OK] DEEPSEEK_API_KEY loaded (length: {len(deepseek_key)})")
else:
    print("[WARN] DEEPSEEK_API_KEY not found in environment")
