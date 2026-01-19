using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Net.Sockets;
using System.Reflection;
using UnityEditor;
using UnityEngine;
using Sirenix.OdinInspector;
using Sirenix.OdinInspector.Editor;
using Cysharp.Threading.Tasks;
using SkillSystem.Actions;
using SkillSystem.Editor;
using SkillSystem.Editor.Data;
using RAGSystem.Editor;
using Debug = UnityEngine.Debug;
namespace SkillSystem.RAG
{
    /// <summary>
    /// Action JSON export tool
    /// Export Action data to JSON for skill_agent to use
    /// Supports AI-powered description generation using DeepSeek
    /// </summary>
    public class DescriptionManagerWindow : OdinEditorWindow
    {
        // 配置现在从 RAGConfig 获取
        private RAGConfig Config => RAGConfig.Instance;

        [MenuItem("技能系统/Action导出工具", priority = 100)]
        public static void ShowWindow()
        {
            var window = GetWindow<DescriptionManagerWindow>("Action导出工具");
            window.minSize = new Vector2(800, 600);
            window.Show();
        }

        
        #region Fields

        // ==================== Server Configuration ====================
        // 服务器配置从 RAGConfig 获取
        private string serverHost => Config.serverHost;
        private int serverPort => Config.serverPort;
        private bool autoNotifyRebuild => Config.autoNotifyRebuild;
        
        [TitleGroup("🔧 全局配置")]
        [InfoBox("点击按钮打开RAG全局配置，可配置服务器地址、端口、Prompt模板等", InfoMessageType.Info)]
        [Button("📋 打开全局配置 (RAGConfig)", ButtonSizes.Large), GUIColor(0.8f, 0.8f, 1f)]
        [PropertyOrder(0)]
        private void OpenRAGConfig()
        {
            RAGConfig.SelectConfig();
        }

        // ==================== DeepSeek AI Configuration ====================
        [TitleGroup("🤖 AI描述生成 (DeepSeek)")]
        [InfoBox("使用DeepSeek AI自动为Action生成高质量描述，用于RAG语义搜索。API Key存储在EditorPrefs中，不会进入版本控制。", InfoMessageType.Info)]
        [LabelText("DeepSeek API Key")]
        [PropertyOrder(1)]
        [ShowInInspector]
        [OnValueChanged("SaveApiKey")]
        private string deepSeekApiKey
        {
            get => RAGConfig.DeepSeekApiKey;
            set => RAGConfig.DeepSeekApiKey = value;
        }

        [TitleGroup("🤖 AI描述生成 (DeepSeek)")]
        [HorizontalGroup("🤖 AI描述生成 (DeepSeek)/AIButtons")]
        [Button("🧠 为选中项生成描述", ButtonSizes.Large), GUIColor(0.5f, 0.8f, 1f)]
        [PropertyOrder(1)]
        [EnableIf("HasSelectedActions")]
        private void GenerateForSelected()
        {
            GenerateDescriptionsForSelectedAsync().Forget();
        }

        [HorizontalGroup("🤖 AI描述生成 (DeepSeek)/AIButtons")]
        [Button("🚀 批量生成（无描述项）", ButtonSizes.Large), GUIColor(0.3f, 0.9f, 0.5f)]
        [PropertyOrder(1)]
        private void GenerateForMissing()
        {
            GenerateDescriptionsForMissingAsync().Forget();
        }

        [TitleGroup("🤖 AI描述生成 (DeepSeek)")]
        [HorizontalGroup("🤖 AI描述生成 (DeepSeek)/AIButtons2")]
        [Button("💾 保存到数据库", ButtonSizes.Medium), GUIColor(0.9f, 0.7f, 0.3f)]
        [PropertyOrder(1)]
        private void SaveToDatabase()
        {
            SaveAllToDatabase();
        }

        [HorizontalGroup("🤖 AI描述生成 (DeepSeek)/AIButtons2")]
        [Button("✅ 全选", ButtonSizes.Medium)]
        [PropertyOrder(1)]
        private void SelectAll()
        {
            foreach (var entry in actionEntries)
                entry.isSelected = true;
            Repaint();
        }

        [HorizontalGroup("🤖 AI描述生成 (DeepSeek)/AIButtons2")]
        [Button("❌ 取消全选", ButtonSizes.Medium)]
        [PropertyOrder(1)]
        private void DeselectAll()
        {
            foreach (var entry in actionEntries)
                entry.isSelected = false;
            Repaint();
        }

        [TitleGroup("🤖 AI描述生成 (DeepSeek)")]
        [ShowInInspector, ReadOnly, LabelText("AI生成进度")]
        [PropertyOrder(1)]
        [ProgressBar(0, 100, ColorGetter = "GetProgressBarColor")]
        private float aiGenerationProgress = 0;

        private bool isGenerating = false;
        private DeepSeekClient deepSeekClient;

        private bool HasSelectedActions => actionEntries.Any(e => e.isSelected);

        private Color GetProgressBarColor()
        {
            if (aiGenerationProgress >= 100) return Color.green;
            if (aiGenerationProgress > 0) return new Color(0.3f, 0.7f, 1f);
            return Color.gray;
        }

        // ==================== Statistics ====================
        [TitleGroup("📊 统计信息")]
        [HorizontalGroup("📊 统计信息/Stats")]
        [ShowInInspector, ReadOnly, LabelText("Action总数")]
        [PropertyOrder(2)]
        private int TotalActions => actionEntries.Count;

        [HorizontalGroup("📊 统计信息/Stats")]
        [ShowInInspector, ReadOnly, LabelText("已有描述")]
        [PropertyOrder(2)]
        private int WithDescription => actionEntries.Count(e => !string.IsNullOrEmpty(e.description));

        [HorizontalGroup("📊 统计信息/Stats")]
        [ShowInInspector, ReadOnly, LabelText("已选中")]
        [PropertyOrder(2)]
        private int SelectedCount => actionEntries.Count(e => e.isSelected);

        // ==================== Export Directory ====================
        // 导出目录从 RAGConfig 获取
        private string exportDirectory => Config.exportDirectory;
        
        [TitleGroup("📤 导出JSON文件")]
        [InfoBox("将Action数据导出为JSON格式，供Python RAG系统使用", InfoMessageType.Info)]
        [ShowInInspector, ReadOnly]
        [LabelText("导出目录")]
        [PropertyOrder(3)]
        private string ExportDirectoryDisplay => Config.exportDirectory;

        [TitleGroup("📤 导出JSON文件")]
        [HorizontalGroup("📤 导出JSON文件/Buttons")]
        [Button("📤 导出所有JSON", ButtonSizes.Large), GUIColor(1f, 0.6f, 0.3f)]
        [PropertyOrder(3)]
        private void ExportJSON()
        {
            ExportActionsToJSON();
        }

        [HorizontalGroup("📤 导出JSON文件/Buttons")]
        [Button("📁 打开导出目录", ButtonSizes.Large), GUIColor(0.8f, 0.8f, 0.8f)]
        [PropertyOrder(3)]
        private void OpenExportFolder()
        {
            string fullPath = Path.GetFullPath(exportDirectory);
            if (Directory.Exists(fullPath))
            {
                System.Diagnostics.Process.Start(fullPath);
            }
            else
            {
                EditorUtility.DisplayDialog("目录不存在", $"导出目录不存在:\n{fullPath}", "确定");
            }
        }

        // ==================== Notify Server ====================
        [TitleGroup("🔄 通知服务器重建索引")]
        [InfoBox("导出JSON后，通知skill_agent服务器重建索引", InfoMessageType.Info)]
        [HorizontalGroup("🔄 通知服务器重建索引/Buttons")]
        [Button("🔄 通知重建索引", ButtonSizes.Large), GUIColor(0.3f, 0.8f, 1f)]
        [PropertyOrder(4)]
        private void NotifyRebuildIndex()
        {
            NotifyRebuildIndexAsync().Forget();
        }
        
        [HorizontalGroup("🔄 通知服务器重建索引/Buttons")]
        [Button("🔍 检查服务器状态", ButtonSizes.Large), GUIColor(0.8f, 0.8f, 0.8f)]
        [PropertyOrder(4)]
        private void CheckServerStatus()
        {
            CheckServerStatusAsync().Forget();
        }

        // ==================== Quick Actions ====================
        [TitleGroup("⚡ 快捷操作")]
        [InfoBox("一键完成（扫描→导出→通知重建索引）", InfoMessageType.None)]
        [Button("⚡ 一键导出并通知重建", ButtonSizes.Large), GUIColor(0.2f, 1f, 0.3f)]
        [PropertyOrder(5)]
        private void QuickExportAndNotify()
        {
            OneClickExportAndNotifyAsync().Forget();
        }

        [TitleGroup("⚡ 快捷操作")]
        [HorizontalGroup("⚡ 快捷操作/Row")]
        [Button("🔄 刷新Action列表", ButtonSizes.Medium)]
        [PropertyOrder(5)]
        private void RefreshActions()
        {
            ScanActions();
            Repaint();
        }

        [HorizontalGroup("⚡ 快捷操作/Row")]
        [Button("🗑️ 清空日志", ButtonSizes.Medium)]
        [PropertyOrder(5)]
        private void ClearLogs()
        {
            operationLogs = "日志已清空\n";
            Repaint();
        }

        // ==================== Action List ====================
        [TitleGroup("📋 Action列表")]
        [TableList(ShowIndexLabels = true, AlwaysExpanded = false, IsReadOnly = false)]
        [PropertyOrder(6)]
        [SerializeField]
        private List<ActionEntry> actionEntries = new List<ActionEntry>();

        // ==================== Operation Logs ====================
        [TitleGroup("📋 操作日志")]
        [TextArea(8, 15)]
        [HideLabel]
        [PropertyOrder(7)]
        [SerializeField]
        private string operationLogs = "准备就绪，等待操作...\n";

        private ActionDescriptionDatabase actionDatabase;

        #endregion

        #region Unity Lifecycle

        protected override void OnEnable()
        {
            base.OnEnable();
            // API Key 现在通过属性直接从 RAGConfig.DeepSeekApiKey 获取，无需单独加载
            LoadDatabase();
            ScanActions();
        }

        #endregion

        #region API Key Management

        private void SaveApiKey()
        {
            // API Key 通过属性 setter 自动保存到 RAGConfig.DeepSeekApiKey (EditorPrefs)
            deepSeekClient = null; // Reset client when key changes
        }

        private DeepSeekClient GetDeepSeekClient()
        {
            if (deepSeekClient == null && !string.IsNullOrEmpty(deepSeekApiKey))
            {
                deepSeekClient = new DeepSeekClient(deepSeekApiKey);
            }
            return deepSeekClient;
        }

        #endregion

        #region Database

        private void LoadDatabase()
        {
            actionDatabase = AssetDatabase.LoadAssetAtPath<ActionDescriptionDatabase>(Config.actionDatabasePath);
            if (actionDatabase != null)
            {
                Log($"[数据库] 加载成功: {actionDatabase.totalActions} 个Action");
            }
            else
            {
                Log("[数据库] 未找到数据库文件，正在创建...");
                CreateDatabase();
            }
        }

        private void CreateDatabase()
        {
            // Ensure directory exists
            string directory = Path.GetDirectoryName(Config.actionDatabasePath);
            if (!string.IsNullOrEmpty(directory) && !Directory.Exists(directory))
            {
                Directory.CreateDirectory(directory);
            }

            actionDatabase = ScriptableObject.CreateInstance<ActionDescriptionDatabase>();
            AssetDatabase.CreateAsset(actionDatabase, Config.actionDatabasePath);
            AssetDatabase.SaveAssets();
            Log("[数据库] 创建成功");
        }

        private void SaveAllToDatabase()
        {
            if (actionDatabase == null)
            {
                CreateDatabase();
            }

            int savedCount = 0;
            foreach (var entry in actionEntries)
            {
                if (!string.IsNullOrEmpty(entry.description))
                {
                    var data = new ActionDescriptionData
                    {
                        typeName = entry.typeName,
                        namespaceName = entry.namespaceName,
                        displayName = entry.displayName,
                        category = entry.category,
                        description = entry.description,
                        searchKeywords = entry.searchKeywords,
                        isAIGenerated = entry.isAIGenerated,
                        aiGeneratedTime = entry.aiGeneratedTime,
                        lastModifiedTime = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss")
                    };
                    actionDatabase.AddOrUpdateAction(data);
                    savedCount++;
                }
            }

            EditorUtility.SetDirty(actionDatabase);
            AssetDatabase.SaveAssets();
            Log($"[保存] 已保存 {savedCount} 个Action描述到数据库");
            EditorUtility.DisplayDialog("保存成功", $"已保存 {savedCount} 个Action描述到数据库", "确定");
        }

        #endregion

        #region Action Scanning

        private void ScanActions()
        {
            actionEntries.Clear();

            var actionTypes = Assembly.GetAssembly(typeof(ISkillAction))
                .GetTypes()
                .Where(t => t.IsSubclassOf(typeof(ISkillAction)) && !t.IsAbstract)
                .OrderBy(t => t.Name);

            foreach (var type in actionTypes)
            {
                var entry = new ActionEntry
                {
                    typeName = type.Name,
                    namespaceName = type.Namespace,
                    fullTypeName = $"{type.Namespace}.{type.Name}"
                };

                // Load from database if available
                var existingData = actionDatabase?.GetDescriptionByType(type.Name);
                if (existingData != null)
                {
                    entry.displayName = existingData.displayName;
                    entry.category = existingData.category;
                    entry.description = existingData.description;
                    entry.searchKeywords = existingData.searchKeywords;
                    entry.isAIGenerated = existingData.isAIGenerated;
                    entry.aiGeneratedTime = existingData.aiGeneratedTime;
                }
                else
                {
                    var displayAttr = type.GetCustomAttribute<ActionDisplayNameAttribute>();
                    var categoryAttr = type.GetCustomAttribute<ActionCategoryAttribute>();
                    entry.displayName = displayAttr?.DisplayName ?? type.Name;
                    entry.category = categoryAttr?.Category ?? "Other";
                }

                actionEntries.Add(entry);
            }

            Log($"[扫描] 完成，找到 {actionEntries.Count} 个Action");
        }

        #endregion

        #region AI Description Generation

        private async UniTaskVoid GenerateDescriptionsForSelectedAsync()
        {
            var selectedEntries = actionEntries.Where(e => e.isSelected).ToList();
            if (selectedEntries.Count == 0)
            {
                EditorUtility.DisplayDialog("无选中项", "请先选择要生成描述的Action", "确定");
                return;
            }

            await GenerateDescriptionsAsync(selectedEntries);
        }

        private async UniTaskVoid GenerateDescriptionsForMissingAsync()
        {
            var missingEntries = actionEntries.Where(e => string.IsNullOrEmpty(e.description)).ToList();
            if (missingEntries.Count == 0)
            {
                EditorUtility.DisplayDialog("无需生成", "所有Action都已有描述", "确定");
                return;
            }

            if (!EditorUtility.DisplayDialog(
                "批量生成确认",
                $"将为 {missingEntries.Count} 个缺少描述的Action生成描述\n\n预计耗时: {missingEntries.Count * 3}秒\n\n是否继续?",
                "继续",
                "取消"))
            {
                return;
            }

            await GenerateDescriptionsAsync(missingEntries);
        }

        private async UniTask GenerateDescriptionsAsync(List<ActionEntry> entries)
        {
            if (string.IsNullOrEmpty(deepSeekApiKey))
            {
                EditorUtility.DisplayDialog("API Key缺失", "请先配置DeepSeek API Key", "确定");
                return;
            }

            var client = GetDeepSeekClient();
            if (client == null)
            {
                EditorUtility.DisplayDialog("客户端初始化失败", "无法创建DeepSeek客户端", "确定");
                return;
            }

            isGenerating = true;
            aiGenerationProgress = 0;
            int successCount = 0;
            int failCount = 0;

            Log($"\n[AI生成] 开始为 {entries.Count} 个Action生成描述...");

            for (int i = 0; i < entries.Count; i++)
            {
                var entry = entries[i];
                aiGenerationProgress = (float)(i + 1) / entries.Count * 100f;

                EditorUtility.DisplayProgressBar(
                    "AI生成描述",
                    $"正在处理: {entry.typeName} ({i + 1}/{entries.Count})",
                    aiGenerationProgress / 100f);

                try
                {
                    // Get source code
                    string sourceCode = GetActionSourceCode(entry.typeName);
                    if (string.IsNullOrEmpty(sourceCode))
                    {
                        Log($"  ⚠️ {entry.typeName}: 无法获取源代码，跳过");
                        failCount++;
                        continue;
                    }

                    // Call DeepSeek API
                    var result = await client.GenerateActionDescriptionAsync(
                        entry.typeName,
                        sourceCode,
                        entry.displayName,
                        entry.category);

                    if (result.success)
                    {
                        entry.displayName = result.displayName;
                        entry.category = result.category;
                        entry.description = result.description;
                        entry.searchKeywords = result.searchKeywords;
                        entry.isAIGenerated = true;
                        entry.aiGeneratedTime = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss");

                        Log($"  ✅ {entry.typeName}: 生成成功");
                        successCount++;
                    }
                    else
                    {
                        Log($"  ❌ {entry.typeName}: {result.error}");
                        failCount++;
                    }

                    // Rate limiting - use configured interval
                    await UniTask.Delay(Config.aiRequestInterval);
                }
                catch (Exception e)
                {
                    Log($"  ❌ {entry.typeName}: 异常 - {e.Message}");
                    failCount++;
                }

                Repaint();
            }

            EditorUtility.ClearProgressBar();
            isGenerating = false;
            aiGenerationProgress = 100;

            Log($"[AI生成] 完成 - 成功: {successCount}, 失败: {failCount}");

            string message = $"生成完成!\n\n成功: {successCount}\n失败: {failCount}";
            if (successCount > 0)
            {
                message += "\n\n请点击\"保存到数据库\"保存结果";
            }
            EditorUtility.DisplayDialog("AI生成完成", message, "确定");

            Repaint();
        }

        /// <summary>
        /// Get source code of an Action class by finding its script file
        /// </summary>
        private string GetActionSourceCode(string typeName)
        {
            try
            {
                // Find the type
                var actionType = Assembly.GetAssembly(typeof(ISkillAction))
                    .GetTypes()
                    .FirstOrDefault(t => t.Name == typeName);

                if (actionType == null)
                {
                    return null;
                }

                // Try to find the script asset using Unity's MonoScript
                var guids = AssetDatabase.FindAssets($"t:MonoScript {typeName}");
                foreach (var guid in guids)
                {
                    string path = AssetDatabase.GUIDToAssetPath(guid);
                    var script = AssetDatabase.LoadAssetAtPath<MonoScript>(path);
                    if (script != null && script.GetClass() == actionType)
                    {
                        // Read the source file
                        string fullPath = Path.GetFullPath(path);
                        if (File.Exists(fullPath))
                        {
                            return File.ReadAllText(fullPath);
                        }
                    }
                }

                // Fallback: search in common action directories
                string[] searchPaths = new[]
                {
                    "Assets/Scripts/SkillSystem/Actions",
                    "Assets/Scripts/Actions",
                    "Assets/Scripts"
                };

                foreach (var searchPath in searchPaths)
                {
                    string filePath = $"{searchPath}/{typeName}.cs";
                    if (File.Exists(filePath))
                    {
                        return File.ReadAllText(filePath);
                    }

                    // Search recursively
                    if (Directory.Exists(searchPath))
                    {
                        var files = Directory.GetFiles(searchPath, $"{typeName}.cs", SearchOption.AllDirectories);
                        if (files.Length > 0)
                        {
                            return File.ReadAllText(files[0]);
                        }
                    }
                }

                return null;
            }
            catch (Exception e)
            {
                Debug.LogError($"获取Action源代码失败: {typeName} - {e.Message}");
                return null;
            }
        }

        #endregion

        #region JSON Export

        private void ExportActionsToJSON()
        {
            try
            {
                string fullDirectory = Path.GetFullPath(exportDirectory);
                if (!Directory.Exists(fullDirectory))
                {
                    Directory.CreateDirectory(fullDirectory);
                }

                int successCount = 0;
                int failCount = 0;

                Log($"\n[导出] 开始导出JSON到: {fullDirectory}");

                foreach (var entry in actionEntries)
                {
                    try
                    {
                        var actionFile = BuildActionFile(entry);
                        string json = JsonUtility.ToJson(actionFile, true);
                        string fileName = $"{entry.typeName}.json";
                        string filePath = Path.Combine(fullDirectory, fileName);

                        File.WriteAllText(filePath, json);
                        successCount++;
                    }
                    catch (Exception e)
                    {
                        Log($"[导出错误] {entry.typeName}: {e.Message}");
                        failCount++;
                    }
                }

                Log($"[导出] 完成 - 成功: {successCount}, 失败: {failCount}");

                EditorUtility.DisplayDialog(
                    "导出完成",
                    $"成功导出 {successCount} 个JSON文件\n失败 {failCount} 个\n\n导出目录: {fullDirectory}",
                    "确定"
                );
            }
            catch (Exception e)
            {
                Log($"[导出失败] {e.Message}");
                EditorUtility.DisplayDialog("导出失败", e.Message, "确定");
            }
        }

        private ActionFile BuildActionFile(ActionEntry entry)
        {
            var actionType = Assembly.GetAssembly(typeof(ISkillAction))
                .GetTypes()
                .FirstOrDefault(t => t.Name == entry.typeName);

            var definition = new ActionDefinition
            {
                typeName = entry.typeName,
                fullTypeName = entry.fullTypeName,
                namespaceName = entry.namespaceName,
                assemblyName = actionType?.Assembly.GetName().Name ?? "",
                displayName = entry.displayName,
                category = entry.category,
                description = entry.description,
                searchText = BuildSearchText(entry),
                parameters = ExtractParameters(actionType)
            };

            return new ActionFile
            {
                version = "1.0",
                exportTime = DateTime.Now.ToString("o"),
                action = definition
            };
        }

        private string BuildSearchText(ActionEntry entry)
        {
            var parts = new List<string> { entry.displayName };
            if (!string.IsNullOrEmpty(entry.description))
                parts.Add(entry.description);
            if (!string.IsNullOrEmpty(entry.searchKeywords))
                parts.Add(entry.searchKeywords);
            parts.Add($"分类: {entry.category}");
            parts.Add($"类型: {entry.typeName}");
            return string.Join("\n", parts);
        }

        private List<ActionParameterInfo> ExtractParameters(Type actionType)
        {
            if (actionType == null) return new List<ActionParameterInfo>();

            var parameters = new List<ActionParameterInfo>();
            var fields = actionType.GetFields(BindingFlags.Public | BindingFlags.Instance);

            object instance = null;
            try { instance = Activator.CreateInstance(actionType); } catch { }

            foreach (var field in fields)
            {
                if (field.DeclaringType == typeof(ISkillAction))
                    continue;

                var param = new ActionParameterInfo
                {
                    name = field.Name,
                    type = GetFriendlyTypeName(field.FieldType),
                    isArray = field.FieldType.IsArray,
                    isEnum = field.FieldType.IsEnum
                };

                if (instance != null)
                {
                    try
                    {
                        object value = field.GetValue(instance);
                        param.defaultValue = SerializeValue(value);
                    }
                    catch { param.defaultValue = "null"; }
                }

                ExtractOdinAttributes(field, param);

                if (field.FieldType.IsEnum)
                    param.enumValues = Enum.GetNames(field.FieldType).ToList();

                if (field.FieldType.IsArray)
                    param.elementType = GetFriendlyTypeName(field.FieldType.GetElementType());

                parameters.Add(param);
            }

            return parameters;
        }

        private void ExtractOdinAttributes(FieldInfo field, ActionParameterInfo param)
        {
            var labelAttr = field.GetCustomAttribute<LabelTextAttribute>();
            if (labelAttr != null) param.label = labelAttr.Text;

            var boxGroupAttr = field.GetCustomAttribute<BoxGroupAttribute>();
            if (boxGroupAttr != null) param.group = boxGroupAttr.GroupName;

            var infoBoxAttr = field.GetCustomAttribute<InfoBoxAttribute>();
            if (infoBoxAttr != null) param.infoBox = infoBoxAttr.Message;

            var minValueAttr = field.GetCustomAttribute<MinValueAttribute>();
            if (minValueAttr != null) param.constraints.minValue = minValueAttr.MinValue.ToString();

            var rangeAttr = field.GetCustomAttribute<RangeAttribute>();
            if (rangeAttr != null)
            {
                param.constraints.min = rangeAttr.min.ToString();
                param.constraints.max = rangeAttr.max.ToString();
            }
        }

        private string GetFriendlyTypeName(Type type)
        {
            if (type == null) return "unknown";
            if (type == typeof(int)) return "int";
            if (type == typeof(float)) return "float";
            if (type == typeof(double)) return "double";
            if (type == typeof(bool)) return "bool";
            if (type == typeof(string)) return "string";
            if (type == typeof(Vector2)) return "Vector2";
            if (type == typeof(Vector3)) return "Vector3";
            if (type == typeof(Vector4)) return "Vector4";
            if (type == typeof(Color)) return "Color";
            if (type == typeof(Quaternion)) return "Quaternion";

            if (type.IsArray)
                return GetFriendlyTypeName(type.GetElementType()) + "[]";

            if (type.IsGenericType && type.GetGenericTypeDefinition() == typeof(List<>))
                return "List<" + GetFriendlyTypeName(type.GetGenericArguments()[0]) + ">";

            return type.Name;
        }

        private string SerializeValue(object value)
        {
            if (value == null) return "null";
            if (value is string str) return $"\"{str}\"";
            if (value is bool b) return b.ToString().ToLower();
            if (value is int || value is float || value is double) return value.ToString();
            if (value is Vector2 v2) return $"({v2.x}, {v2.y})";
            if (value is Vector3 v3) return $"({v3.x}, {v3.y}, {v3.z})";
            if (value is Vector4 v4) return $"({v4.x}, {v4.y}, {v4.z}, {v4.w})";
            if (value is Color c) return $"RGBA({c.r:F2}, {c.g:F2}, {c.b:F2}, {c.a:F2})";
            if (value is Quaternion q) return $"({q.x}, {q.y}, {q.z}, {q.w})";
            if (value is Enum e) return e.ToString();
            if (value.GetType().IsArray)
            {
                var array = value as Array;
                return array.Length == 0 ? "[]" : $"[{array.Length} items]";
            }
            return value.ToString();
        }

        #endregion

        #region Server Communication

        private async UniTaskVoid CheckServerStatusAsync()
        {
            Log("\n[检查] 正在检查skill_agent服务器状态...");
            EditorUtility.DisplayProgressBar("检查服务器", "正在连接...", 0.5f);
            
            try
            {
                bool serverOnline = IsServerRunning();
                EditorUtility.ClearProgressBar();
                
                if (serverOnline)
                {
                    Log($"  ✅ skill_agent服务器在线");
                    EditorUtility.DisplayDialog("服务器状态", $"✅ skill_agent服务器在线\n\n地址: http://{serverHost}:{serverPort}", "确定");
                }
                else
                {
                    Log($"  ❌ skill_agent服务器离线");
                    EditorUtility.DisplayDialog("服务器状态", $"❌ skill_agent服务器离线\n\n地址: http://{serverHost}:{serverPort}\n\n请使用 Tools → SkillAgent → 启动服务器", "确定");
                }
            }
            catch (Exception e)
            {
                EditorUtility.ClearProgressBar();
                Log($"  ❌ 检查失败: {e.Message}");
                EditorUtility.DisplayDialog("检查失败", $"无法检查服务器状态:\n{e.Message}", "确定");
            }
        }

        private async UniTaskVoid NotifyRebuildIndexAsync()
        {
            Log("\n[通知] 正在通知服务器重建索引...");
            var (success, message) = await SendRebuildNotificationAsync();
            
            if (success)
            {
                EditorUtility.DisplayDialog("通知成功", $"已通知服务器重建索引!\n\n{message}", "确定");
            }
            else
            {
                EditorUtility.DisplayDialog("通知失败", $"通知服务器失败!\n\n{message}\n\n请检查skill_agent服务器是否已启动。", "确定");
            }
        }

        private async UniTask<(bool success, string message)> SendRebuildNotificationAsync()
        {
            try
            {
                EditorUtility.DisplayProgressBar("通知重建索引", "正在连接skill_agent服务器...", 0.3f);
                
                // Simple HTTP request to notify server
                string url = $"http://{serverHost}:{serverPort}/rebuild_index";
                using (var request = UnityEngine.Networking.UnityWebRequest.PostWwwForm(url, ""))
                {
                    request.timeout = 60;
                    var operation = request.SendWebRequest();
                    
                    while (!operation.isDone)
                    {
                        EditorUtility.DisplayProgressBar("通知重建索引", "正在等待服务器响应...", 0.5f);
                        await UniTask.Yield();
                    }
                    
                    EditorUtility.ClearProgressBar();
                    
                    if (request.result == UnityEngine.Networking.UnityWebRequest.Result.Success)
                    {
                        Log($"  ✅ 已通知服务器重建索引");
                        return (true, "服务器已收到重建索引请求");
                    }
                    else
                    {
                        string error = request.error ?? "未知错误";
                        Log($"  ❌ 通知失败: {error}");
                        return (false, error);
                    }
                }
            }
            catch (Exception e)
            {
                EditorUtility.ClearProgressBar();
                Log($"  ❌ 通知异常: {e.Message}");
                return (false, e.Message);
            }
        }

        private bool IsServerRunning()
        {
            return IsPortOpen(serverHost, serverPort);
        }

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

        private async UniTask<bool> EnsureServerRunningAsync()
        {
            if (IsServerRunning())
            {
                Log("  ✅ skill_agent服务器已在运行");
                return true;
            }
            
            Log("  ⚠️ skill_agent服务器未运行，正在启动...");
            EditorUtility.DisplayProgressBar("启动服务器", "正在启动skill_agent服务器，请稍候...", 0.2f);
            
            try
            {
                SkillAgentServerManager.StartServer();
                
                int maxWaitSeconds = 30;
                for (int i = 0; i < maxWaitSeconds; i++)
                {
                    EditorUtility.DisplayProgressBar(
                        "启动服务器", 
                        $"等待服务器启动... ({i + 1}/{maxWaitSeconds}秒)", 
                        0.2f + 0.6f * i / maxWaitSeconds
                    );
                    
                    await UniTask.Delay(1000);
                    
                    if (IsServerRunning())
                    {
                        EditorUtility.ClearProgressBar();
                        Log($"  ✅ skill_agent服务器启动成功（等待了 {i + 1} 秒）");
                        await UniTask.Delay(1000);
                        return true;
                    }
                }
                
                EditorUtility.ClearProgressBar();
                Log($"  ❌ skill_agent服务器启动超时（{maxWaitSeconds}秒）");
                return false;
            }
            catch (Exception e)
            {
                EditorUtility.ClearProgressBar();
                Log($"  ❌ 启动服务器异常: {e.Message}");
                return false;
            }
        }

        #endregion

        #region One-Click Export and Notify

        private async UniTaskVoid OneClickExportAndNotifyAsync()
        {
            string stepInfo = autoNotifyRebuild 
                ? "1. 扫描所有Action\n2. 导出JSON文件\n3. 启动skill_agent服务器（如未运行）\n4. 通知服务器重建索引"
                : "1. 扫描所有Action\n2. 导出JSON文件";
            
            if (!EditorUtility.DisplayDialog(
                "确认导出",
                $"将依次执行以下操作:\n\n{stepInfo}\n\n是否继续?",
                "继续",
                "取消"))
            {
                return;
            }

            int totalSteps = autoNotifyRebuild ? 4 : 2;
            Log($"\n{new string('=', 60)}\n[一键导出] 开始自动化流程...\n{new string('=', 60)}");

            // Step 1: Scan
            Log($"\n[步骤1/{totalSteps}] 扫描Actions...");
            ScanActions();
            await UniTask.Delay(500);

            // Step 2: Export JSON
            Log($"\n[步骤2/{totalSteps}] 导出JSON文件...");
            ExportActionsToJSONSilent();
            await UniTask.Delay(500);

            // Step 3-4: Start server and notify rebuild
            bool notifySuccess = false;
            string notifyMessage = "";
            
            if (autoNotifyRebuild)
            {
                Log($"\n[步骤3/{totalSteps}] 检查skill_agent服务器状态...");
                bool serverReady = await EnsureServerRunningAsync();
                
                if (serverReady)
                {
                    Log($"\n[步骤4/{totalSteps}] 通知服务器重建索引...");
                    (notifySuccess, notifyMessage) = await SendRebuildNotificationAsync();
                }
                else
                {
                    notifyMessage = "服务器启动失败或超时";
                    Log($"  ❌ {notifyMessage}");
                }
            }

            Log($"\n{new string('=', 60)}\n[一键导出] 流程完成!\n{new string('=', 60)}");

            // Show completion dialog
            if (autoNotifyRebuild && notifySuccess)
            {
                EditorUtility.DisplayDialog(
                    "导出完成",
                    $"所有操作已完成!\n\n" +
                    $"✅ Action总数: {TotalActions}\n" +
                    $"✅ JSON已导出\n" +
                    $"✅ 已通知服务器重建索引\n\n" +
                    $"{notifyMessage}",
                    "确定"
                );
            }
            else if (autoNotifyRebuild && !notifySuccess)
            {
                EditorUtility.DisplayDialog(
                    "导出完成（通知失败）",
                    $"导出操作已完成，但通知服务器失败!\n\n" +
                    $"✅ Action总数: {TotalActions}\n" +
                    $"✅ JSON已导出\n" +
                    $"❌ 通知服务器失败: {notifyMessage}\n\n" +
                    $"请确保skill_agent服务器已启动 (http://{serverHost}:{serverPort})",
                    "确定"
                );
            }
            else
            {
                EditorUtility.DisplayDialog(
                    "导出完成",
                    $"导出操作已完成!\n\n" +
                    $"✅ Action总数: {TotalActions}\n" +
                    $"✅ JSON已导出",
                    "确定"
                );
            }
        }

        private void ExportActionsToJSONSilent()
        {
            string fullDirectory = Path.GetFullPath(exportDirectory);
            if (!Directory.Exists(fullDirectory)) Directory.CreateDirectory(fullDirectory);

            int successCount = 0;
            foreach (var entry in actionEntries)
            {
                try
                {
                    var actionFile = BuildActionFile(entry);
                    string json = JsonUtility.ToJson(actionFile, true);
                    File.WriteAllText(Path.Combine(fullDirectory, $"{entry.typeName}.json"), json);
                    successCount++;
                }
                catch { }
            }

            Log($"  已导出 {successCount} 个JSON文件");
        }

        #endregion

        #region Logging

        private void Log(string message)
        {
            operationLogs += $"[{DateTime.Now:HH:mm:ss}] {message}\n";

            if (operationLogs.Length > 10000)
            {
                operationLogs = operationLogs.Substring(operationLogs.Length - 8000);
            }

            Repaint();
        }

        #endregion

        #region Inner Classes

        [Serializable]
        private class ActionEntry
        {
            [TableColumnWidth(30, Resizable = false)]
            [LabelText("")]
            [VerticalGroup("Select")]
            public bool isSelected;

            [TableColumnWidth(150, Resizable = false)]
            [ReadOnly, LabelText("Action类型")]
            public string typeName;

            [HideInTables, ReadOnly]
            public string namespaceName;

            [HideInTables, ReadOnly]
            public string fullTypeName;

            [TableColumnWidth(100), LabelText("显示名称")]
            public string displayName;

            [TableColumnWidth(80), LabelText("分类")]
            public string category;

            [TableColumnWidth(250), LabelText("功能描述")]
            [TextArea(1, 3)]
            public string description;

            [HideInTables]
            public string searchKeywords;

            [HideInTables]
            public bool isAIGenerated;

            [HideInTables]
            public string aiGeneratedTime;
        }

        #endregion
    }
}
