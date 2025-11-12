using System;
using System.Diagnostics;
using System.IO;
using System.Net.Sockets;
using UnityEditor;
using UnityEngine;
using Debug = UnityEngine.Debug;

namespace RAGSystem.Editor
{
    /// <summary>
    /// SkillRAG服务器管理器（Unity Editor）
    /// 提供从Unity启动/停止Python服务器的功能
    /// </summary>
    public static class SkillRAGServerManager
    {
        // ==================== 配置 ====================

        private const string SERVER_SCRIPT_PATH = "快速启动(Unity).bat";  // Unity专用启动脚本
        private const string INSTALL_DEPS_SCRIPT = "安装依赖.bat";        // 依赖安装脚本
        private const string WEB_UI_URL = "http://127.0.0.1:7860";
        private const int WEB_UI_PORT = 7860;
        private const int RPC_PORT = 8766;
        private const string PROCESS_ID_KEY = "SkillRAG_ServerProcessID";

        private static Process serverProcess;

        // ==================== Unity菜单 ====================

        [MenuItem("Tools/SkillRAG/启动服务器 (Start Server)", priority = 1)]
        public static void StartServer()
        {
            if (IsServerRunning())
            {
                EditorUtility.DisplayDialog(
                    "SkillRAG服务器",
                    "服务器已在运行中！\n\n" +
                    $"Web UI: {WEB_UI_URL}\n" +
                    $"RPC端口: {RPC_PORT}",
                    "确定"
                );
                OpenWebUI();
                return;
            }

            Debug.Log("[SkillRAG] 正在启动服务器...");

            try
            {
                // 查找bat文件路径
                string batPath = FindServerBatchFile();

                if (string.IsNullOrEmpty(batPath))
                {
                    EditorUtility.DisplayDialog(
                        "错误",
                        $"未找到启动脚本：{SERVER_SCRIPT_PATH}\n\n" +
                        "请确保SkillRAG文件夹在项目根目录。",
                        "确定"
                    );
                    return;
                }

                // 启动进程
                ProcessStartInfo startInfo = new ProcessStartInfo
                {
                    FileName = batPath,
                    WorkingDirectory = Path.GetDirectoryName(batPath),
                    UseShellExecute = true, // 需要shell执行bat
                    CreateNoWindow = false,  // 显示控制台窗口（方便查看日志）
                };

                serverProcess = Process.Start(startInfo);

                if (serverProcess != null)
                {
                    // 保存进程ID
                    EditorPrefs.SetInt(PROCESS_ID_KEY, serverProcess.Id);

                    Debug.Log($"[SkillRAG] 服务器已启动（PID: {serverProcess.Id}）");
                    Debug.Log($"[SkillRAG] Web UI启动中，请稍候...");

                    // 等待服务器启动后自动打开浏览器
                    EditorApplication.delayCall += () =>
                    {
                        WaitAndOpenBrowser();
                    };
                }
                else
                {
                    Debug.LogError("[SkillRAG] 启动服务器失败");
                }
            }
            catch (Exception e)
            {
                Debug.LogError($"[SkillRAG] 启动服务器异常: {e.Message}");
                EditorUtility.DisplayDialog(
                    "启动失败",
                    $"启动服务器时发生错误：\n{e.Message}\n\n" +
                    "请检查：\n" +
                    "1. Python是否已安装\n" +
                    "2. API Key是否配置\n" +
                    "3. 查看控制台日志获取详细信息",
                    "确定"
                );
            }
        }

        [MenuItem("Tools/SkillRAG/停止服务器 (Stop Server)", priority = 2)]
        public static void StopServer()
        {
            if (!IsServerRunning())
            {
                EditorUtility.DisplayDialog(
                    "SkillRAG服务器",
                    "服务器未运行",
                    "确定"
                );
                return;
            }

            try
            {
                int processId = EditorPrefs.GetInt(PROCESS_ID_KEY, -1);

                if (processId > 0)
                {
                    // 尝试获取进程
                    Process process = null;
                    try
                    {
                        process = Process.GetProcessById(processId);
                    }
                    catch
                    {
                        // 进程不存在
                    }

                    if (process != null && !process.HasExited)
                    {
                        process.Kill();
                        process.WaitForExit(3000);
                        Debug.Log("[SkillRAG] 服务器已停止");

                        // 同时杀掉可能的Python子进程
                        KillPythonProcesses();
                    }
                }

                EditorPrefs.DeleteKey(PROCESS_ID_KEY);
                serverProcess = null;

                EditorUtility.DisplayDialog(
                    "SkillRAG服务器",
                    "服务器已停止",
                    "确定"
                );
            }
            catch (Exception e)
            {
                Debug.LogError($"[SkillRAG] 停止服务器异常: {e.Message}");
            }
        }

        [MenuItem("Tools/SkillRAG/打开Web UI (Open Web UI)", priority = 3)]
        public static void OpenWebUI()
        {
            Application.OpenURL(WEB_UI_URL);
            Debug.Log($"[SkillRAG] 正在打开浏览器: {WEB_UI_URL}");
        }

        [MenuItem("Tools/SkillRAG/检查服务器状态 (Check Status)", priority = 4)]
        public static void CheckServerStatus()
        {
            bool webUIRunning = IsPortOpen("127.0.0.1", WEB_UI_PORT);
            bool rpcRunning = IsPortOpen("127.0.0.1", RPC_PORT);

            string status = "SkillRAG 服务器状态\n\n";
            status += $"Web UI (端口 {WEB_UI_PORT}): {(webUIRunning ? "✓ 运行中" : "✗ 未运行")}\n";
            status += $"RPC服务 (端口 {RPC_PORT}): {(rpcRunning ? "✓ 运行中" : "✗ 未运行")}\n";

            if (webUIRunning || rpcRunning)
            {
                status += $"\n访问地址: {WEB_UI_URL}";
            }

            EditorUtility.DisplayDialog("服务器状态", status, "确定");
        }

        [MenuItem("Tools/SkillRAG/---", priority = 4)]
        private static void Separator1() { } // 分隔线

        [MenuItem("Tools/SkillRAG/安装依赖 (Install Dependencies)", priority = 5)]
        public static void InstallDependencies()
        {
            string installScriptPath = FindInstallScript();

            if (string.IsNullOrEmpty(installScriptPath))
            {
                EditorUtility.DisplayDialog(
                    "错误",
                    "未找到安装脚本：" + INSTALL_DEPS_SCRIPT,
                    "确定"
                );
                return;
            }

            bool confirm = EditorUtility.DisplayDialog(
                "安装SkillRAG依赖",
                "即将打开控制台安装Python依赖包。\n\n" +
                "这可能需要几分钟时间。\n\n" +
                "注意：需要先安装Python 3.8+",
                "确定安装",
                "取消"
            );

            if (!confirm) return;

            try
            {
                ProcessStartInfo startInfo = new ProcessStartInfo
                {
                    FileName = installScriptPath,
                    WorkingDirectory = Path.GetDirectoryName(installScriptPath),
                    UseShellExecute = true,
                    CreateNoWindow = false
                };

                Process.Start(startInfo);

                Debug.Log("[SkillRAG] 依赖安装脚本已启动，请等待安装完成");
            }
            catch (Exception e)
            {
                Debug.LogError($"[SkillRAG] 启动安装脚本失败: {e.Message}");
            }
        }

        [MenuItem("Tools/SkillRAG/配置API Key", priority = 6)]
        public static void ConfigureAPIKey()
        {
            string message = "请设置环境变量或编辑配置文件：\n\n";
            message += "环境变量方式（推荐）：\n";
            message += "  DEEPSEEK_API_KEY=your-key\n";
            message += "  DASHSCOPE_API_KEY=your-qwen-key\n\n";
            message += "配置文件方式：\n";
            message += "  编辑 SkillRAG/Python/config.yaml\n";

            EditorUtility.DisplayDialog("配置API Key", message, "确定");

            // 打开配置文件目录
            string configDir = Path.Combine(GetProjectRoot(), "SkillRAG", "Python");
            if (Directory.Exists(configDir))
            {
                EditorUtility.RevealInFinder(Path.Combine(configDir, "config.yaml"));
            }
        }

        // ==================== 工具方法 ====================

        /// <summary>
        /// 查找启动脚本
        /// </summary>
        private static string FindServerBatchFile()
        {
            string projectRoot = GetProjectRoot();

            // 尝试多个可能的路径
            string[] possiblePaths = new[]
            {
                Path.Combine(projectRoot, "SkillRAG", SERVER_SCRIPT_PATH),
                Path.Combine(projectRoot, "..", "SkillRAG", SERVER_SCRIPT_PATH),
                Path.Combine(Application.dataPath, "..", "..", "SkillRAG", SERVER_SCRIPT_PATH),
            };

            foreach (string path in possiblePaths)
            {
                string fullPath = Path.GetFullPath(path);
                if (File.Exists(fullPath))
                {
                    Debug.Log($"[SkillRAG] 找到启动脚本: {fullPath}");
                    return fullPath;
                }
            }

            Debug.LogError($"[SkillRAG] 未找到启动脚本，搜索路径: {string.Join(", ", possiblePaths)}");
            return null;
        }

        /// <summary>
        /// 查找依赖安装脚本
        /// </summary>
        private static string FindInstallScript()
        {
            string projectRoot = GetProjectRoot();

            string[] possiblePaths = new[]
            {
                Path.Combine(projectRoot, "SkillRAG", INSTALL_DEPS_SCRIPT),
                Path.Combine(projectRoot, "..", "SkillRAG", INSTALL_DEPS_SCRIPT),
                Path.Combine(Application.dataPath, "..", "..", "SkillRAG", INSTALL_DEPS_SCRIPT),
            };

            foreach (string path in possiblePaths)
            {
                string fullPath = Path.GetFullPath(path);
                if (File.Exists(fullPath))
                {
                    return fullPath;
                }
            }

            return null;
        }

        /// <summary>
        /// 获取项目根目录
        /// </summary>
        private static string GetProjectRoot()
        {
            string assetsPath = Application.dataPath;
            return Path.GetFullPath(Path.Combine(assetsPath, ".."));
        }

        /// <summary>
        /// 检查服务器是否运行（通过端口检测）
        /// </summary>
        private static bool IsServerRunning()
        {
            return IsPortOpen("127.0.0.1", WEB_UI_PORT) || IsPortOpen("127.0.0.1", RPC_PORT);
        }

        /// <summary>
        /// 检查端口是否开放
        /// </summary>
        private static bool IsPortOpen(string host, int port)
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
        /// 等待服务器启动后打开浏览器
        /// </summary>
        private static async void WaitAndOpenBrowser()
        {
            int maxRetries = 30; // 最多等待30秒
            int retryCount = 0;

            while (retryCount < maxRetries)
            {
                await System.Threading.Tasks.Task.Delay(1000);

                if (IsPortOpen("127.0.0.1", WEB_UI_PORT))
                {
                    Debug.Log("[SkillRAG] 服务器启动完成，正在打开浏览器...");
                    OpenWebUI();

                    EditorUtility.DisplayDialog(
                        "SkillRAG服务器",
                        "服务器启动成功！\n\n" +
                        $"Web UI: {WEB_UI_URL}\n" +
                        $"RPC端口: {RPC_PORT}\n\n" +
                        "浏览器将自动打开，如未打开请手动访问。",
                        "确定"
                    );
                    return;
                }

                retryCount++;
            }

            Debug.LogWarning("[SkillRAG] 服务器启动超时，请检查控制台窗口的日志");
            EditorUtility.DisplayDialog(
                "启动超时",
                "服务器启动超时（30秒）\n\n" +
                "请检查启动脚本的控制台窗口查看错误信息。\n\n" +
                "常见问题：\n" +
                "1. Python未安装或版本过低\n" +
                "2. API Key未配置\n" +
                "3. 依赖包安装失败",
                "确定"
            );
        }

        /// <summary>
        /// 杀掉Python进程（清理残留）
        /// </summary>
        private static void KillPythonProcesses()
        {
            try
            {
                // 在Windows上查找并杀掉python.exe进程（仅杀掉web_ui.py相关的）
                Process[] processes = Process.GetProcessesByName("python");

                foreach (Process process in processes)
                {
                    try
                    {
                        // 检查命令行参数是否包含web_ui.py
                        string commandLine = GetProcessCommandLine(process.Id);
                        if (commandLine != null && commandLine.Contains("web_ui.py"))
                        {
                            process.Kill();
                            Debug.Log($"[SkillRAG] 已杀掉Python进程: {process.Id}");
                        }
                    }
                    catch
                    {
                        // 忽略无权限的进程
                    }
                }
            }
            catch (Exception e)
            {
                Debug.LogWarning($"[SkillRAG] 清理Python进程时出错: {e.Message}");
            }
        }

        /// <summary>
        /// 获取进程命令行（Windows）
        /// </summary>
        private static string GetProcessCommandLine(int processId)
        {
            try
            {
                using (var searcher = new System.Management.ManagementObjectSearcher(
                    $"SELECT CommandLine FROM Win32_Process WHERE ProcessId = {processId}"))
                {
                    foreach (var obj in searcher.Get())
                    {
                        return obj["CommandLine"]?.ToString();
                    }
                }
            }
            catch
            {
                // 忽略错误
            }

            return null;
        }

        // ==================== Unity编辑器关闭时清理 ====================

        [InitializeOnLoadMethod]
        private static void Initialize()
        {
            // 编辑器关闭时自动停止服务器（可选）
            // EditorApplication.quitting += () =>
            // {
            //     if (IsServerRunning())
            //     {
            //         StopServer();
            //     }
            // };

            Debug.Log("[SkillRAG] 服务器管理器已加载。使用 Tools > SkillRAG 菜单启动服务。");
        }
    }
}
