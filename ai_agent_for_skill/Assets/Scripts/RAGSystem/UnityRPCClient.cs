using System;
using System.Collections.Generic;
using System.Net.Sockets;
using System.Text;
using System.Threading;
using Cysharp.Threading.Tasks;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using UnityEngine;

namespace RAGSystem
{
    /// <summary>
    /// Unity RPC客户�?    /// 基于JSON-RPC 2.0协议与Python服务器通信
    /// </summary>
    public class UnityRPCClient : MonoBehaviour
    {
        // ==================== 配置 ====================

        [Header("RPC服务器配�?)]
        [SerializeField] private string serverHost = "127.0.0.1";
        [SerializeField] private int serverPort = 8766;
        [SerializeField] private int connectTimeout = 5000; // 毫秒
        [SerializeField] private int requestTimeout = 30000; // 毫秒

        // ==================== 状�?====================

        private TcpClient tcpClient;
        private NetworkStream networkStream;
        private bool isConnected = false;
        private CancellationTokenSource cancellationTokenSource;

        // 请求映射（ID -> TaskCompletionSource�?        private Dictionary<string, UniTaskCompletionSource<JObject>> pendingRequests =
            new Dictionary<string, UniTaskCompletionSource<JObject>>();

        // ==================== Unity生命周期 ====================

        private void Awake()
        {
            // 确保单例
            var existing = FindObjectsOfType<UnityRPCClient>();
            if (existing.Length > 1)
            {
                Destroy(gameObject);
                return;
            }

            DontDestroyOnLoad(gameObject);
        }

        private async void Start()
        {
            await ConnectAsync();
        }

        private void OnDestroy()
        {
            DisconnectAsync().Forget();
        }

        private void OnApplicationQuit()
        {
            DisconnectAsync().Forget();
        }

        // ==================== 连接管理 ====================

        /// <summary>
        /// 连接到RPC服务�?        /// </summary>
        public async UniTask ConnectAsync()
        {
            if (isConnected)
            {
                Debug.LogWarning("[UnityRPC] Already connected");
                return;
            }

            try
            {
                Debug.Log($"[UnityRPC] Connecting to {serverHost}:{serverPort}...");

                tcpClient = new TcpClient();
                cancellationTokenSource = new CancellationTokenSource();

                // 连接超时控制
                var connectTask = tcpClient.ConnectAsync(serverHost, serverPort);
                var timeoutTask = UniTask.Delay(connectTimeout, cancellationToken: cancellationTokenSource.Token);

                var completedTask = await UniTask.WhenAny(connectTask.AsUniTask(), timeoutTask);

                if (completedTask == 1)
                {
                    throw new TimeoutException($"Connection timeout after {connectTimeout}ms");
                }

                networkStream = tcpClient.GetStream();
                isConnected = true;

                Debug.Log("[UnityRPC] Connected successfully");

                // 启动接收消息循环
                ReceiveMessageLoop(cancellationTokenSource.Token).Forget();

            }
            catch (Exception e)
            {
                Debug.LogError($"[UnityRPC] Connection failed: {e.Message}");
                isConnected = false;
                throw;
            }
        }

        /// <summary>
        /// 断开连接
        /// </summary>
        public async UniTask DisconnectAsync()
        {
            if (!isConnected)
            {
                return;
            }

            Debug.Log("[UnityRPC] Disconnecting...");

            cancellationTokenSource?.Cancel();
            cancellationTokenSource?.Dispose();

            networkStream?.Close();
            networkStream?.Dispose();

            tcpClient?.Close();
            tcpClient?.Dispose();

            isConnected = false;

            Debug.Log("[UnityRPC] Disconnected");

            await UniTask.Yield();
        }

        // ==================== RPC调用 ====================

        /// <summary>
        /// 调用RPC方法
        /// </summary>
        /// <param name="method">方法�?/param>
        /// <param name="params">参数（可选）</param>
        /// <returns>结果</returns>
        public async UniTask<JObject> CallAsync(string method, object @params = null)
        {
            if (!isConnected)
            {
                throw new InvalidOperationException("Not connected to RPC server");
            }

            // 生成请求ID
            string requestId = Guid.NewGuid().ToString();

            // 创建JSON-RPC请求
            var request = new
            {
                jsonrpc = "2.0",
                method = method,
                @params = @params,
                id = requestId
            };

            // 创建等待响应的TaskCompletionSource
            var tcs = new UniTaskCompletionSource<JObject>();
            pendingRequests[requestId] = tcs;

            try
            {
                // 发送请�?                await SendMessageAsync(request);

                // 等待响应（带超时�?                var responseTask = tcs.Task;
                var timeoutTask = UniTask.Delay(requestTimeout);

                var completedTask = await UniTask.WhenAny(responseTask, timeoutTask);

                if (completedTask == 1)
                {
                    pendingRequests.Remove(requestId);
                    throw new TimeoutException($"RPC call '{method}' timeout after {requestTimeout}ms");
                }

                return await responseTask;
            }
            catch
            {
                pendingRequests.Remove(requestId);
                throw;
            }
        }

        /// <summary>
        /// 发送通知（不等待响应�?        /// </summary>
        /// <param name="method">方法�?/param>
        /// <param name="params">参数</param>
        public async UniTask NotifyAsync(string method, object @params = null)
        {
            if (!isConnected)
            {
                throw new InvalidOperationException("Not connected to RPC server");
            }

            var notification = new
            {
                jsonrpc = "2.0",
                method = method,
                @params = @params
                // 注意：通知没有id字段
            };

            await SendMessageAsync(notification);
        }

        // ==================== 消息传输 ====================

        /// <summary>
        /// 发送JSON消息（长度前缀协议�?        /// </summary>
        private async UniTask SendMessageAsync(object message)
        {
            string json = JsonConvert.SerializeObject(message);
            byte[] data = Encoding.UTF8.GetBytes(json);

            // 4字节长度前缀 + JSON数据
            byte[] lengthPrefix = BitConverter.GetBytes(data.Length);
            if (BitConverter.IsLittleEndian)
            {
                Array.Reverse(lengthPrefix); // 转为大端�?            }

            await networkStream.WriteAsync(lengthPrefix, 0, 4);
            await networkStream.WriteAsync(data, 0, data.Length);
            await networkStream.FlushAsync();

            Debug.Log($"[UnityRPC] Sent: {json}");
        }

        /// <summary>
        /// 接收JSON消息（长度前缀协议�?        /// </summary>
        private async UniTask<JObject> ReceiveMessageAsync()
        {
            // 读取4字节长度
            byte[] lengthBuffer = new byte[4];
            int bytesRead = await networkStream.ReadAsync(lengthBuffer, 0, 4);

            if (bytesRead != 4)
            {
                throw new Exception("Connection closed");
            }

            if (BitConverter.IsLittleEndian)
            {
                Array.Reverse(lengthBuffer); // 大端序转小端�?            }
            int length = BitConverter.ToInt32(lengthBuffer, 0);

            // 读取JSON数据
            byte[] dataBuffer = new byte[length];
            int totalRead = 0;

            while (totalRead < length)
            {
                int read = await networkStream.ReadAsync(
                    dataBuffer,
                    totalRead,
                    length - totalRead
                );

                if (read == 0)
                {
                    throw new Exception("Connection closed");
                }

                totalRead += read;
            }

            string json = Encoding.UTF8.GetString(dataBuffer);
            Debug.Log($"[UnityRPC] Received: {json}");

            return JObject.Parse(json);
        }

        /// <summary>
        /// 接收消息循环
        /// </summary>
        private async UniTaskVoid ReceiveMessageLoop(CancellationToken cancellationToken)
        {
            try
            {
                while (!cancellationToken.IsCancellationRequested && isConnected)
                {
                    var message = await ReceiveMessageAsync();

                    // 处理响应
                    if (message.ContainsKey("id") && message["id"].Type != JTokenType.Null)
                    {
                        string responseId = message["id"].ToString();

                        if (pendingRequests.TryGetValue(responseId, out var tcs))
                        {
                            pendingRequests.Remove(responseId);

                            if (message.ContainsKey("error"))
                            {
                                var error = message["error"];
                                var exception = new Exception(
                                    $"RPC Error: {error["message"]} (code: {error["code"]})"
                                );
                                tcs.TrySetException(exception);
                            }
                            else
                            {
                                tcs.TrySetResult(message);
                            }
                        }
                    }
                    else
                    {
                        // 处理通知（服务端主动推送）
                        HandleNotification(message);
                    }
                }
            }
            catch (Exception e)
            {
                if (!cancellationToken.IsCancellationRequested)
                {
                    Debug.LogError($"[UnityRPC] Receive loop error: {e.Message}");
                    isConnected = false;
                }
            }
        }

        /// <summary>
        /// 处理服务端通知
        /// </summary>
        private void HandleNotification(JObject message)
        {
            string method = message["method"]?.ToString();
            var @params = message["params"] as JObject;

            Debug.Log($"[UnityRPC] Notification: {method}");

            // 可以在这里触发事件或委托
            // 例如：OnServerNotification?.Invoke(method, @params);
        }

        // ==================== 便捷API ====================

        /// <summary>
        /// Ping服务�?        /// </summary>
        public async UniTask<bool> PingAsync()
        {
            try
            {
                var response = await CallAsync("ping");
                return response["result"]["pong"].Value<bool>();
            }
            catch (Exception e)
            {
                Debug.LogError($"[UnityRPC] Ping failed: {e.Message}");
                return false;
            }
        }

        /// <summary>
        /// 获取服务器信�?        /// </summary>
        public async UniTask<JObject> GetServerInfoAsync()
        {
            var response = await CallAsync("get_server_info");
            return response["result"] as JObject;
        }

        // ==================== 属�?====================

        public bool IsConnected => isConnected;
    }
}
