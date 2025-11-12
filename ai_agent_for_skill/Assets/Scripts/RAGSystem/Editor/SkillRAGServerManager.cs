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
    /// Skill Agent服务器管理器（Unity Editor）
    /// 提供从Unity启动/停止LangGraph + WebUI服务栈的功能
    /// 架构：LangGraph Server (2024) + Next.js WebUI (3000)
    /// </summary>
    public static class SkillRAGServerManager
    {
        // ==================== 配置 ====================

        private const string SERVER_SCRIPT_PATH = "start_webui.bat";     // 启动脚本（位于skill_agent目录）
        private const string STOP_SCRIPT_PATH = "stop_webui.bat";        // 停止脚本
        private const string WEBUI_URL = "http://127.0.0.1:3000";        // Next.js WebUI地址
        private const string API_URL = "http://127.0.0.1:2024";          // LangGraph API地址
        private const int WEBUI_PORT = 3000;                              // WebUI端口
        private const int API_PORT = 2024;                                // API端口
        private const string PROCESS_ID_KEY = "SkillAgent_ServerProcessID";

        private static Process serverProcess;

        // ==================== Unity菜单 ====================

        [MenuItem("技能系统/Skill Agent/启动服务 (Start Service)", priority = 1)]
        public static void StartServer()
        {
            if (IsServerRunning())
            {
                EditorUtility.DisplayDialog(
                    "Skill Agent",
                    "服务已在运行中！\n\n" +
                    $"WebUI: {WEBUI_URL}\n" +
                    $"API: {API_URL}\n\n" +
                    "点击确定打开WebUI界面",
                    "确定"
                );
                OpenWebUI();
                return;
            }

            Debug.Log("[Skill Agent] 正在启动服务...");

            try
            {
                // 查找bat文件路径
                string batPath = FindServerBatchFile();

                if (string.IsNullOrEmpty(batPath))
                {
                    EditorUtility.DisplayDialog(
                        "错误",
                        $"未找到启动脚本：{SERVER_SCRIPT_PATH}\n\n" +
                        "请确保skill_agent文件夹在项目根目录，且包含start_webui.bat文件。",
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

                    Debug.Log($"[Skill Agent] 服务已启动（PID: {serverProcess.Id}）");
                    Debug.Log($"[Skill Agent] LangGraph Server + WebUI 正在启动，请稍候30秒...");

                    // 等待服务器启动后自动打开浏览器
                    EditorApplication.delayCall += () =>
                    {
                        WaitAndOpenBrowser();
                    };
                }
                else
                {
                    Debug.LogError("[Skill Agent] 启动服务失败");
                }
            }
            catch (Exception e)
            {
                Debug.LogError($"[Skill Agent] 启动服务异常: {e.Message}");
                EditorUtility.DisplayDialog(
                    "启动失败",
                    $"启动服务时发生错误：\n{e.Message}\n\n" +
                    "请检查：\n" +
                    "1. Python 3.8+ 是否已安装\n" +
                    "2. Node.js 18+ 是否已安装\n" +
                    "3. DeepSeek API Key是否配置\n" +
                    "4. 查看控制台窗口的日志获取详细信息",
                    "确定"
                );
            }
        }

        [MenuItem("技能系统/Skill Agent/停止服务 (Stop Service)", priority = 2)]
        public static void StopServer()
        {
            if (!IsServerRunning())
            {
                EditorUtility.DisplayDialog(
                    "Skill Agent",
                    "服务未运行",
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
                        Debug.Log("[Skill Agent] 服务已停止");

                        // 同时杀掉可能的Python和Node子进程
                        KillChildProcesses();
                    }
                }

                EditorPrefs.DeleteKey(PROCESS_ID_KEY);
                serverProcess = null;

                EditorUtility.DisplayDialog(
                    "Skill Agent",
                    "服务已停止",
                    "确定"
                );
            }
            catch (Exception e)
            {
                Debug.LogError($"[Skill Agent] 停止服务异常: {e.Message}");
            }
        }

        [MenuItem("技能系统/Skill Agent/打开WebUI (Open WebUI)", priority = 3)]
        public static void OpenWebUI()
        {
            Application.OpenURL(WEBUI_URL);
            Debug.Log($"[Skill Agent] 正在打开浏览器: {WEBUI_URL}");
        }

        [MenuItem("技能系统/Skill Agent/检查服务状态 (Check Status)", priority = 4)]
        public static void CheckServerStatus()
        {
            bool webUIRunning = IsPortOpen("127.0.0.1", WEBUI_PORT);
            bool apiRunning = IsPortOpen("127.0.0.1", API_PORT);

            string status = "Skill Agent 服务状态\n\n";
            status += $"WebUI (端口 {WEBUI_PORT}): {(webUIRunning ? "✓ 运行中" : "✗ 未运行")}\n";
            status += $"LangGraph API (端口 {API_PORT}): {(apiRunning ? "✓ 运行中" : "✗ 未运行")}\n";

            if (webUIRunning || apiRunning)
            {
                status += $"\nWebUI地址: {WEBUI_URL}\n";
                status += $"API地址: {API_URL}";
            }
            else
            {
                status += "\n请先启动服务";
            }

            EditorUtility.DisplayDialog("服务状态", status, "确定");
        }

        [MenuItem("技能系统/Skill Agent/---", priority = 10)]
        private static void Separator1() { } // 分隔线

        [MenuItem("技能系统/Skill Agent/配置API Key", priority = 11)]
        public static void ConfigureAPIKey()
        {
            string message = "请设置DeepSeek API Key：\n\n";
            message += "方式1（推荐）- 环境变量：\n";
            message += "  DEEPSEEK_API_KEY=your-api-key\n\n";
            message += "方式2 - 配置文件：\n";
            message += "  在skill_agent目录创建.env文件\n";
            message += "  内容：DEEPSEEK_API_KEY=your-api-key\n\n";
            message += "获取API Key：https://platform.deepseek.com/";

            EditorUtility.DisplayDialog("配置API Key", message, "确定");

            // 打开配置文件目录
            string configDir = Path.Combine(GetProjectRoot(), "skill_agent");
            if (Directory.Exists(configDir))
            {
                EditorUtility.RevealInFinder(Path.Combine(configDir, "core_config.yaml"));
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
                    Debug.Log($"[Skill Agent] 找到启动脚本: {fullPath}");
                    return fullPath;
                }
            }

            Debug.LogError($"[Skill Agent] 未找到启动脚本，搜索路径: {string.Join(", ", possiblePaths)}");
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
        /// 检查服务是否运行（通过端口检测）
        /// </summary>
        private static bool IsServerRunning()
        {
            return IsPortOpen("127.0.0.1", WEBUI_PORT) || IsPortOpen("127.0.0.1", API_PORT);
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
        /// 等待服务启动后打开浏览器
        /// </summary>
        private static async void WaitAndOpenBrowser()
        {
            int maxRetries = 60; // 最多等待60秒（首次启动需要安装依赖）
            int retryCount = 0;

            while (retryCount < maxRetries)
            {
                await System.Threading.Tasks.Task.Delay(1000);

                // 检查WebUI端口（优先）或API端口
                if (IsPortOpen("127.0.0.1", WEBUI_PORT))
                {
                    Debug.Log("[Skill Agent] 服务启动完成，正在打开浏览器...");
                    OpenWebUI();

                    EditorUtility.DisplayDialog(
                        "Skill Agent",
                        "服务启动成功！\n\n" +
                        $"WebUI: {WEBUI_URL}\n" +
                        $"API: {API_URL}\n\n" +
                        "浏览器已自动打开，可以开始对话生成技能！",
                        "确定"
                    );
                    return;
                }

                retryCount++;

                // 每10秒提示一次
                if (retryCount % 10 == 0)
                {
                    Debug.Log($"[Skill Agent] 等待服务启动... ({retryCount}/60秒)");
                }
            }

            Debug.LogWarning("[Skill Agent] 服务启动超时，请检查控制台窗口的日志");
            EditorUtility.DisplayDialog(
                "启动超时",
                "服务启动超时（60秒）\n\n" +
                "请检查启动脚本的控制台窗口查看错误信息。\n\n" +
                "常见问题：\n" +
                "1. Python 3.8+ 未安装\n" +
                "2. Node.js 18+ 未安装\n" +
                "3. DeepSeek API Key未配置\n" +
                "4. 网络问题导致依赖安装失败\n\n" +
                "提示：首次启动需要安装依赖，可能需要5-10分钟",
                "确定"
            );
        }

        /// <summary>
        /// 杀掉子进程（清理残留的Python和Node进程）
        /// </summary>
        private static void KillChildProcesses()
        {
            try
            {
                // 杀掉Python进程（langgraph_server.py）
                Process[] pythonProcesses = Process.GetProcessesByName("python");
                foreach (Process process in pythonProcesses)
                {
                    try
                    {
                        string commandLine = GetProcessCommandLine(process.Id);
                        if (commandLine != null && (commandLine.Contains("langgraph_server.py") || commandLine.Contains("skill_agent")))
                        {
                            process.Kill();
                            Debug.Log($"[Skill Agent] 已杀掉Python进程: {process.Id}");
                        }
                    }
                    catch { }
                }

                // 杀掉Node.js进程（Next.js）
                Process[] nodeProcesses = Process.GetProcessesByName("node");
                foreach (Process process in nodeProcesses)
                {
                    try
                    {
                        string commandLine = GetProcessCommandLine(process.Id);
                        if (commandLine != null && commandLine.Contains("webui"))
                        {
                            process.Kill();
                            Debug.Log($"[Skill Agent] 已杀掉Node.js进程: {process.Id}");
                        }
                    }
                    catch { }
                }
            }
            catch (Exception e)
            {
                Debug.LogWarning($"[Skill Agent] 清理子进程时出错: {e.Message}");
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
            // 编辑器关闭时自动停止服务（可选）
            // EditorApplication.quitting += () =>
            // {
            //     if (IsServerRunning())
            //     {
            //         StopServer();
            //     }
            // };

            Debug.Log("[Skill Agent] 服务管理器已加载。使用 菜单 > 技能系统 > Skill Agent 启动服务。");
        }
    }
}
