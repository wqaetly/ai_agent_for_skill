"""
Unity RPC客户端测试程�?用于验证RPC服务器的通信功能
"""

import asyncio
import json
import struct
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SimpleRPCClient:
    """简单的RPC测试客户�?""

    def __init__(self, host='127.0.0.1', port=8766):
        self.host = host
        self.port = port
        self.reader = None
        self.writer = None

    async def connect(self):
        """连接到RPC服务�?""
        try:
            self.reader, self.writer = await asyncio.open_connection(
                self.host, self.port
            )
            logger.info(f"已连接到RPC服务�? {self.host}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"连接失败: {e}")
            return False

    async def send_message(self, message: dict):
        """发送消息到服务�?""
        try:
            # 序列化为JSON
            json_data = json.dumps(message, ensure_ascii=False).encode('utf-8')

            # 发送长度前缀�?字节，大端序�?            length = len(json_data)
            self.writer.write(struct.pack('>I', length))

            # 发送JSON数据
            self.writer.write(json_data)
            await self.writer.drain()

            logger.debug(f"已发�? {message}")

        except Exception as e:
            logger.error(f"发送失�? {e}")
            raise

    async def receive_message(self) -> dict:
        """接收服务器响�?""
        try:
            # 读取长度前缀�?字节�?            length_data = await self.reader.readexactly(4)
            length = struct.unpack('>I', length_data)[0]

            # 读取JSON数据
            json_data = await self.reader.readexactly(length)
            message = json.loads(json_data.decode('utf-8'))

            logger.debug(f"已接�? {message}")
            return message

        except Exception as e:
            logger.error(f"接收失败: {e}")
            raise

    async def call(self, method: str, params: dict = None) -> dict:
        """
        调用RPC方法

        Args:
            method: 方法�?            params: 参数

        Returns:
            服务器响应结�?        """
        # 构造JSON-RPC 2.0请求
        request = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {},
            "id": "test-1"
        }

        # 发送请�?        await self.send_message(request)

        # 接收响应
        response = await self.receive_message()

        # 检查错�?        if "error" in response:
            error = response["error"]
            raise Exception(f"RPC错误: {error['message']} (code: {error['code']})")

        return response.get("result")

    async def close(self):
        """关闭连接"""
        if self.writer:
            self.writer.close()
            await self.writer.wait_closed()
            logger.info("连接已关�?)


async def test_rpc_server():
    """测试RPC服务器功�?""
    client = SimpleRPCClient()

    # 连接到服务器
    if not await client.connect():
        logger.error("无法连接到RPC服务器，请先启动服务器：python start_unity_rpc.py")
        return False

    try:
        # 测试1: ping方法
        logger.info("\n=== 测试1: ping方法 ===")
        result = await client.call("ping", {})
        logger.info(f"ping响应: {result}")
        assert result.get("pong") == True, "ping测试失败"
        logger.info("�?ping测试通过")

        # 测试2: get_server_info方法
        logger.info("\n=== 测试2: get_server_info方法 ===")
        result = await client.call("get_server_info", {})
        logger.info(f"服务器信�? {result}")
        logger.info(f"  - 版本: {result.get('version')}")
        logger.info(f"  - Unity客户端数: {result.get('unity_clients_count')}")
        logger.info(f"  - 已注册方�? {result.get('registered_methods')}")
        logger.info("�?get_server_info测试通过")

        # 测试3: create_skill方法（如果已注册�?        logger.info("\n=== 测试3: create_skill方法 ===")
        skill_config = {
            "skillName": "测试技�?,
            "skillId": "test_skill_001",
            "actions": []
        }
        result = await client.call("create_skill", {
            "skill_name": "测试技�?,
            "config": skill_config
        })
        logger.info(f"创建技能响�? {result}")
        assert result.get("success") == True, "create_skill测试失败"
        logger.info("�?create_skill测试通过")

        # 测试4: 不存在的方法（应该返回错误）
        logger.info("\n=== 测试4: 调用不存在的方法 ===")
        try:
            await client.call("non_existent_method", {})
            logger.error("�?应该抛出异常但没�?)
            return False
        except Exception as e:
            logger.info(f"正确捕获错误: {e}")
            logger.info("�?错误处理测试通过")

        logger.info("\n" + "=" * 60)
        logger.info("所有测试通过！RPC服务器工作正�?)
        logger.info("=" * 60)
        return True

    except Exception as e:
        logger.error(f"\n测试失败: {e}", exc_info=True)
        return False

    finally:
        await client.close()


if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("Unity RPC Server 测试程序")
    logger.info("=" * 60)
    logger.info("请确保RPC服务器已启动：python start_unity_rpc.py")
    logger.info("=" * 60 + "\n")

    success = asyncio.run(test_rpc_server())

    if success:
        logger.info("\n测试结果: 成功 �?)
        exit(0)
    else:
        logger.error("\n测试结果: 失败 �?)
        exit(1)
