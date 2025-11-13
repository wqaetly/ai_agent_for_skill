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
    /// SkillAgent服务器管理器（Unity Editor）
    /// 提供从Unity启动/停止Python服务器的功能
    /// </summary>
    public static class SkillAgentServerManager
    {
        // ==================== 配置 ====================

        private const string SERVER_SCRIPT_PATH = "start_webui.bat";      // 启动脚本（新架构）
        private const string INSTALL_DEPS_SCRIPT = "安装依赖.bat";        // 依赖安装脚本
        private const string WEB_UI_URL = "http://127.0.0.1:3000";        // WebUI地址（新架构）
        private const int WEB_UI_PORT = 3000;                             // WebUI端口
        private const int LANGGRAPH_PORT = 2024;                          // LangGraph后端端口
        private const string PROCESS_ID_KEY = "SkillAgent_ServerProcessID";

        private static Process serverProcess;

        // ==================== Unity菜单 ====================

        [MenuItem("Tools/SkillAgent/启动服务器 (Start Server)", priority = 1)]
        public static void StartServer()
        {
            if (IsServerRunning())
            {
                EditorUtility.DisplayDialog(
                    "SkillAgent服务器",
                    "服务器已在运行中！\n\n" +
                    $"WebUI: {WEB_UI_URL}\n" +
                    $"WebUI RAG查询: {WEB_UI_URL}/rag\n" +
                    $"LangGraph API: http://127.0.0.1:{LANGGRAPH_PORT}",
                    "确定"
                );
                OpenWebUI();
                return;
            }

            Debug.Log("[SkillAgent] 正在启动服务器...");

            try
            {
                // 查找bat文件路径
                string batPath = FindServerBatchFile();

                if (string.IsNullOrEmpty(batPath))
                {
                    EditorUtility.DisplayDialog(
                        "错误",
                        $"未找到启动脚本：{SERVER_SCRIPT_PATH}\n\n" +
                        "请确保SkillAgent文件夹在项目根目录。",
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

                    Debug.Log($"[SkillAgent] 服务器已启动（PID: {serverProcess.Id}）");
                    Debug.Log($"[SkillAgent] Web UI启动中，请稍候...");

                    // 等待服务器启动后自动打开浏览器
                    EditorApplication.delayCall += () =>
                    {
                        WaitAndOpenBrowser();
                    };
                }
                else
                {
                    Debug.LogError("[SkillAgent] 启动服务器失败");
                }
            }
            catch (Exception e)
            {
                Debug.LogError($"[SkillAgent] 启动服务器异常: {e.Message}");
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

        [MenuItem("Tools/SkillAgent/停止服务器 (Stop Server)", priority = 2)]
        public static void StopServer()
        {
            if (!IsServerRunning())
            {
                EditorUtility.DisplayDialog(
                    "SkillAgent服务器",
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
                        Debug.Log("[SkillAgent] 服务器已停止");

                        // 同时杀掉可能的Python子进程
                        KillPythonProcesses();
                    }
                }

                EditorPrefs.DeleteKey(PROCESS_ID_KEY);
                serverProcess = null;

                EditorUtility.DisplayDialog(
                    "SkillAgent服务器",
                    "服务器已停止",
                    "确定"
                );
            }
            catch (Exception e)
            {
                Debug.LogError($"[SkillAgent] 停止服务器异常: {e.Message}");
            }
        }

        [MenuItem("Tools/SkillAgent/打开Web UI (Open Web UI)", priority = 3)]
        public static void OpenWebUI()
        {
            string ragUrl = $"{WEB_UI_URL}/rag";
            Application.OpenURL(ragUrl);
            Debug.Log($"[SkillAgent] 正在打开浏览器: {ragUrl}");
        }

        [MenuItem("Tools/SkillAgent/检查服务器状态 (Check Status)", priority = 4)]
        public static void CheckServerStatus()
        {
            bool webUIRunning = IsPortOpen("127.0.0.1", WEB_UI_PORT);
            bool langgraphRunning = IsPortOpen("127.0.0.1", LANGGRAPH_PORT);

            string status = "SkillAgent服务器状态\n\n";
            status += $"WebUI (端口 {WEB_UI_PORT}): {(webUIRunning ? "✓ 运行中" : "✗ 未运行")}\n";
            status += $"LangGraph API (端口 {LANGGRAPH_PORT}): {(langgraphRunning ? "✓ 运行中" : "✗ 未运行")}\n";

            if (webUIRunning && langgraphRunning)
            {
                status += $"\n✅ 所有服务运行正常！\n";
                status += $"\nWebUI主页: {WEB_UI_URL}\n";
                status += $"RAG查询: {WEB_UI_URL}/rag\n";
                status += $"API文档: http://127.0.0.1:{LANGGRAPH_PORT}/docs";
            }
            else if (!webUIRunning && !langgraphRunning)
            {
                status += $"\n⚠️ 请先启动服务器！\n菜单: Tools → SkillAgent → 启动服务器";
            }

            EditorUtility.DisplayDialog("服务器状态", status, "确定");
        }

        [MenuItem("Tools/SkillAgent/---", priority = 4)]
        private static void Separator1() { } // 分隔线

        [MenuItem("Tools/SkillAgent/安装依赖 (Install Dependencies)", priority = 5)]
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
                "安装SkillAgent依赖",
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

                Debug.Log("[SkillAgent] 依赖安装脚本已启动，请等待安装完成");
            }
            catch (Exception e)
            {
                Debug.LogError($"[SkillAgent] 启动安装脚本失败: {e.Message}");
            }
        }

        [MenuItem("Tools/SkillAgent/配置API Key", priority = 6)]
        public static void ConfigureAPIKey()
        {
            string message = "请设置环境变量或编辑配置文件：\n\n";
            message += "环境变量方式（推荐）：\n";
            message += "  DEEPSEEK_API_KEY=your-key\n";
            message += "  DASHSCOPE_API_KEY=your-qwen-key\n\n";
            message += "配置文件方式：\n";
            message += "  编辑 SkillAgent/Python/config.yaml\n";

            EditorUtility.DisplayDialog("配置API Key", message, "确定");

            // 打开配置文件目录
            string configDir = Path.Combine(GetProjectRoot(), "skill_agent", "Python");
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
                Path.Combine(projectRoot, "skill_agent", SERVER_SCRIPT_PATH),
                Path.Combine(projectRoot, "..", "skill_agent", SERVER_SCRIPT_PATH),
                Path.Combine(Application.dataPath, "..", "..", "skill_agent", SERVER_SCRIPT_PATH),
            };

            foreach (string path in possiblePaths)
            {
                string fullPath = Path.GetFullPath(path);
                if (File.Exists(fullPath))
                {
                    Debug.Log($"[SkillAgent] 找到启动脚本: {fullPath}");
                    return fullPath;
                }
            }

            Debug.LogError($"[SkillAgent] 未找到启动脚本，搜索路径: {string.Join(", ", possiblePaths)}");
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
                Path.Combine(projectRoot, "skill_agent", INSTALL_DEPS_SCRIPT),
                Path.Combine(projectRoot, "..", "skill_agent", INSTALL_DEPS_SCRIPT),
                Path.Combine(Application.dataPath, "..", "..", "skill_agent", INSTALL_DEPS_SCRIPT),
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
            return IsPortOpen("127.0.0.1", WEB_UI_PORT) || IsPortOpen("127.0.0.1", LANGGRAPH_PORT);
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
                    Debug.Log("[SkillAgent] 服务器启动完成，正在打开浏览器...");
                    OpenWebUI();

                    EditorUtility.DisplayDialog(
                        "SkillAgent服务器",
                        "服务器启动成功！\n\n" +
                        $"WebUI: {WEB_UI_URL}\n" +
                        $"RAG查询: {WEB_UI_URL}/rag\n" +
                        $"LangGraph API: http://127.0.0.1:{LANGGRAPH_PORT}\n\n" +
                        "浏览器将自动打开到RAG查询页面。",
                        "确定"
                    );
                    return;
                }

                retryCount++;
            }

            Debug.LogWarning("[SkillAgent] 服务器启动超时，请检查控制台窗口的日志");
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
        /// 杀掉Python和Node.js进程（清理残留）
        /// 注意：这会杀掉所有python.exe和node.exe进程，请谨慎使用
        /// </summary>
        private static void KillPythonProcesses()
        {
            try
            {
                // 杀掉 Python 进程（LangGraph服务器）
                KillProcessByName("python");

                // 杀掉 Node.js 进程（WebUI）
                KillProcessByName("node");
            }
            catch (Exception e)
            {
                Debug.LogWarning($"[SkillAgent] 清理进程时出错: {e.Message}");
            }
        }

        /// <summary>
        /// 通过进程名杀掉进程
        /// </summary>
        private static void KillProcessByName(string processName)
        {
            try
            {
                Process[] processes = Process.GetProcessesByName(processName);

                foreach (Process process in processes)
                {
                    try
                    {
                        process.Kill();
                        Debug.Log($"[SkillAgent] 已杀掉{processName}进程: {process.Id}");
                    }
                    catch
                    {
                        // 忽略无权限的进程
                    }
                }

                if (processes.Length > 0)
                {
                    Debug.Log($"[SkillAgent] 共杀掉 {processes.Length} 个 {processName} 进程");
                }
            }
            catch (Exception e)
            {
                Debug.LogWarning($"[SkillAgent] 杀掉{processName}进程时出错: {e.Message}");
            }
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

            Debug.Log("[SkillAgent] 服务器管理器已加载。使用 Tools > SkillAgent菜单启动服务。");
        }
    }
}
