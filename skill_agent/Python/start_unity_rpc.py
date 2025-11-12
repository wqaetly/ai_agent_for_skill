"""
Unity RPC服务器启动程�?支持命令行参数配置和环境变量加载
"""

import asyncio
import logging
import os
import sys
from pathlib import Path
import argparse

# 添加父目录到Python路径，以便导入core模块
sys.path.insert(0, str(Path(__file__).parent.parent))

from Python.unity_rpc_server import UnityRPCServer

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)


def load_env_file(env_path: str = ".env"):
    """
    加载.env文件中的环境变量

    Args:
        env_path: .env文件路径
    """
    env_file = Path(__file__).parent.parent / env_path

    if not env_file.exists():
        logger.warning(f".env文件不存�? {env_file}")
        return

    logger.info(f"加载环境变量: {env_file}")

    with open(env_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()

            # 跳过注释和空�?            if not line or line.startswith('#'):
                continue

            # 解析 KEY=VALUE
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")

                # 只在环境变量未设置时加载
                if key and key not in os.environ:
                    os.environ[key] = value
                    logger.debug(f"加载环境变量: {key}")


async def main():
    """主函�?""
    parser = argparse.ArgumentParser(
        description='Unity RPC Server - Unity与Python双向通信服务�?,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python start_unity_rpc.py                    # 使用默认配置启动
  python start_unity_rpc.py --port 9000        # 自定义端�?  python start_unity_rpc.py --host 0.0.0.0     # 监听所有网络接�?  python start_unity_rpc.py --debug            # 开启调试日�?        """
    )

    parser.add_argument(
        '--host',
        default=os.getenv('UNITY_RPC_HOST', '127.0.0.1'),
        help='监听地址 (默认: 127.0.0.1，可通过UNITY_RPC_HOST环境变量配置)'
    )

    parser.add_argument(
        '--port',
        type=int,
        default=int(os.getenv('UNITY_RPC_PORT', '8766')),
        help='监听端口 (默认: 8766，可通过UNITY_RPC_PORT环境变量配置)'
    )

    parser.add_argument(
        '--debug',
        action='store_true',
        help='开启调试日�?
    )

    parser.add_argument(
        '--env-file',
        default='.env',
        help='环境变量文件路径 (默认: .env)'
    )

    args = parser.parse_args()

    # 设置日志级别
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("调试模式已开�?)

    # 加载环境变量
    load_env_file(args.env_file)

    # 显示启动信息
    logger.info("=" * 60)
    logger.info("Unity RPC Server v1.0.0")
    logger.info("=" * 60)
    logger.info(f"监听地址: {args.host}:{args.port}")
    logger.info(f"工作目录: {Path.cwd()}")
    logger.info("=" * 60)
    logger.info("服务器启动中...")
    logger.info("�?Ctrl+C 停止服务�?)
    logger.info("=" * 60)

    # 创建并启动RPC服务�?    server = UnityRPCServer(host=args.host, port=args.port)

    # 注册示例方法
    async def handle_create_skill(params: dict):
        """处理技能创建请�?""
        skill_name = params.get("skill_name", "UnknownSkill")
        config = params.get("config", {})

        logger.info(f"收到技能创建请�? {skill_name}")
        logger.debug(f"配置内容: {config}")

        # 这里可以添加实际的技能创建逻辑
        # 例如：保存到文件、调用Unity�?
        return {
            "success": True,
            "message": f"技�?'{skill_name}' 创建成功",
            "skill_name": skill_name
        }

    async def handle_update_skill(params: dict):
        """处理技能更新请�?""
        skill_name = params.get("skill_name", "UnknownSkill")
        config = params.get("config", {})

        logger.info(f"收到技能更新请�? {skill_name}")

        return {
            "success": True,
            "message": f"技�?'{skill_name}' 更新成功"
        }

    async def handle_delete_skill(params: dict):
        """处理技能删除请�?""
        skill_name = params.get("skill_name", "UnknownSkill")

        logger.info(f"收到技能删除请�? {skill_name}")

        return {
            "success": True,
            "message": f"技�?'{skill_name}' 删除成功"
        }

    # 注册方法
    server.register_method("create_skill", handle_create_skill)
    server.register_method("update_skill", handle_update_skill)
    server.register_method("delete_skill", handle_delete_skill)

    logger.info(f"已注册方�? {list(server.method_handlers.keys())}")

    try:
        # 启动服务�?        await server.start()
    except KeyboardInterrupt:
        logger.info("\n收到停止信号，正在关闭服务器...")
        await server.stop()
    except Exception as e:
        logger.error(f"服务器运行错�? {e}", exc_info=True)
        return 1

    logger.info("服务器已停止")
    return 0


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except Exception as e:
        logger.error(f"启动失败: {e}", exc_info=True)
        sys.exit(1)
