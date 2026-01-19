using System;
using System.Collections.Generic;
using System.Diagnostics;
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
    /// 统一的描述管理工具
    /// 管理Action和技能的AI描述生成、JSON导出
    /// </summary>
    public class DescriptionManagerWindow : OdinEditorWindow
    {
        private const string ACTION_DATABASE_PATH = "Assets/Data/ActionDescriptionDatabase.asset";
        private const string SKILL_DATABASE_PATH = "Assets/Data/SkillDescriptionDatabase.asset";
        private const string EXPORT_DIRECTORY = "../skill_agent/Data/Actions";
        private const string DEEPSEEK_API_KEY = "sk-e8ec7e0c860d4b7d98ffc4212ab2c138";

        [MenuItem("技能系统/描述管理器", priority = 100)]
        public static void ShowWindow()
        {
            var window = GetWindow<DescriptionManagerWindow>("描述管理器");
            window.minSize = new Vector2(1000, 700);
            window.Show();
        }

        #region 字段

        // ==================== RAG服务配置 ====================
        private const string RAG_SERVER_HOST = "127.0.0.1";
        private const int RAG_SERVER_PORT = 2024;
        
        [TitleGroup("🔧 RAG服务配置")]
        [InfoBox("配置RAG服务器地址，用于一键导出后自动重建索引", InfoMessageType.Info)]
        [LabelText("服务器地址")]
        [PropertyOrder(0)]
        [SerializeField]
        private string ragServerHost = RAG_SERVER_HOST;
        
        [TitleGroup("🔧 RAG服务配置")]
        [LabelText("服务器端口")]
        [PropertyOrder(0)]
        [SerializeField]
        private int ragServerPort = RAG_SERVER_PORT;
        
        [TitleGroup("🔧 RAG服务配置")]
        [LabelText("导出后自动重建索引")]
        [PropertyOrder(0)]
        [SerializeField]
        private bool autoRebuildIndex = true;

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

        // ==================== 步骤1: 扫描Actions ====================
        [TitleGroup("🔍 步骤1: 扫描Actions")]
        [InfoBox("扫描项目中所有的Action类型，并从数据库加载已有的描述信息", InfoMessageType.Info)]
        [Button("🔍 扫描所有Actions", ButtonSizes.Large), GUIColor(0.3f, 0.8f, 1f)]
        [PropertyOrder(1)]
        private void Step1_ScanActions()
        {
            ScanActions();
        }

        // ==================== 步骤2: AI生成描述 ====================
        [TitleGroup("🤖 步骤2: AI生成描述")]
        [InfoBox("使用DeepSeek AI为缺少描述的Action自动生成功能说明", InfoMessageType.Info)]
        [LabelText("DeepSeek API Key")]
        [PropertyOrder(2)]
        [SerializeField]
        private string deepSeekApiKey = DEEPSEEK_API_KEY;

        [TitleGroup("🤖 步骤2: AI生成描述")]
        [HorizontalGroup("🤖 步骤2: AI生成描述/Buttons")]
        [Button("🤖 生成所有缺失描述", ButtonSizes.Large), GUIColor(0.3f, 1f, 0.3f)]
        [PropertyOrder(2)]
        private void Step2_GenerateAllMissing()
        {
            GenerateAllMissingDescriptionsAsync().Forget();
        }

        [HorizontalGroup("🤖 步骤2: AI生成描述/Buttons")]
        [Button("🔄 重新生成选中项", ButtonSizes.Large), GUIColor(0.5f, 1f, 0.5f)]
        [PropertyOrder(2)]
        private void Step2_RegenerateSelected()
        {
            RegenerateSelectedDescriptionsAsync().Forget();
        }

        // ==================== 步骤3: 查看和编辑 ====================
        [TitleGroup("📝 步骤3: 查看和编辑Action列表")]
        [InfoBox("检查AI生成的描述，可以手动修改不满意的内容。勾选项可用于重新生成", InfoMessageType.Info)]
        [HorizontalGroup("📝 步骤3: 查看和编辑Action列表/Selection")]
        [Button("全选", ButtonSizes.Medium)]
        [PropertyOrder(3)]
        private void SelectAll()
        {
            foreach (var entry in actionEntries)
                entry.isSelected = true;
            Repaint();
        }

        [HorizontalGroup("📝 步骤3: 查看和编辑Action列表/Selection")]
        [Button("全不选", ButtonSizes.Medium)]
        [PropertyOrder(3)]
        private void DeselectAll()
        {
            foreach (var entry in actionEntries)
                entry.isSelected = false;
            Repaint();
        }

        [HorizontalGroup("📝 步骤3: 查看和编辑Action列表/Selection")]
        [Button("反选", ButtonSizes.Medium)]
        [PropertyOrder(3)]
        private void InvertSelection()
        {
            foreach (var entry in actionEntries)
                entry.isSelected = !entry.isSelected;
            Repaint();
        }

        [HorizontalGroup("📝 步骤3: 查看和编辑Action列表/Selection")]
        [Button("选择待生成", ButtonSizes.Medium)]
        [PropertyOrder(3)]
        private void SelectMissing()
        {
            foreach (var entry in actionEntries)
                entry.isSelected = string.IsNullOrEmpty(entry.description);
            Repaint();
        }

        [TitleGroup("📝 步骤3: 查看和编辑Action列表")]
        [TableList(ShowIndexLabels = true, AlwaysExpanded = false, IsReadOnly = false)]
        [PropertyOrder(3)]
        [SerializeField]
        private List<ActionEntry> actionEntries = new List<ActionEntry>();

        // ==================== 步骤4: 保存到数据库 ====================
        [TitleGroup("💾 步骤4: 保存到数据库")]
        [InfoBox("将编辑好的描述保存到ActionDescriptionDatabase资源文件", InfoMessageType.Info)]
        [HorizontalGroup("💾 步骤4: 保存到数据库/Buttons")]
        [Button("💾 保存所有到数据库", ButtonSizes.Large), GUIColor(1f, 0.8f, 0.3f)]
        [PropertyOrder(4)]
        private void Step4_SaveToDatabase()
        {
            SaveAllToDatabase();
        }

        [HorizontalGroup("💾 步骤4: 保存到数据库/Buttons")]
        [Button("📂 打开数据库文件", ButtonSizes.Large), GUIColor(0.8f, 0.8f, 0.8f)]
        [PropertyOrder(4)]
        private void Step4_OpenDatabase()
        {
            Selection.activeObject = actionDatabase;
            EditorGUIUtility.PingObject(actionDatabase);
        }

        [TitleGroup("💾 步骤4: 保存到数据库")]
        [InlineEditor(ObjectFieldMode = InlineEditorObjectFieldModes.Boxed)]
        [PropertyOrder(4)]
        [SerializeField]
        private ActionDescriptionDatabase actionDatabase;

        // ==================== 步骤5: 导出JSON ====================
        [TitleGroup("📤 步骤5: 导出JSON文件")]
        [InfoBox("将Action数据导出为JSON格式，供Python RAG系统使用", InfoMessageType.Info)]
        [FolderPath]
        [LabelText("导出目录")]
        [PropertyOrder(5)]
        [SerializeField]
        private string exportDirectory = EXPORT_DIRECTORY;

        [TitleGroup("📤 步骤5: 导出JSON文件")]
        [HorizontalGroup("📤 步骤5: 导出JSON文件/Buttons")]
        [Button("📤 导出所有JSON", ButtonSizes.Large), GUIColor(1f, 0.6f, 0.3f)]
        [PropertyOrder(5)]
        private void Step5_ExportJSON()
        {
            ExportActionsToJSON();
        }

        [HorizontalGroup("📤 步骤5: 导出JSON文件/Buttons")]
        [Button("📁 打开导出目录", ButtonSizes.Large), GUIColor(0.8f, 0.8f, 0.8f)]
        [PropertyOrder(5)]
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
        [TitleGroup("🔄 步骤6: 重建RAG索引")]
        [InfoBox("导出JSON后，调用RAG服务器API重建向量索引", InfoMessageType.Info)]
        [HorizontalGroup("🔄 步骤6: 重建RAG索引/Buttons")]
        [Button("🔄 重建RAG索引", ButtonSizes.Large), GUIColor(0.3f, 0.8f, 1f)]
        [PropertyOrder(6)]
        private void Step6_RebuildRAGIndex()
        {
            RebuildRAGIndexManualAsync().Forget();
        }
        
        [HorizontalGroup("🔄 步骤6: 重建RAG索引/Buttons")]
        [Button("🔍 检查服务器状态", ButtonSizes.Large), GUIColor(0.8f, 0.8f, 0.8f)]
        [PropertyOrder(6)]
        private void Step6_CheckServerStatus()
        {
            CheckRAGServerStatusAsync().Forget();
        }
        
        private async UniTaskVoid CheckRAGServerStatusAsync()
        {
            Log("\n[检查] 正在检查RAG服务器状态...");
            EditorUtility.DisplayProgressBar("检查服务器", "正在连接...", 0.5f);
            
            try
            {
                var client = new RAGClient(ragServerHost, ragServerPort, 10);
                bool completed = false;
                bool serverOnline = false;
                string statusMessage = "";
                
                var enumerator = client.CheckHealth((success, status) =>
                {
                    completed = true;
                    serverOnline = success;
                    statusMessage = success ? status : "无法连接";
                });
                
                while (enumerator.MoveNext())
                {
                    await UniTask.Yield();
                }
                
                int waitCount = 0;
                while (!completed && waitCount < 50)
                {
                    await UniTask.Delay(100);
                    waitCount++;
                }
                
                EditorUtility.ClearProgressBar();
                
                if (serverOnline)
                {
                    Log($"  ✅ RAG服务器在线: {statusMessage}");
                    EditorUtility.DisplayDialog("服务器状态", $"✅ RAG服务器在线\n\n地址: http://{ragServerHost}:{ragServerPort}\n状态: {statusMessage}", "确定");
                }
                else
                {
                    Log($"  ❌ RAG服务器离线");
                    EditorUtility.DisplayDialog("服务器状态", $"❌ RAG服务器离线\n\n地址: http://{ragServerHost}:{ragServerPort}\n\n请使用 Tools → SkillAgent → 启动服务器", "确定");
                }
            }
            catch (Exception e)
            {
                EditorUtility.ClearProgressBar();
                Log($"  ❌ 检查失败: {e.Message}");
                EditorUtility.DisplayDialog("检查失败", $"无法检查服务器状态:\n{e.Message}", "确定");
            }
        }

        // ==================== 快捷操作 ====================
        [TitleGroup("⚡ 快捷操作")]
        [InfoBox("一键完成所有步骤（扫描→生成→保存→导出→重建索引）", InfoMessageType.None)]
        [Button("⚡ 一键完成全流程", ButtonSizes.Large), GUIColor(0.2f, 1f, 0.3f)]
        [PropertyOrder(6)]
        private void QuickAction_FullWorkflow()
        {
            OneClickPublishAllAsync().Forget();
        }

        [TitleGroup("⚡ 快捷操作")]
        [HorizontalGroup("⚡ 快捷操作/Row")]
        [Button("🔄 刷新界面", ButtonSizes.Medium)]
        [PropertyOrder(6)]
        private void QuickAction_Refresh()
        {
            ScanActions();
            Repaint();
        }

        [HorizontalGroup("⚡ 快捷操作/Row")]
        [Button("🗑️ 清空日志", ButtonSizes.Medium)]
        [PropertyOrder(6)]
        private void QuickAction_ClearLogs()
        {
            operationLogs = "日志已清空\n";
            Repaint();
        }

        // ==================== 操作日志 ====================
        [TitleGroup("📋 操作日志")]
        [TextArea(10, 20)]
        [HideLabel]
        [PropertyOrder(7)]
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

        #region 一键发布流程

        private async UniTaskVoid OneClickPublishAllAsync()
        {
            string stepInfo = autoRebuildIndex 
                ? "1. 扫描所有Action\n2. AI生成缺失的描述\n3. 保存到数据库\n4. 导出JSON文件\n5. 启动RAG服务器（如未运行）\n6. 自动重建RAG索引"
                : "1. 扫描所有Action\n2. AI生成缺失的描述\n3. 保存到数据库\n4. 导出JSON文件";
            
            if (!EditorUtility.DisplayDialog(
                "确认一键发布",
                $"将依次执行以下操作:\n\n{stepInfo}\n\n是否继续?",
                "继续",
                "取消"))
            {
                return;
            }

            int totalSteps = autoRebuildIndex ? 6 : 4;
            Log($"\n{new string('=', 60)}\n[一键发布] 开始自动化流程...\n{new string('=', 60)}");

            // 步骤1: 扫描
            Log($"\n[步骤1/{totalSteps}] 扫描Actions...");
            ScanActions();
            await UniTask.Delay(500);

            // 步骤2: AI生成
            Log($"\n[步骤2/{totalSteps}] AI生成缺失描述...");
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
            Log($"\n[步骤3/{totalSteps}] 保存到数据库...");
            SaveAllToDatabaseSilent();
            await UniTask.Delay(500);

            // 步骤4: 导出JSON
            Log($"\n[步骤4/{totalSteps}] 导出JSON文件...");
            ExportActionsToJSONSilent();
            await UniTask.Delay(500);

            // 步骤5-6: 启动服务器并重建RAG索引
            bool indexSuccess = false;
            string indexMessage = "";
            
            if (autoRebuildIndex)
            {
                // 步骤5: 检查并启动服务器
                Log($"\n[步骤5/{totalSteps}] 检查RAG服务器状态...");
                bool serverReady = await EnsureRAGServerRunningAsync();
                
                if (serverReady)
                {
                    // 步骤6: 重建索引
                    Log($"\n[步骤6/{totalSteps}] 自动重建RAG索引...");
                    (indexSuccess, indexMessage) = await RebuildRAGIndexAsync();
                }
                else
                {
                    indexMessage = "服务器启动失败或超时";
                    Log($"  ❌ {indexMessage}");
                }
            }

            Log($"\n{new string('=', 60)}\n[一键发布] 流程完成!\n{new string('=', 60)}");

            // 显示完成对话框
            if (autoRebuildIndex && indexSuccess)
            {
                EditorUtility.DisplayDialog(
                    "一键发布完成",
                    $"所有操作已完成!\n\n" +
                    $"✅ Action总数: {TotalActions}\n" +
                    $"✅ 已生成描述: {GeneratedActions}\n" +
                    $"✅ JSON已导出\n" +
                    $"✅ RAG索引已重建\n\n" +
                    $"{indexMessage}",
                    "确定"
                );
            }
            else if (autoRebuildIndex && !indexSuccess)
            {
                var choice = EditorUtility.DisplayDialogComplex(
                    "一键发布完成（索引重建失败）",
                    $"导出操作已完成，但RAG索引重建失败!\n\n" +
                    $"✅ Action总数: {TotalActions}\n" +
                    $"✅ 已生成描述: {GeneratedActions}\n" +
                    $"✅ JSON已导出\n" +
                    $"❌ RAG索引重建失败: {indexMessage}\n\n" +
                    $"请确保RAG服务器已启动 (http://{ragServerHost}:{ragServerPort})",
                    "手动重建索引",
                    "稍后操作",
                    "确定"
                );
                
                if (choice == 0)
                {
                    // 重试重建索引
                    RebuildRAGIndexManualAsync().Forget();
                }
            }
            else
            {
                EditorUtility.DisplayDialog(
                    "一键发布完成",
                    $"所有操作已完成!\n\n" +
                    $"✅ Action总数: {TotalActions}\n" +
                    $"✅ 已生成描述: {GeneratedActions}\n" +
                    $"✅ JSON已导出\n\n" +
                    $"⚠️ 请手动重建RAG索引",
                    "确定"
                );
            }
        }
        
        /// <summary>
        /// 确保RAG服务器正在运行，如果没有则自动启动
        /// </summary>
        private async UniTask<bool> EnsureRAGServerRunningAsync()
        {
            // 检查服务器是否已运行
            if (IsRAGServerRunning())
            {
                Log("  ✅ RAG服务器已在运行");
                return true;
            }
            
            Log("  ⚠️ RAG服务器未运行，正在启动...");
            EditorUtility.DisplayProgressBar("启动RAG服务器", "正在启动服务器，请稍候...", 0.2f);
            
            try
            {
                // 调用 SkillAgentServerManager 启动服务器
                SkillAgentServerManager.StartServer();
                
                // 等待服务器启动（最多等待30秒）
                int maxWaitSeconds = 30;
                for (int i = 0; i < maxWaitSeconds; i++)
                {
                    EditorUtility.DisplayProgressBar(
                        "启动RAG服务器", 
                        $"等待服务器启动... ({i + 1}/{maxWaitSeconds}秒)", 
                        0.2f + 0.6f * i / maxWaitSeconds
                    );
                    
                    await UniTask.Delay(1000);
                    
                    if (IsRAGServerRunning())
                    {
                        EditorUtility.ClearProgressBar();
                        Log($"  ✅ RAG服务器启动成功（等待了 {i + 1} 秒）");
                        // 额外等待1秒确保服务完全就绪
                        await UniTask.Delay(1000);
                        return true;
                    }
                }
                
                EditorUtility.ClearProgressBar();
                Log($"  ❌ RAG服务器启动超时（{maxWaitSeconds}秒）");
                return false;
            }
            catch (Exception e)
            {
                EditorUtility.ClearProgressBar();
                Log($"  ❌ 启动服务器异常: {e.Message}");
                return false;
            }
        }
        
        /// <summary>
        /// 检查RAG服务器是否正在运行
        /// </summary>
        private bool IsRAGServerRunning()
        {
            return IsPortOpen(ragServerHost, ragServerPort);
        }
        
        /// <summary>
        /// 检查端口是否开放
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
        /// 异步重建RAG索引
        /// </summary>
        private async UniTask<(bool success, string message)> RebuildRAGIndexAsync()
        {
            try
            {
                EditorUtility.DisplayProgressBar("重建RAG索引", "正在连接RAG服务器...", 0.1f);
                
                var client = new RAGClient(ragServerHost, ragServerPort, 120);
                bool completed = false;
                bool success = false;
                string message = "";
                
                // 使用EditorCoroutineUtility运行协程
                EditorApplication.update += CheckCompletion;
                var enumerator = client.RebuildIndex((s, response, error) =>
                {
                    completed = true;
                    if (s && response != null)
                    {
                        success = true;
                        int skillCount = response.skill_index?.count ?? 0;
                        int actionCount = response.action_index?.count ?? 0;
                        message = $"技能索引: {skillCount} 个\nAction索引: {actionCount} 个";
                        Log($"  ✅ RAG索引重建成功");
                        Log($"     技能索引: {skillCount} 个");
                        Log($"     Action索引: {actionCount} 个");
                    }
                    else
                    {
                        success = false;
                        message = error ?? "未知错误";
                        Log($"  ❌ RAG索引重建失败: {message}");
                    }
                });
                
                // 手动驱动协程
                while (enumerator.MoveNext())
                {
                    EditorUtility.DisplayProgressBar("重建RAG索引", "正在重建索引，请稍候...", 0.5f);
                    await UniTask.Yield();
                }
                
                // 等待回调完成
                int waitCount = 0;
                while (!completed && waitCount < 100)
                {
                    await UniTask.Delay(100);
                    waitCount++;
                }
                
                void CheckCompletion() { }
                EditorApplication.update -= CheckCompletion;
                EditorUtility.ClearProgressBar();
                
                return (success, message);
            }
            catch (Exception e)
            {
                EditorUtility.ClearProgressBar();
                Log($"  ❌ RAG索引重建异常: {e.Message}");
                return (false, e.Message);
            }
        }
        
        /// <summary>
        /// 手动重建RAG索引（带UI反馈）
        /// </summary>
        private async UniTaskVoid RebuildRAGIndexManualAsync()
        {
            Log("\n[手动重建] 开始重建RAG索引...");
            var (success, message) = await RebuildRAGIndexAsync();
            
            if (success)
            {
                EditorUtility.DisplayDialog("索引重建成功", $"RAG索引已成功重建!\n\n{message}", "确定");
            }
            else
            {
                EditorUtility.DisplayDialog("索引重建失败", $"RAG索引重建失败!\n\n{message}\n\n请检查RAG服务器是否已启动。", "确定");
            }
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
