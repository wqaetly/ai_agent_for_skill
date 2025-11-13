"""
Unity RPC服务器
基于JSON-RPC 2.0协议的TCP Socket服务器，支持Unity与Web UI的双向通信
"""

import asyncio
import json
import logging
import uuid
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass, asdict
from datetime import datetime

logger = logging.getLogger(__name__)


# ==================== JSON-RPC 2.0数据模型 ====================

@dataclass
class JSONRPCRequest:
    """JSON-RPC 2.0请求"""
    jsonrpc: str = "2.0"
    method: str = ""
    params: Optional[Dict[str, Any]] = None
    id: Optional[str] = None  # None表示通知（不需要响应）


@dataclass
class JSONRPCResponse:
    """JSON-RPC 2.0响应"""
    jsonrpc: str = "2.0"
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None
    id: Optional[str] = None


@dataclass
class JSONRPCError:
    """JSON-RPC 2.0错误"""
    code: int
    message: str
    data: Optional[Any] = None


# JSON-RPC 2.0错误码
class RPCErrorCode:
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603


# ==================== Unity客户端连接 ====================

class UnityClient:
    """Unity客户端连接"""

    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        self.reader = reader
        self.writer = writer
        self.client_id = str(uuid.uuid4())[:8]
        self.connected_at = datetime.now()
        self.addr = writer.get_extra_info('peername')

        logger.info(f"Unity client connected: {self.client_id} from {self.addr}")

    async def send_request(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        向Unity发送RPC请求并等待响应

        Args:
            method: 方法名
            params: 参数

        Returns:
            Unity响应结果
        """
        request_id = str(uuid.uuid4())
        request = JSONRPCRequest(
            jsonrpc="2.0",
            method=method,
            params=params,
            id=request_id
        )

        # 发送请求
        await self._send_message(asdict(request))

        # 等待响应（简化版，实际应该有超时和请求映射）
        response_data = await self._receive_message()

        if response_data is None:
            raise ConnectionError("Unity client disconnected")

        response = JSONRPCResponse(**response_data)

        if response.error:
            raise Exception(
                f"Unity RPC error: {response.error['message']} "
                f"(code: {response.error['code']})"
            )

        return response.result

    async def send_notification(self, method: str, params: Dict[str, Any]):
        """
        向Unity发送通知（不等待响应）

        Args:
            method: 方法名
            params: 参数
        """
        notification = JSONRPCRequest(
            jsonrpc="2.0",
            method=method,
            params=params,
            id=None  # 通知没有id
        )

        await self._send_message(asdict(notification))

    async def _send_message(self, message: Dict[str, Any]):
        """发送JSON消息"""
        data = json.dumps(message).encode('utf-8')
        # 使用长度前缀协议：4字节长度 + JSON数据
        length = len(data)
        self.writer.write(length.to_bytes(4, byteorder='big'))
        self.writer.write(data)
        await self.writer.drain()

    async def _receive_message(self) -> Optional[Dict[str, Any]]:
        """接收JSON消息"""
        try:
            # 读取4字节长度
            length_bytes = await self.reader.readexactly(4)
            length = int.from_bytes(length_bytes, byteorder='big')

            # 读取JSON数据
            data = await self.reader.readexactly(length)
            message = json.loads(data.decode('utf-8'))
            return message

        except asyncio.IncompleteReadError:
            logger.warning(f"Unity client {self.client_id} disconnected")
            return None
        except Exception as e:
            logger.error(f"Error receiving message from Unity: {e}")
            return None

    def close(self):
        """关闭连接"""
        self.writer.close()
        logger.info(f"Unity client {self.client_id} connection closed")


# ==================== Unity RPC服务器 ====================

class UnityRPCServer:
    """Unity RPC服务器"""

    def __init__(self, host: str = "127.0.0.1", port: int = 8766):
        """
        初始化RPC服务器

        Args:
            host: 监听地址
            port: 监听端口
        """
        self.host = host
        self.port = port
        self.server: Optional[asyncio.Server] = None

        # Unity客户端连接（支持多个Unity实例）
        self.unity_clients: List[UnityClient] = []

        # 注册的RPC方法处理器
        self.method_handlers: Dict[str, Callable] = {}

        # 注册内置方法
        self._register_builtin_methods()

    def register_method(self, method_name: str, handler: Callable):
        """
        注册RPC方法处理器

        Args:
            method_name: 方法名
            handler: 处理函数（async或sync均可）

        Example:
            >>> async def handle_search(params):
            ...     return {"results": [...]}
            >>> server.register_method("search_skills", handle_search)
        """
        self.method_handlers[method_name] = handler
        logger.info(f"Registered RPC method: {method_name}")

    def _register_builtin_methods(self):
        """注册内置方法"""
        self.register_method("ping", self._handle_ping)
        self.register_method("get_server_info", self._handle_server_info)

    async def _handle_ping(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """内置ping方法"""
        return {"pong": True, "timestamp": datetime.now().isoformat()}

    async def _handle_server_info(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """内置服务器信息方法"""
        return {
            "version": "1.0.0",
            "unity_clients_count": len(self.unity_clients),
            "registered_methods": list(self.method_handlers.keys())
        }

    async def start(self):
        """启动RPC服务器"""
        self.server = await asyncio.start_server(
            self._handle_client,
            self.host,
            self.port
        )

        addr = self.server.sockets[0].getsockname()
        logger.info(f"Unity RPC server started on {addr[0]}:{addr[1]}")

        async with self.server:
            await self.server.serve_forever()

    async def _handle_client(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter
    ):
        """处理客户端连接"""
        client = UnityClient(reader, writer)
        self.unity_clients.append(client)

        try:
            while True:
                # 接收消息
                message = await client._receive_message()

                if message is None:
                    break  # 客户端断开

                # 解析为JSON-RPC请求
                try:
                    request = JSONRPCRequest(**message)
                    response = await self._handle_request(request)

                    # 如果是请求（有id），发送响应
                    if request.id is not None:
                        await client._send_message(asdict(response))

                except Exception as e:
                    logger.error(f"Error processing request: {e}")
                    error_response = self._create_error_response(
                        RPCErrorCode.INVALID_REQUEST,
                        f"Invalid request: {e}",
                        request_id=message.get("id")
                    )
                    await client._send_message(asdict(error_response))

        except Exception as e:
            logger.error(f"Client handler error: {e}")

        finally:
            # 移除客户端
            self.unity_clients.remove(client)
            client.close()

    async def _handle_request(self, request: JSONRPCRequest) -> JSONRPCResponse:
        """
        处理RPC请求

        Args:
            request: JSON-RPC请求

        Returns:
            JSON-RPC响应
        """
        method = request.method
        params = request.params or {}

        # 查找方法处理器
        handler = self.method_handlers.get(method)

        if handler is None:
            return self._create_error_response(
                RPCErrorCode.METHOD_NOT_FOUND,
                f"Method '{method}' not found",
                request_id=request.id
            )

        try:
            # 调用处理器
            if asyncio.iscoroutinefunction(handler):
                result = await handler(params)
            else:
                result = handler(params)

            return JSONRPCResponse(
                jsonrpc="2.0",
                result=result,
                id=request.id
            )

        except Exception as e:
            logger.error(f"Error executing method '{method}': {e}", exc_info=True)
            return self._create_error_response(
                RPCErrorCode.INTERNAL_ERROR,
                f"Method execution failed: {str(e)}",
                request_id=request.id,
                error_data={"exception": str(e)}
            )

    def _create_error_response(
        self,
        code: int,
        message: str,
        request_id: Optional[str] = None,
        error_data: Optional[Any] = None
    ) -> JSONRPCResponse:
        """创建错误响应"""
        return JSONRPCResponse(
            jsonrpc="2.0",
            error={
                "code": code,
                "message": message,
                "data": error_data
            },
            id=request_id
        )

    async def call_unity(
        self,
        method: str,
        params: Dict[str, Any],
        client_index: int = 0
    ) -> Dict[str, Any]:
        """
        调用Unity方法

        Args:
            method: Unity方法名
            params: 参数
            client_index: Unity客户端索引（支持多个Unity实例）

        Returns:
            Unity返回结果

        Raises:
            ConnectionError: 无Unity客户端连接
        """
        if not self.unity_clients:
            raise ConnectionError("No Unity client connected")

        if client_index >= len(self.unity_clients):
            raise IndexError(f"Unity client index {client_index} out of range")

        client = self.unity_clients[client_index]
        return await client.send_request(method, params)

    async def notify_unity(
        self,
        method: str,
        params: Dict[str, Any],
        broadcast: bool = False
    ):
        """
        向Unity发送通知

        Args:
            method: Unity方法名
            params: 参数
            broadcast: 是否广播给所有Unity客户端
        """
        if not self.unity_clients:
            logger.warning("No Unity client to notify")
            return

        if broadcast:
            # 广播给所有客户端
            for client in self.unity_clients:
                await client.send_notification(method, params)
        else:
            # 只发送给第一个客户端
            await self.unity_clients[0].send_notification(method, params)

    async def stop(self):
        """停止RPC服务器"""
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            logger.info("Unity RPC server stopped")


# ==================== 使用示例 ====================

async def main():
    """测试示例"""
    server = UnityRPCServer(host="127.0.0.1", port=8766)

    # 注册自定义方法
    async def handle_create_skill(params: Dict[str, Any]):
        skill_name = params.get("skill_name")
        config = params.get("config")
        logger.info(f"Creating skill: {skill_name}")

        # 调用Unity
        result = await server.call_unity("CreateSkill", {
            "skillName": skill_name,
            "config": config
        })

        return result

    server.register_method("create_skill", handle_create_skill)

    # 启动服务器
    await server.start()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
