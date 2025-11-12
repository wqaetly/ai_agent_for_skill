using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Reflection;
using UnityEditor;
using UnityEngine;
using Sirenix.OdinInspector;
using Sirenix.OdinInspector.Editor;
using Cysharp.Threading.Tasks;
using SkillSystem.Actions;
using SkillSystem.Editor;
using SkillSystem.Editor.Data;
using Debug = UnityEngine.Debug;

namespace SkillSystem.RAG
{
    /// <summary>
    /// 统一的描述管理工具
    /// 管理Action和技能的AI描述生成、JSON导出、RAG索引重建
    /// </summary>
    public class DescriptionManagerWindow : OdinEditorWindow
    {
        private const string ACTION_DATABASE_PATH = "Assets/Data/ActionDescriptionDatabase.asset";
        private const string SKILL_DATABASE_PATH = "Assets/Data/SkillDescriptionDatabase.asset";
        private const string EXPORT_DIRECTORY = "../SkillRAG/Data/Actions";
        private const string DEEPSEEK_API_KEY = "sk-e8ec7e0c860d4b7d98ffc4212ab2c138";

        [MenuItem("技能系统/描述管理器", priority = 100)]
        public static void ShowWindow()
        {
            var window = GetWindow<DescriptionManagerWindow>("描述管理器");
            window.minSize = new Vector2(1000, 700);
            window.Show();
        }

        #region 字段

        // ==================== 统计信息 ====================
        [TitleGroup("📊 统计信息")]
        [HorizontalGroup("📊 统计信息/Stats")]
        [ShowInInspector, ReadOnly, LabelText("Action总数")]
        [PropertyOrder(1)]
        private int TotalActions => actionEntries.Count;

        [HorizontalGroup("📊 统计信息/Stats")]
        [ShowInInspector, ReadOnly, LabelText("已生成描述")]
        [PropertyOrder(1)]
        private int GeneratedActions => actionEntries.Count(e => !string.IsNullOrEmpty(e.description));

        [HorizontalGroup("📊 统计信息/Stats")]
        [ShowInInspector, ReadOnly, LabelText("待生成")]
        [PropertyOrder(1)]
        private int PendingActions => actionEntries.Count(e => string.IsNullOrEmpty(e.description));

        [HorizontalGroup("📊 统计信息/Stats")]
        [ShowInInspector, ReadOnly, LabelText("RAG服务器")]
        [PropertyOrder(1)]
        private string RAGServerStatus => ragServerConnected ? "🟢 运行中" : "🔴 未连接";

        private bool ragServerConnected = false;
        private DateTime lastServerCheckTime = DateTime.MinValue;
        
        // 服务器进程管理
        private Process serverProcess = null;
        private bool isServerRunning = false;
        private string serverOutput = "";
        
        [TitleGroup("📊 统计信息")]
        [HorizontalGroup("📊 统计信息/ServerControl")]
        [Button("🚀 启动RAG服务器", ButtonSizes.Medium), GUIColor(0.3f, 1f, 0.3f)]
        [PropertyOrder(1)]
        [ShowIf("@!isServerRunning")]
        private void StartRAGServer()
        {
            StartServer();
        }
        
        [HorizontalGroup("📊 统计信息/ServerControl")]
        [Button("⏹️ 停止RAG服务器", ButtonSizes.Medium), GUIColor(1f, 0.5f, 0.3f)]
        [PropertyOrder(1)]
        [ShowIf("@isServerRunning")]
        private void StopRAGServer()
        {
            StopServer();
        }
        
        [HorizontalGroup("📊 统计信息/ServerControl")]
        [Button("📋 查看服务器日志", ButtonSizes.Medium), GUIColor(0.7f, 0.7f, 1f)]
        [PropertyOrder(1)]
        [ShowIf("@isServerRunning")]
        private void ViewServerLog()
        {
            Debug.Log($"[RAG Server] 输出:\n{serverOutput}");
            EditorUtility.DisplayDialog("服务器日志", 
                string.IsNullOrEmpty(serverOutput) ? "暂无日志" : serverOutput.Substring(Math.Max(0, serverOutput.Length - 1000)), 
                "确定");
        }

        // ==================== 步骤1: 扫描Actions ====================
        [TitleGroup("🔍 步骤1: 扫描Actions")]
        [InfoBox("扫描项目中所有的Action类型，并从数据库加载已有的描述信息", InfoMessageType.Info)]
        [Button("🔍 扫描所有Actions", ButtonSizes.Large), GUIColor(0.3f, 0.8f, 1f)]
        [PropertyOrder(2)]
        private void Step1_ScanActions()
        {
            ScanActions();
        }

        // ==================== 步骤2: AI生成描述 ====================
        [TitleGroup("🤖 步骤2: AI生成描述")]
        [InfoBox("使用DeepSeek AI为缺少描述的Action自动生成功能说明", InfoMessageType.Info)]
        [LabelText("DeepSeek API Key")]
        [PropertyOrder(3)]
        [SerializeField]
        private string deepSeekApiKey = DEEPSEEK_API_KEY;

        [TitleGroup("🤖 步骤2: AI生成描述")]
        [HorizontalGroup("🤖 步骤2: AI生成描述/Buttons")]
        [Button("🤖 生成所有缺失描述", ButtonSizes.Large), GUIColor(0.3f, 1f, 0.3f)]
        [PropertyOrder(3)]
        private void Step2_GenerateAllMissing()
        {
            GenerateAllMissingDescriptionsAsync().Forget();
        }

        [HorizontalGroup("🤖 步骤2: AI生成描述/Buttons")]
        [Button("🔄 重新生成选中项", ButtonSizes.Large), GUIColor(0.5f, 1f, 0.5f)]
        [PropertyOrder(3)]
        private void Step2_RegenerateSelected()
        {
            RegenerateSelectedDescriptionsAsync().Forget();
        }

        // ==================== 步骤3: 查看和编辑 ====================
        [TitleGroup("📝 步骤3: 查看和编辑Action列表")]
        [InfoBox("检查AI生成的描述，可以手动修改不满意的内容。勾选项可用于重新生成", InfoMessageType.Info)]
        [HorizontalGroup("📝 步骤3: 查看和编辑Action列表/Selection")]
        [Button("全选", ButtonSizes.Medium)]
        [PropertyOrder(4)]
        private void SelectAll()
        {
            foreach (var entry in actionEntries)
                entry.isSelected = true;
            Repaint();
        }

        [HorizontalGroup("📝 步骤3: 查看和编辑Action列表/Selection")]
        [Button("全不选", ButtonSizes.Medium)]
        [PropertyOrder(4)]
        private void DeselectAll()
        {
            foreach (var entry in actionEntries)
                entry.isSelected = false;
            Repaint();
        }

        [HorizontalGroup("📝 步骤3: 查看和编辑Action列表/Selection")]
        [Button("反选", ButtonSizes.Medium)]
        [PropertyOrder(4)]
        private void InvertSelection()
        {
            foreach (var entry in actionEntries)
                entry.isSelected = !entry.isSelected;
            Repaint();
        }

        [HorizontalGroup("📝 步骤3: 查看和编辑Action列表/Selection")]
        [Button("选择待生成", ButtonSizes.Medium)]
        [PropertyOrder(4)]
        private void SelectMissing()
        {
            foreach (var entry in actionEntries)
                entry.isSelected = string.IsNullOrEmpty(entry.description);
            Repaint();
        }

        [TitleGroup("📝 步骤3: 查看和编辑Action列表")]
        [TableList(ShowIndexLabels = true, AlwaysExpanded = false, IsReadOnly = false)]
        [PropertyOrder(4)]
        [SerializeField]
        private List<ActionEntry> actionEntries = new List<ActionEntry>();

        // ==================== 步骤4: 保存到数据库 ====================
        [TitleGroup("💾 步骤4: 保存到数据库")]
        [InfoBox("将编辑好的描述保存到ActionDescriptionDatabase资源文件", InfoMessageType.Info)]
        [HorizontalGroup("💾 步骤4: 保存到数据库/Buttons")]
        [Button("💾 保存所有到数据库", ButtonSizes.Large), GUIColor(1f, 0.8f, 0.3f)]
        [PropertyOrder(5)]
        private void Step4_SaveToDatabase()
        {
            SaveAllToDatabase();
        }

        [HorizontalGroup("💾 步骤4: 保存到数据库/Buttons")]
        [Button("📂 打开数据库文件", ButtonSizes.Large), GUIColor(0.8f, 0.8f, 0.8f)]
        [PropertyOrder(5)]
        private void Step4_OpenDatabase()
        {
            Selection.activeObject = actionDatabase;
            EditorGUIUtility.PingObject(actionDatabase);
        }

        [TitleGroup("💾 步骤4: 保存到数据库")]
        [InlineEditor(ObjectFieldMode = InlineEditorObjectFieldModes.Boxed)]
        [PropertyOrder(5)]
        [SerializeField]
        private ActionDescriptionDatabase actionDatabase;

        // ==================== 步骤5: 导出JSON ====================
        [TitleGroup("📤 步骤5: 导出JSON文件")]
        [InfoBox("将Action数据导出为JSON格式，供Python RAG系统使用", InfoMessageType.Info)]
        [FolderPath]
        [LabelText("导出目录")]
        [PropertyOrder(6)]
        [SerializeField]
        private string exportDirectory = EXPORT_DIRECTORY;

        [TitleGroup("📤 步骤5: 导出JSON文件")]
        [HorizontalGroup("📤 步骤5: 导出JSON文件/Buttons")]
        [Button("📤 导出所有JSON", ButtonSizes.Large), GUIColor(1f, 0.6f, 0.3f)]
        [PropertyOrder(6)]
        private void Step5_ExportJSON()
        {
            ExportActionsToJSON();
        }

        [HorizontalGroup("📤 步骤5: 导出JSON文件/Buttons")]
        [Button("📁 打开导出目录", ButtonSizes.Large), GUIColor(0.8f, 0.8f, 0.8f)]
        [PropertyOrder(6)]
        private void Step5_OpenExportFolder()
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

        // ==================== 步骤6: 重建RAG索引 ====================
        [TitleGroup("🔨 步骤6: 重建RAG索引")]
        [InfoBox("触发Python RAG服务器重建向量索引（需要RAG服务器运行中）", InfoMessageType.Warning)]
        [Button("🔨 重建RAG索引", ButtonSizes.Large), GUIColor(0.8f, 0.3f, 1f)]
        [PropertyOrder(7)]
        private void Step6_RebuildIndex()
        {
            RebuildRAGIndexAsync().Forget();
        }

        // ==================== 快捷操作 ====================
        [TitleGroup("⚡ 快捷操作")]
        [InfoBox("一键完成所有步骤（扫描→生成→保存→导出→索引）", InfoMessageType.None)]
        [Button("⚡ 一键完成全流程", ButtonSizes.Large), GUIColor(0.2f, 1f, 0.3f)]
        [PropertyOrder(8)]
        private void QuickAction_FullWorkflow()
        {
            OneClickPublishAllAsync().Forget();
        }

        [TitleGroup("⚡ 快捷操作")]
        [HorizontalGroup("⚡ 快捷操作/Row")]
        [Button("🔄 刷新界面", ButtonSizes.Medium)]
        [PropertyOrder(8)]
        private void QuickAction_Refresh()
        {
            ScanActions();
            Repaint();
        }

        [HorizontalGroup("⚡ 快捷操作/Row")]
        [Button("🗑️ 清空日志", ButtonSizes.Medium)]
        [PropertyOrder(8)]
        private void QuickAction_ClearLogs()
        {
            operationLogs = "日志已清空\n";
            Repaint();
        }

        // ==================== 操作日志 ====================
        [TitleGroup("📋 操作日志")]
        [TextArea(10, 20)]
        [HideLabel]
        [PropertyOrder(9)]
        [SerializeField]
        private string operationLogs = "准备就绪，等待操作...\n";

        #endregion

        #region Unity生命周期

        protected override void OnEnable()
        {
            base.OnEnable();
            LoadOrCreateDatabase();
            ScanActions();
        }

        #endregion

        #region 数据库管理

        private void LoadOrCreateDatabase()
        {
            // 加载Action数据库
            actionDatabase = AssetDatabase.LoadAssetAtPath<ActionDescriptionDatabase>(ACTION_DATABASE_PATH);

            if (actionDatabase == null)
            {
                actionDatabase = CreateInstance<ActionDescriptionDatabase>();

                string directory = Path.GetDirectoryName(ACTION_DATABASE_PATH);
                if (!Directory.Exists(directory))
                {
                    Directory.CreateDirectory(directory);
                }

                AssetDatabase.CreateAsset(actionDatabase, ACTION_DATABASE_PATH);
                AssetDatabase.SaveAssets();

                Log($"[数据库] 创建新Action数据库: {ACTION_DATABASE_PATH}");
            }
            else
            {
                Log($"[数据库] 加载Action数据库成功: {actionDatabase.totalActions} 个Action");
            }
        }

        #endregion

        #region Action扫描

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

                // 从数据库加载现有数据
                var existingData = actionDatabase?.GetDescriptionByType(type.Name);
                if (existingData != null)
                {
                    entry.displayName = existingData.displayName;
                    entry.category = existingData.category;
                    entry.description = existingData.description;
                    entry.searchKeywords = existingData.searchKeywords;
                    entry.isAIGenerated = existingData.isAIGenerated;
                    entry.hasData = true;
                }
                else
                {
                    var displayAttr = type.GetCustomAttribute<ActionDisplayNameAttribute>();
                    var categoryAttr = type.GetCustomAttribute<ActionCategoryAttribute>();

                    entry.displayName = displayAttr?.DisplayName ?? type.Name;
                    entry.category = categoryAttr?.Category ?? "Other";
                    entry.hasData = false;
                }

                entry.sourceCode = ReadActionSourceCode(type);
                actionEntries.Add(entry);
            }

            Log($"[扫描] 完成，找到 {actionEntries.Count} 个Action");
        }

        private string ReadActionSourceCode(Type type)
        {
            try
            {
                string[] guids = AssetDatabase.FindAssets($"{type.Name} t:MonoScript");
                if (guids.Length == 0)
                    return null;

                string path = AssetDatabase.GUIDToAssetPath(guids[0]);
                return File.ReadAllText(path);
            }
            catch (Exception e)
            {
                Log($"[警告] 无法读取 {type.Name} 的源代码: {e.Message}");
                return null;
            }
        }

        #endregion

        #region AI生成

        private async UniTaskVoid GenerateAllMissingDescriptionsAsync()
        {
            var missingEntries = actionEntries.Where(e => string.IsNullOrEmpty(e.description)).ToList();
            
            if (missingEntries.Count == 0)
            {
                EditorUtility.DisplayDialog("提示", "所有Action都已有描述", "确定");
                return;
            }

            await GenerateDescriptionsForEntriesAsync(missingEntries, "生成缺失描述");
        }

        private async UniTaskVoid RegenerateSelectedDescriptionsAsync()
        {
            var selectedEntries = actionEntries.Where(e => e.isSelected).ToList();
            
            if (selectedEntries.Count == 0)
            {
                EditorUtility.DisplayDialog("提示", "请先在列表中勾选要重新生成的Action", "确定");
                return;
            }

            if (!EditorUtility.DisplayDialog(
                "确认重新生成",
                $"将重新生成 {selectedEntries.Count} 个Action的描述\n原有描述将被覆盖，是否继续？",
                "继续",
                "取消"))
            {
                return;
            }

            await GenerateDescriptionsForEntriesAsync(selectedEntries, "重新生成描述");
        }

        private async UniTask GenerateDescriptionsForEntriesAsync(List<ActionEntry> entries, string operationName)
        {
            var client = new DeepSeekClient(deepSeekApiKey);

            int successCount = 0;
            int failCount = 0;
            int total = entries.Count;

            Log($"\n[{operationName}] 开始处理 {total} 个Action...");

            for (int i = 0; i < entries.Count; i++)
            {
                var entry = entries[i];

                try
                {
                    EditorUtility.DisplayProgressBar(
                        operationName,
                        $"正在生成 {entry.typeName} 的描述... ({i + 1}/{total})",
                        (float)i / total
                    );

                    if (string.IsNullOrEmpty(entry.sourceCode))
                    {
                        Log($"[跳过] {entry.typeName}: 无法读取源代码");
                        failCount++;
                        continue;
                    }

                    var result = await client.GenerateActionDescriptionAsync(
                        entry.typeName,
                        entry.sourceCode,
                        entry.displayName,
                        entry.category
                    );

                    if (result.success)
                    {
                        entry.displayName = result.displayName;
                        entry.category = result.category;
                        entry.description = result.description;
                        entry.searchKeywords = result.searchKeywords;
                        entry.isAIGenerated = true;
                        entry.hasData = true;
                        successCount++;

                        Log($"[成功] {entry.typeName} - 已生成描述 ({entry.description.Length} 字符)");
                    }
                    else
                    {
                        Log($"[失败] {entry.typeName}: {result.error}");
                        failCount++;
                    }

                    await UniTask.Delay(1000);
                }
                catch (Exception e)
                {
                    Log($"[异常] {entry.typeName}: {e.Message}");
                    failCount++;
                }
            }

            EditorUtility.ClearProgressBar();

            Log($"\n[{operationName}] 完成 - 成功: {successCount}, 失败: {failCount}");

            EditorUtility.DisplayDialog(
                $"{operationName}完成",
                $"成功: {successCount} 个\n失败: {failCount} 个\n\n请检查生成结果，然后点击【保存到数据库】",
                "确定"
            );

            Repaint();
        }

        #endregion

        #region 保存数据库

        private void SaveAllToDatabase()
        {
            if (actionDatabase == null)
            {
                EditorUtility.DisplayDialog("错误", "数据库未加载", "确定");
                return;
            }

            int savedCount = 0;

            foreach (var entry in actionEntries)
            {
                if (string.IsNullOrEmpty(entry.description))
                    continue;

                var data = new ActionDescriptionData
                {
                    typeName = entry.typeName,
                    namespaceName = entry.namespaceName,
                    displayName = entry.displayName,
                    category = entry.category,
                    description = entry.description,
                    searchKeywords = entry.searchKeywords,
                    isAIGenerated = entry.isAIGenerated,
                    aiGeneratedTime = entry.isAIGenerated ? DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss") : "",
                    lastModifiedTime = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss"),
                    lastModifiedBy = Environment.UserName
                };

                actionDatabase.AddOrUpdateAction(data);
                savedCount++;
            }

            var validTypeNames = actionEntries.Select(e => e.typeName).ToList();
            actionDatabase.CleanupMissingActions(validTypeNames);

            EditorUtility.SetDirty(actionDatabase);
            AssetDatabase.SaveAssets();

            Log($"\n[保存] 完成 - 已保存 {savedCount} 个Action到数据库");

            EditorUtility.DisplayDialog(
                "保存成功",
                $"已保存 {savedCount} 个Action的描述到数据库\n\n下一步: 点击【导出JSON文件】",
                "确定"
            );
        }

        #endregion

        #region JSON导出

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
                    $"成功导出 {successCount} 个JSON文件\n失败 {failCount} 个\n\n导出目录: {fullDirectory}\n\n下一步: 点击【重建RAG索引】",
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
            // 从反射获取完整的参数信息
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
            var parts = new List<string>
            {
                entry.displayName
            };

            if (!string.IsNullOrEmpty(entry.description))
            {
                parts.Add(entry.description);
            }

            if (!string.IsNullOrEmpty(entry.searchKeywords))
            {
                parts.Add($"关键词: {entry.searchKeywords}");
            }

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
                {
                    param.enumValues = Enum.GetNames(field.FieldType).ToList();
                }

                if (field.FieldType.IsArray)
                {
                    param.elementType = GetFriendlyTypeName(field.FieldType.GetElementType());
                }

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

        #region RAG索引重建

        /// <summary>
        /// 检查RAG服务器连接状态
        /// </summary>
        private async UniTask<bool> CheckRAGServerConnectionAsync()
        {
            try
            {
                using (var client = new EditorRAGClient())
                {
                    var status = await UniTask.RunOnThreadPool(async () =>
                    {
                        return await client.CheckHealthAsync();
                    });
                    
                    ragServerConnected = !string.IsNullOrEmpty(status);
                    lastServerCheckTime = DateTime.Now;
                    return ragServerConnected;
                }
            }
            catch
            {
                ragServerConnected = false;
                lastServerCheckTime = DateTime.Now;
                return false;
            }
        }

        /// <summary>
        /// 显示RAG服务器未连接的详细提示
        /// </summary>
        private void ShowRAGServerNotConnectedDialog()
        {
            var choice = EditorUtility.DisplayDialogComplex(
                "❌ 无法连接到RAG服务器",
                "RAG索引重建需要服务器运行。\n\n" +
                "可能原因：\n" +
                "• 服务器未启动\n" +
                "• 端口8765被占用\n" +
                "• 防火墙阻止连接\n\n" +
                "解决方法：\n" +
                "1. 点击顶部的 🚀 启动RAG服务器 按钮\n" +
                "2. 等待启动完成（约3-5秒）\n" +
                "3. 重新尝试重建索引\n\n" +
                "或者：\n" +
                "1. 打开 技能系统 > RAG查询窗口\n" +
                "2. 点击工具栏的 启动服务器 按钮\n\n" +
                "💡 提示：描述管理器的其他功能不需要服务器即可使用！",
                "打开RAG查询窗口",
                "查看排查指南",
                "取消"
            );

            switch (choice)
            {
                case 0: // 打开RAG查询窗口
                    EditorWindow.GetWindow<SkillRAGWindow>("RAG查询窗口");
                    break;
                case 1: // 查看排查指南
                    var guidePath = Path.GetFullPath("../SkillRAG/RAG索引错误排查指南.md");
                    if (File.Exists(guidePath))
                    {
                        System.Diagnostics.Process.Start(guidePath);
                    }
                    else
                    {
                        Log("[提示] 排查指南文件不存在: " + guidePath);
                    }
                    break;
            }
        }

        private async UniTaskVoid RebuildRAGIndexAsync()
        {
            try
            {
                Log($"\n[RAG] 开始重建索引...");

                // 先检查服务器连接
                Log("[RAG] 检查服务器连接...");
                bool isConnected = await CheckRAGServerConnectionAsync();
                
                if (!isConnected)
                {
                    Log("[RAG错误] 无法连接到服务器 (http://127.0.0.1:8765)");
                    ShowRAGServerNotConnectedDialog();
                    return;
                }
                
                Log("[RAG] ✅ 服务器连接正常");

                EditorUtility.DisplayProgressBar("重建RAG索引", "正在重建Action和技能索引...", 0.5f);

                // 调用RAG客户端重建索引
                using (var client = new EditorRAGClient())
                {
                    var result = await UniTask.RunOnThreadPool(async () =>
                    {
                        return await client.TriggerIndexAsync(forceRebuild: true);
                    });

                    EditorUtility.ClearProgressBar();

                    if (result.status == "success")
                    {
                        Log($"[RAG] 索引重建成功!");
                        Log($"  - 索引数量: {result.count} 个");
                        Log($"  - 耗时: {result.elapsed_time:F2} 秒");

                        EditorUtility.DisplayDialog(
                            "索引重建成功",
                            $"RAG索引已更新:\n\n" +
                            $"索引数量: {result.count} 个\n" +
                            $"耗时: {result.elapsed_time:F2} 秒\n\n" +
                            $"✅ 现在可以在RAG查询窗口中测试搜索了！",
                            "确定"
                        );
                    }
                    else
                    {
                        Log($"[RAG错误] {result.message}");
                        EditorUtility.DisplayDialog("索引重建失败", result.message, "确定");
                    }
                }
            }
            catch (Exception e)
            {
                EditorUtility.ClearProgressBar();
                Log($"[RAG异常] {e.Message}");
                
                // 提供更详细的错误信息
                var errorMessage = e.Message;
                var detailedMessage = "索引重建时发生错误。\n\n";
                
                if (errorMessage.Contains("sending the request") || 
                    errorMessage.Contains("connection") ||
                    errorMessage.Contains("refused"))
                {
                    detailedMessage += "❌ 网络连接错误\n\n" +
                        "这通常表示RAG服务器未运行。\n\n" +
                        "请按以下步骤操作：\n" +
                        "1. 点击顶部的 🚀 启动RAG服务器 按钮\n" +
                        "2. 等待启动完成（约3-5秒）\n" +
                        "3. 重新点击 🔨 重建RAG索引\n\n" +
                        "或者：\n" +
                        "1. 打开 技能系统 > RAG查询窗口\n" +
                        "2. 点击 🚀 启动服务器\n\n" +
                        $"技术细节: {errorMessage}";
                    
                    var choice = EditorUtility.DisplayDialogComplex(
                        "索引重建失败",
                        detailedMessage,
                        "打开RAG查询窗口",
                        "查看排查指南",
                        "关闭"
                    );
                    
                    if (choice == 0)
                    {
                        EditorWindow.GetWindow<SkillRAGWindow>("RAG查询窗口");
                    }
                    else if (choice == 1)
                    {
                        var guidePath = Path.GetFullPath("../SkillRAG/RAG索引错误排查指南.md");
                        if (File.Exists(guidePath))
                        {
                            System.Diagnostics.Process.Start(guidePath);
                        }
                    }
                }
                else
                {
                    EditorUtility.DisplayDialog(
                        "索引重建异常",
                        $"发生未知错误：\n\n{errorMessage}\n\n" +
                        "请查看Console获取详细信息。",
                        "确定"
                    );
                }
            }
        }
        
        /// <summary>
        /// 测试RAG服务器连接
        /// </summary>
        [TitleGroup("🔨 步骤6: 重建RAG索引")]
        [HorizontalGroup("🔨 步骤6: 重建RAG索引/Buttons")]
        [Button("🔍 测试服务器连接", ButtonSizes.Medium), GUIColor(0.3f, 0.8f, 1f)]
        [PropertyOrder(61)]
        private async void TestRAGServerConnection()
        {
            Log("\n[RAG] 测试服务器连接...");
            
            bool isConnected = await CheckRAGServerConnectionAsync();
            
            if (isConnected)
            {
                Log("[RAG] ✅ 服务器连接成功！");
                EditorUtility.DisplayDialog(
                    "✅ 连接成功",
                    "RAG服务器运行正常！\n\n" +
                    "服务器地址: http://127.0.0.1:8765\n" +
                    "状态: 运行中\n\n" +
                    "现在可以重建索引了。",
                    "确定"
                );
            }
            else
            {
                Log("[RAG] ❌ 无法连接到服务器");
                ShowRAGServerNotConnectedDialog();
            }
        }

        #endregion

        #region 一键发布流程

        private async UniTaskVoid OneClickPublishAllAsync()
        {
            if (!EditorUtility.DisplayDialog(
                "确认一键发布",
                "将依次执行以下操作:\n\n" +
                "1. 扫描所有Action\n" +
                "2. AI生成缺失的描述\n" +
                "3. 保存到数据库\n" +
                "4. 导出JSON文件\n" +
                "5. 重建RAG索引\n\n" +
                "是否继续?",
                "继续",
                "取消"))
            {
                return;
            }

            Log($"\n{new string('=', 60)}\n[一键发布] 开始自动化流程...\n{new string('=', 60)}");

            // 步骤1: 扫描
            Log("\n[步骤1/5] 扫描Actions...");
            ScanActions();
            await UniTask.Delay(500);

            // 步骤2: AI生成
            Log("\n[步骤2/5] AI生成缺失描述...");
            var missingCount = actionEntries.Count(e => string.IsNullOrEmpty(e.description));
            if (missingCount > 0)
            {
                await GenerateAllMissingDescriptionsWithoutDialogAsync();
            }
            else
            {
                Log("  所有Action都已有描述，跳过");
            }

            // 步骤3: 保存数据库
            Log("\n[步骤3/5] 保存到数据库...");
            SaveAllToDatabaseSilent();
            await UniTask.Delay(500);

            // 步骤4: 导出JSON
            Log("\n[步骤4/5] 导出JSON文件...");
            ExportActionsToJSONSilent();
            await UniTask.Delay(500);

            // 步骤5: 重建索引
            Log("\n[步骤5/5] 重建RAG索引...");
            await RebuildRAGIndexSilentAsync();

            Log($"\n{new string('=', 60)}\n[一键发布] 流程完成!\n{new string('=', 60)}");

            EditorUtility.DisplayDialog(
                "一键发布完成",
                $"所有操作已完成!\n\n" +
                $"✅ Action总数: {TotalActions}\n" +
                $"✅ 已生成描述: {GeneratedActions}\n" +
                $"✅ JSON已导出\n" +
                $"✅ RAG索引已更新\n\n" +
                $"现在可以在RAG查询窗口中测试搜索了！",
                "完成"
            );
        }

        private async UniTask GenerateAllMissingDescriptionsWithoutDialogAsync()
        {
            var client = new DeepSeekClient(deepSeekApiKey);
            var missingEntries = actionEntries.Where(e => string.IsNullOrEmpty(e.description)).ToList();
            int total = missingEntries.Count;
            int successCount = 0;
            int failCount = 0;

            for (int i = 0; i < missingEntries.Count; i++)
            {
                var entry = missingEntries[i];

                EditorUtility.DisplayProgressBar(
                    "AI生成描述",
                    $"正在生成 {entry.typeName}... ({i + 1}/{total})",
                    (float)i / total
                );

                if (string.IsNullOrEmpty(entry.sourceCode))
                {
                    failCount++;
                    continue;
                }

                try
                {
                    var result = await client.GenerateActionDescriptionAsync(
                        entry.typeName, entry.sourceCode, entry.displayName, entry.category);

                    if (result.success)
                    {
                        entry.displayName = result.displayName;
                        entry.category = result.category;
                        entry.description = result.description;
                        entry.searchKeywords = result.searchKeywords;
                        entry.isAIGenerated = true;
                        entry.hasData = true;
                        successCount++;
                        Log($"  ✅ {entry.typeName}");
                    }
                    else
                    {
                        failCount++;
                        Log($"  ❌ {entry.typeName}: {result.error}");
                    }

                    await UniTask.Delay(1000);
                }
                catch (Exception e)
                {
                    failCount++;
                    Log($"  ❌ {entry.typeName}: {e.Message}");
                }
            }

            EditorUtility.ClearProgressBar();
            Log($"  完成 - 成功: {successCount}, 失败: {failCount}");
        }

        private void SaveAllToDatabaseSilent()
        {
            int savedCount = 0;
            foreach (var entry in actionEntries.Where(e => !string.IsNullOrEmpty(e.description)))
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
                    aiGeneratedTime = entry.isAIGenerated ? DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss") : "",
                    lastModifiedTime = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss"),
                    lastModifiedBy = Environment.UserName
                };
                actionDatabase.AddOrUpdateAction(data);
                savedCount++;
            }

            EditorUtility.SetDirty(actionDatabase);
            AssetDatabase.SaveAssets();
            Log($"  已保存 {savedCount} 个Action");
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

        private async UniTask RebuildRAGIndexSilentAsync()
        {
            try
            {
                using (var client = new EditorRAGClient())
                {
                    var result = await UniTask.RunOnThreadPool(async () =>
                    {
                        return await client.TriggerIndexAsync(forceRebuild: true);
                    });

                    if (result.status == "success")
                    {
                        Log($"  索引重建成功: {result.count}个, 耗时 {result.elapsed_time:F2}秒");
                    }
                    else
                    {
                        Log($"  索引重建失败: {result.message}");
                    }
                }
            }
            catch (Exception e)
            {
                Log($"  索引重建异常: {e.Message}");
            }
        }

        #endregion

        #region 服务器管理

        /// <summary>
        /// 启动Python RAG服务器
        /// </summary>
        private void StartServer()
        {
            if (isServerRunning)
            {
                Log("[RAG] 服务器已在运行中");
                return;
            }

            try
            {
                // 查找Python可执行文件
                string pythonPath = FindPythonExecutable();
                if (string.IsNullOrEmpty(pythonPath))
                {
                    EditorUtility.DisplayDialog("错误", "未找到Python环境，请先安装Python 3.7+", "确定");
                    Log("[RAG错误] 未找到Python环境");
                    return;
                }

                // 构建服务器脚本路径
                string assetsPath = Application.dataPath;
                string unityProjectPath = Directory.GetParent(assetsPath).FullName;
                string rootPath = Directory.GetParent(unityProjectPath).FullName;
                string serverScriptPath = Path.Combine(rootPath, "SkillRAG", "Python", "server.py");
                serverScriptPath = Path.GetFullPath(serverScriptPath);

                Log($"[RAG] 查找服务器脚本: {serverScriptPath}");

                if (!File.Exists(serverScriptPath))
                {
                    EditorUtility.DisplayDialog("错误",
                        $"未找到服务器脚本:\n{serverScriptPath}\n\n" +
                        "请确保SkillRAG目录与ai_agent_for_skill目录在同一级",
                        "确定");
                    Log($"[RAG错误] 服务器脚本不存在: {serverScriptPath}");
                    return;
                }

                // 配置进程启动信息
                ProcessStartInfo startInfo = new ProcessStartInfo
                {
                    FileName = pythonPath,
                    Arguments = $"\"{serverScriptPath}\"",
                    UseShellExecute = false,
                    RedirectStandardOutput = true,
                    RedirectStandardError = true,
                    CreateNoWindow = true,
                    WorkingDirectory = Path.GetDirectoryName(serverScriptPath)
                };

                // 启动进程
                serverProcess = new Process { StartInfo = startInfo };

                // 监听输出
                serverProcess.OutputDataReceived += (sender, e) =>
                {
                    if (!string.IsNullOrEmpty(e.Data))
                    {
                        serverOutput += e.Data + "\n";
                        Debug.Log($"[RAG Server] {e.Data}");
                    }
                };

                serverProcess.ErrorDataReceived += (sender, e) =>
                {
                    if (!string.IsNullOrEmpty(e.Data))
                    {
                        serverOutput += "[ERROR] " + e.Data + "\n";
                        Debug.LogWarning($"[RAG Server] {e.Data}");
                    }
                };

                serverProcess.Start();
                serverProcess.BeginOutputReadLine();
                serverProcess.BeginErrorReadLine();

                isServerRunning = true;
                Log($"[RAG] 服务器已启动 (PID: {serverProcess.Id})");
                Log("[RAG] 等待服务器初始化... (约3-5秒)");

                // 等待3秒后尝试连接
                WaitAndCheckConnectionAsync().Forget();
            }
            catch (Exception e)
            {
                Log($"[RAG错误] 启动服务器失败: {e.Message}");
                EditorUtility.DisplayDialog("错误", $"启动服务器失败:\n{e.Message}", "确定");
                isServerRunning = false;
            }
        }

        /// <summary>
        /// 等待3秒后尝试连接
        /// </summary>
        private async UniTaskVoid WaitAndCheckConnectionAsync()
        {
            await UniTask.Delay(TimeSpan.FromSeconds(3));
            
            Log("[RAG] 检查服务器连接...");
            bool isConnected = await CheckRAGServerConnectionAsync();
            
            if (isConnected)
            {
                Log("[RAG] ✅ 服务器启动成功！");
                EditorUtility.DisplayDialog(
                    "✅ 服务器启动成功",
                    "RAG服务器已成功启动！\n\n" +
                    "服务器地址: http://127.0.0.1:8765\n" +
                    "状态: 运行中\n\n" +
                    "现在可以使用所有RAG功能了。",
                    "确定"
                );
            }
            else
            {
                Log("[RAG警告] 服务器可能还在初始化中，请稍后再试");
            }
        }

        /// <summary>
        /// 停止Python RAG服务器
        /// </summary>
        private void StopServer()
        {
            if (serverProcess != null && !serverProcess.HasExited)
            {
                try
                {
                    serverProcess.Kill();
                    serverProcess.WaitForExit(5000);
                    serverProcess.Dispose();
                    serverProcess = null;

                    isServerRunning = false;
                    ragServerConnected = false;
                    Log("[RAG] 服务器已停止");
                }
                catch (Exception e)
                {
                    Log($"[RAG错误] 停止服务器失败: {e.Message}");
                }
            }
            else
            {
                serverProcess = null;
                isServerRunning = false;
                Log("[RAG] 服务器未运行");
            }
        }

        /// <summary>
        /// 查找Python可执行文件
        /// </summary>
        private string FindPythonExecutable()
        {
            string[] pythonCommands = { "python", "python3", "py" };

            foreach (string cmd in pythonCommands)
            {
                try
                {
                    ProcessStartInfo startInfo = new ProcessStartInfo
                    {
                        FileName = cmd,
                        Arguments = "--version",
                        UseShellExecute = false,
                        RedirectStandardOutput = true,
                        CreateNoWindow = true
                    };

                    using (Process process = Process.Start(startInfo))
                    {
                        process.WaitForExit(2000);
                        if (process.ExitCode == 0)
                        {
                            return cmd;
                        }
                    }
                }
                catch
                {
                    // 继续尝试下一个命令
                }
            }

            return null;
        }
        
        /// <summary>
        /// 窗口关闭时清理
        /// </summary>
        private void OnDestroy()
        {
            StopServer();
        }

        #endregion

        #region 日志

        private void Log(string message)
        {
            operationLogs += $"[{DateTime.Now:HH:mm:ss}] {message}\n";

            // 限制日志长度
            if (operationLogs.Length > 10000)
            {
                operationLogs = operationLogs.Substring(operationLogs.Length - 8000);
            }

            Repaint();
        }

        #endregion

        #region 内部类

        [Serializable]
        private class ActionEntry
        {
            [TableColumnWidth(40, Resizable = false)]
            [LabelText("选择")]
            public bool isSelected;

            [TableColumnWidth(120, Resizable = false)]
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

            [TableColumnWidth(300), MultiLineProperty(3), LabelText("功能描述")]
            public string description;

            [HideInTables, LabelText("搜索关键词")]
            public string searchKeywords;

            [TableColumnWidth(80), ReadOnly, LabelText("状态")]
            [ShowInInspector]
            public string Status => hasData ? (isAIGenerated ? "✅AI生成" : "✏️手动") : "⏳待生成";

            [HideInInspector]
            public string sourceCode;

            [HideInInspector]
            public bool hasData;

            [HideInInspector]
            public bool isAIGenerated;
        }

        #endregion
    }
}
