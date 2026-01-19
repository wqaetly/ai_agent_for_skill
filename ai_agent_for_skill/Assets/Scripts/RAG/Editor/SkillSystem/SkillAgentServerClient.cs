using System;
using System.Net.Sockets;
using Cysharp.Threading.Tasks;
using UnityEditor;
using UnityEngine.Networking;

namespace RAG
{
    /// <summary>
    /// Handles communication with skill_agent server
    /// </summary>
    public class SkillAgentServerClient
    {
        private string serverHost;
        private int serverPort;
        private Action<string> logAction;

        public SkillAgentServerClient(string host, int port, Action<string> logAction = null)
        {
            this.serverHost = host;
            this.serverPort = port;
            this.logAction = logAction;
        }

        /// <summary>
        /// Check if the server is running
        /// </summary>
        public bool IsServerRunning()
        {
            return IsPortOpen(serverHost, serverPort);
        }

        /// <summary>
        /// Check if a specific port is open
        /// </summary>
        private bool IsPortOpen(string host, int port)
        {
            try
            {
                using (TcpClient tcpClient = new TcpClient())
                {
                    var result = tcpClient.BeginConnect(host, port, null, null);
                    bool success = result.AsyncWaitHandle.WaitOne(TimeSpan.FromMilliseconds(500));
                    if (success)
                    {
                        tcpClient.EndConnect(result);
                        return true;
                    }
                    return false;
                }
            }
            catch
            {
                return false;
            }
        }

        /// <summary>
        /// Check server status with UI feedback
        /// </summary>
        public async UniTask CheckServerStatusAsync()
        {
            Log("\n[Check] Checking skill_agent server status...");
            EditorUtility.DisplayProgressBar("Check Server", "Connecting...", 0.5f);

            try
            {
                bool serverOnline = IsServerRunning();
                EditorUtility.ClearProgressBar();

                if (serverOnline)
                {
                    Log($"  ✅ skill_agent server online");
                    EditorUtility.DisplayDialog("Server Status", $"✅ skill_agent server online\n\nAddress: http://{serverHost}:{serverPort}", "OK");
                }
                else
                {
                    Log($"  ❌ skill_agent server offline");
                    EditorUtility.DisplayDialog("Server Status", $"❌ skill_agent server offline\n\nAddress: http://{serverHost}:{serverPort}\n\nPlease use Tools → SkillAgent → Start Server", "OK");
                }
            }
            catch (Exception e)
            {
                EditorUtility.ClearProgressBar();
                Log($"  ❌ Check failed: {e.Message}");
                EditorUtility.DisplayDialog("Check Failed", $"Unable to check server status:\n{e.Message}", "OK");
            }
        }

        /// <summary>
        /// Notify server to rebuild index with UI feedback
        /// </summary>
        public async UniTask NotifyRebuildIndexAsync()
        {
            Log("\n[Notify] Notifying server to rebuild index...");
            var (success, message) = await SendRebuildNotificationAsync();

            if (success)
            {
                EditorUtility.DisplayDialog("Notification Successful", $"Notified server to rebuild index!\n\n{message}", "OK");
            }
            else
            {
                EditorUtility.DisplayDialog("Notification Failed", $"Failed to notify server!\n\n{message}\n\nPlease check if skill_agent server is running.", "OK");
            }
        }

        /// <summary>
        /// Send rebuild notification to server
        /// </summary>
        public async UniTask<(bool success, string message)> SendRebuildNotificationAsync()
        {
            try
            {
                EditorUtility.DisplayProgressBar("Notify Rebuild Index", "Connecting to skill_agent server...", 0.3f);

                string url = $"http://{serverHost}:{serverPort}/rebuild_index";
                using (var request = UnityWebRequest.PostWwwForm(url, ""))
                {
                    request.timeout = 60;
                    var operation = request.SendWebRequest();

                    while (!operation.isDone)
                    {
                        EditorUtility.DisplayProgressBar("Notify Rebuild Index", "Waiting for server response...", 0.5f);
                        await UniTask.Yield();
                    }

                    EditorUtility.ClearProgressBar();

                    if (request.result == UnityWebRequest.Result.Success)
                    {
                        Log($"  ✅ Notified server to rebuild index");
                        return (true, "Server received rebuild index request");
                    }
                    else
                    {
                        string error = request.error ?? "Unknown error";
                        Log($"  ❌ Notification failed: {error}");
                        return (false, error);
                    }
                }
            }
            catch (Exception e)
            {
                EditorUtility.ClearProgressBar();
                Log($"  ❌ Notification exception: {e.Message}");
                return (false, e.Message);
            }
        }

        /// <summary>
        /// Ensure server is running, start if not
        /// </summary>
        public async UniTask<bool> EnsureServerRunningAsync()
        {
            if (IsServerRunning())
            {
                Log("  ✅ skill_agent server already running");
                return true;
            }

            Log("  ⚠️ skill_agent server not running, starting...");
            EditorUtility.DisplayProgressBar("Start Server", "Starting skill_agent server, please wait...", 0.2f);

            try
            {
                SkillAgentServerManager.StartServer();

                int maxWaitSeconds = 30;
                for (int i = 0; i < maxWaitSeconds; i++)
                {
                    EditorUtility.DisplayProgressBar(
                        "Start Server",
                        $"Waiting for server to start... ({i + 1}/{maxWaitSeconds}s)",
                        0.2f + 0.6f * i / maxWaitSeconds
                    );

                    await UniTask.Delay(1000);

                    if (IsServerRunning())
                    {
                        EditorUtility.ClearProgressBar();
                        Log($"  ✅ skill_agent server started successfully (waited {i + 1} seconds)");
                        await UniTask.Delay(1000);
                        return true;
                    }
                }

                EditorUtility.ClearProgressBar();
                Log($"  ❌ skill_agent server startup timeout ({maxWaitSeconds}s)");
                return false;
            }
            catch (Exception e)
            {
                EditorUtility.ClearProgressBar();
                Log($"  ❌ Server startup exception: {e.Message}");
                return false;
            }
        }

        private void Log(string message)
        {
            logAction?.Invoke(message);
        }
    }
}
