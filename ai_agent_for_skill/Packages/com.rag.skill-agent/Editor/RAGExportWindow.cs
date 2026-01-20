using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEngine;
using UnityEngine.UIElements;
using RAG.BuffSystem;

namespace RAG
{
    /// <summary>
    /// 统一的 RAG 数据导出工具窗口
    /// 整合技能 Action 和 Buff 系统的数据导出功能
    /// </summary>
    public class RAGExportWindow : EditorWindow
    {
        private int selectedTab = 0;
        private Vector2 scrollPosition;
        private string logText = "";
        
        // 扫描结果缓存
        private List<ActionEntry> cachedActions;
        private List<BuffEffectEntry> cachedBuffEffects;
        private List<BuffTriggerEntry> cachedBuffTriggers;
        
        // 选择状态
        private bool selectAllActions = true;
        private bool selectAllBuffEffects = true;
        private bool selectAllBuffTriggers = true;
        private Dictionary<string, bool> actionSelections = new Dictionary<string, bool>();
        private Dictionary<string, bool> buffEffectSelections = new Dictionary<string, bool>();
        private Dictionary<string, bool> buffTriggerSelections = new Dictionary<string, bool>();

        [MenuItem("Tools/RAG System/RAG 数据导出中心", priority = 10)]
        public static void ShowWindow()
        {
            var window = GetWindow<RAGExportWindow>("RAG 数据导出");
            window.minSize = new Vector2(600, 500);
        }

        private void OnEnable()
        {
            RefreshAllData();
        }

        private void OnGUI()
        {
            // 标题栏
            EditorGUILayout.BeginHorizontal(EditorStyles.toolbar);
            GUILayout.Label("RAG 数据导出中心", EditorStyles.boldLabel);
            GUILayout.FlexibleSpace();
            if (GUILayout.Button("刷新", EditorStyles.toolbarButton, GUILayout.Width(50)))
            {
                RefreshAllData();
            }
            if (GUILayout.Button("导出全部", EditorStyles.toolbarButton, GUILayout.Width(60)))
            {
                ExportAll();
            }
            EditorGUILayout.EndHorizontal();

            // Tab 切换
            EditorGUILayout.Space(5);
            selectedTab = GUILayout.Toolbar(selectedTab, new string[] { 
                $"技能 Actions ({cachedActions?.Count ?? 0})", 
                $"Buff 效果 ({cachedBuffEffects?.Count ?? 0})", 
                $"Buff 触发器 ({cachedBuffTriggers?.Count ?? 0})",
                "导出日志"
            });
            EditorGUILayout.Space(5);

            // 内容区域
            scrollPosition = EditorGUILayout.BeginScrollView(scrollPosition);
            
            switch (selectedTab)
            {
                case 0:
                    DrawActionsTab();
                    break;
                case 1:
                    DrawBuffEffectsTab();
                    break;
                case 2:
                    DrawBuffTriggersTab();
                    break;
                case 3:
                    DrawLogTab();
                    break;
            }
            
            EditorGUILayout.EndScrollView();
        }

        #region Tab 绘制方法

        private void DrawActionsTab()
        {
            if (cachedActions == null || cachedActions.Count == 0)
            {
                EditorGUILayout.HelpBox("未找到任何 Action 类型。请确保项目中存在实现 ISkillAction 的类。", MessageType.Info);
                return;
            }

            // 全选/取消全选
            EditorGUILayout.BeginHorizontal();
            bool newSelectAll = EditorGUILayout.ToggleLeft($"全选 ({cachedActions.Count} 个 Actions)", selectAllActions, EditorStyles.boldLabel);
            if (newSelectAll != selectAllActions)
            {
                selectAllActions = newSelectAll;
                foreach (var action in cachedActions)
                    actionSelections[action.typeName] = selectAllActions;
            }
            GUILayout.FlexibleSpace();
            if (GUILayout.Button("导出选中", GUILayout.Width(80)))
            {
                ExportSelectedActions();
            }
            EditorGUILayout.EndHorizontal();
            
            EditorGUILayout.Space(5);
            
            // Action 列表
            var groupedActions = cachedActions.GroupBy(a => a.category).OrderBy(g => g.Key);
            foreach (var group in groupedActions)
            {
                EditorGUILayout.LabelField($"▼ {group.Key} ({group.Count()})", EditorStyles.boldLabel);
                EditorGUI.indentLevel++;
                foreach (var action in group)
                {
                    if (!actionSelections.ContainsKey(action.typeName))
                        actionSelections[action.typeName] = true;
                    
                    EditorGUILayout.BeginHorizontal();
                    actionSelections[action.typeName] = EditorGUILayout.ToggleLeft(
                        $"{action.displayName} ({action.typeName})", 
                        actionSelections[action.typeName]);
                    EditorGUILayout.EndHorizontal();
                }
                EditorGUI.indentLevel--;
                EditorGUILayout.Space(3);
            }
        }

        private void DrawBuffEffectsTab()
        {
            if (cachedBuffEffects == null || cachedBuffEffects.Count == 0)
            {
                EditorGUILayout.HelpBox("未找到任何 Buff 效果类型。请确保项目中存在实现 IBuffEffect 的类。", MessageType.Info);
                return;
            }

            // 全选/取消全选
            EditorGUILayout.BeginHorizontal();
            bool newSelectAll = EditorGUILayout.ToggleLeft($"全选 ({cachedBuffEffects.Count} 个效果)", selectAllBuffEffects, EditorStyles.boldLabel);
            if (newSelectAll != selectAllBuffEffects)
            {
                selectAllBuffEffects = newSelectAll;
                foreach (var effect in cachedBuffEffects)
                    buffEffectSelections[effect.typeName] = selectAllBuffEffects;
            }
            GUILayout.FlexibleSpace();
            if (GUILayout.Button("导出选中", GUILayout.Width(80)))
            {
                ExportSelectedBuffEffects();
            }
            EditorGUILayout.EndHorizontal();
            
            EditorGUILayout.Space(5);

            // 效果列表
            var groupedEffects = cachedBuffEffects.GroupBy(e => e.category).OrderBy(g => g.Key);
            foreach (var group in groupedEffects)
            {
                EditorGUILayout.LabelField($"▼ {group.Key} ({group.Count()})", EditorStyles.boldLabel);
                EditorGUI.indentLevel++;
                foreach (var effect in group)
                {
                    if (!buffEffectSelections.ContainsKey(effect.typeName))
                        buffEffectSelections[effect.typeName] = true;

                    EditorGUILayout.BeginHorizontal();
                    buffEffectSelections[effect.typeName] = EditorGUILayout.ToggleLeft(
                        $"{effect.displayName} ({effect.typeName})",
                        buffEffectSelections[effect.typeName]);
                    EditorGUILayout.EndHorizontal();
                }
                EditorGUI.indentLevel--;
                EditorGUILayout.Space(3);
            }
        }

        private void DrawBuffTriggersTab()
        {
            if (cachedBuffTriggers == null || cachedBuffTriggers.Count == 0)
            {
                EditorGUILayout.HelpBox("未找到任何 Buff 触发器类型。请确保项目中存在实现 IBuffTrigger 的类。", MessageType.Info);
                return;
            }

            // 全选/取消全选
            EditorGUILayout.BeginHorizontal();
            bool newSelectAll = EditorGUILayout.ToggleLeft($"全选 ({cachedBuffTriggers.Count} 个触发器)", selectAllBuffTriggers, EditorStyles.boldLabel);
            if (newSelectAll != selectAllBuffTriggers)
            {
                selectAllBuffTriggers = newSelectAll;
                foreach (var trigger in cachedBuffTriggers)
                    buffTriggerSelections[trigger.typeName] = selectAllBuffTriggers;
            }
            GUILayout.FlexibleSpace();
            if (GUILayout.Button("导出选中", GUILayout.Width(80)))
            {
                ExportSelectedBuffTriggers();
            }
            EditorGUILayout.EndHorizontal();

            EditorGUILayout.Space(5);

            // 触发器列表
            var groupedTriggers = cachedBuffTriggers.GroupBy(t => t.category).OrderBy(g => g.Key);
            foreach (var group in groupedTriggers)
            {
                EditorGUILayout.LabelField($"▼ {group.Key} ({group.Count()})", EditorStyles.boldLabel);
                EditorGUI.indentLevel++;
                foreach (var trigger in group)
                {
                    if (!buffTriggerSelections.ContainsKey(trigger.typeName))
                        buffTriggerSelections[trigger.typeName] = true;

                    EditorGUILayout.BeginHorizontal();
                    buffTriggerSelections[trigger.typeName] = EditorGUILayout.ToggleLeft(
                        $"{trigger.displayName} ({trigger.typeName})",
                        buffTriggerSelections[trigger.typeName]);
                    EditorGUILayout.EndHorizontal();
                }
                EditorGUI.indentLevel--;
                EditorGUILayout.Space(3);
            }
        }

        private void DrawLogTab()
        {
            EditorGUILayout.BeginHorizontal();
            EditorGUILayout.LabelField("导出日志", EditorStyles.boldLabel);
            GUILayout.FlexibleSpace();
            if (GUILayout.Button("清空", GUILayout.Width(50)))
            {
                logText = "";
            }
            EditorGUILayout.EndHorizontal();

            EditorGUILayout.Space(5);

            EditorGUILayout.TextArea(logText, GUILayout.ExpandHeight(true));
        }

        #endregion

        #region 数据刷新

        private void RefreshAllData()
        {
            Log("[刷新] 开始扫描所有数据...");

            // 扫描 Actions
            try
            {
                cachedActions = ActionScanner.ScanActions();
                foreach (var action in cachedActions)
                    if (!actionSelections.ContainsKey(action.typeName))
                        actionSelections[action.typeName] = true;
                Log($"[Action] 扫描到 {cachedActions.Count} 个 Action 类型");
            }
            catch (Exception e)
            {
                Log($"[Action Error] {e.Message}");
                cachedActions = new List<ActionEntry>();
            }

            // 扫描 Buff 效果
            try
            {
                cachedBuffEffects = BuffScanner.ScanBuffEffects();
                foreach (var effect in cachedBuffEffects)
                    if (!buffEffectSelections.ContainsKey(effect.typeName))
                        buffEffectSelections[effect.typeName] = true;
                Log($"[Buff Effect] 扫描到 {cachedBuffEffects.Count} 个效果类型");
            }
            catch (Exception e)
            {
                Log($"[Buff Effect Error] {e.Message}");
                cachedBuffEffects = new List<BuffEffectEntry>();
            }

            // 扫描 Buff 触发器
            try
            {
                cachedBuffTriggers = BuffScanner.ScanBuffTriggers();
                foreach (var trigger in cachedBuffTriggers)
                    if (!buffTriggerSelections.ContainsKey(trigger.typeName))
                        buffTriggerSelections[trigger.typeName] = true;
                Log($"[Buff Trigger] 扫描到 {cachedBuffTriggers.Count} 个触发器类型");
            }
            catch (Exception e)
            {
                Log($"[Buff Trigger Error] {e.Message}");
                cachedBuffTriggers = new List<BuffTriggerEntry>();
            }

            Log("[刷新] 扫描完成");
            Repaint();
        }

        #endregion

        #region 导出方法

        private void ExportAll()
        {
            Log("\n========== 开始导出全部数据 ==========");
            ExportSelectedActions();
            ExportSelectedBuffEffects();
            ExportSelectedBuffTriggers();
            ExportBuffEnums();
            Log("========== 全部导出完成 ==========\n");

            AssetDatabase.Refresh();
            EditorUtility.DisplayDialog("导出完成", "所有 RAG 数据已导出", "确定");
        }

        private void ExportSelectedActions()
        {
            var config = RAGConfig.Instance;
            if (config == null)
            {
                Log("[Error] 无法加载 RAGConfig");
                return;
            }

            var selectedActions = cachedActions?
                .Where(a => actionSelections.TryGetValue(a.typeName, out bool selected) && selected)
                .ToList() ?? new List<ActionEntry>();

            if (selectedActions.Count == 0)
            {
                Log("[Action] 没有选中任何 Action");
                return;
            }

            string exportDir = Path.Combine(Application.dataPath, config.exportDirectory);
            var exporter = new ActionJSONExporter(exportDir, Log);
            var (success, fail) = exporter.ExportActionsToJSON(selectedActions);
            Log($"[Action] 导出完成 - 成功: {success}, 失败: {fail}");
        }

        private void ExportSelectedBuffEffects()
        {
            var config = RAGConfig.Instance;
            if (config == null) return;

            var selectedEffects = cachedBuffEffects?
                .Where(e => buffEffectSelections.TryGetValue(e.typeName, out bool selected) && selected)
                .ToList() ?? new List<BuffEffectEntry>();

            if (selectedEffects.Count == 0)
            {
                Log("[Buff Effect] 没有选中任何效果");
                return;
            }

            string directory = Path.Combine(Application.dataPath, config.buffSystemConfig.exportDirectory, "Effects");
            Directory.CreateDirectory(directory);

            int exportedCount = 0;
            foreach (var effect in selectedEffects)
            {
                try
                {
                    var wrapper = new BuffEffectFileWrapper
                    {
                        version = "1.0",
                        exportTime = DateTime.Now.ToString("O"),
                        dataType = "BuffEffect",
                        effect = effect
                    };

                    string json = JsonUtility.ToJson(wrapper, true);
                    File.WriteAllText(Path.Combine(directory, $"{effect.typeName}.json"), json);
                    exportedCount++;
                }
                catch (Exception e)
                {
                    Log($"[Buff Effect Error] {effect.typeName}: {e.Message}");
                }
            }

            Log($"[Buff Effect] 导出完成 - 成功: {exportedCount}/{selectedEffects.Count}");
        }

        private void ExportSelectedBuffTriggers()
        {
            var config = RAGConfig.Instance;
            if (config == null) return;

            var selectedTriggers = cachedBuffTriggers?
                .Where(t => buffTriggerSelections.TryGetValue(t.typeName, out bool selected) && selected)
                .ToList() ?? new List<BuffTriggerEntry>();

            if (selectedTriggers.Count == 0)
            {
                Log("[Buff Trigger] 没有选中任何触发器");
                return;
            }

            string directory = Path.Combine(Application.dataPath, config.buffSystemConfig.exportDirectory, "Triggers");
            Directory.CreateDirectory(directory);

            int exportedCount = 0;
            foreach (var trigger in selectedTriggers)
            {
                try
                {
                    var wrapper = new BuffTriggerFileWrapper
                    {
                        version = "1.0",
                        exportTime = DateTime.Now.ToString("O"),
                        dataType = "BuffTrigger",
                        trigger = trigger
                    };

                    string json = JsonUtility.ToJson(wrapper, true);
                    File.WriteAllText(Path.Combine(directory, $"{trigger.typeName}.json"), json);
                    exportedCount++;
                }
                catch (Exception e)
                {
                    Log($"[Buff Trigger Error] {trigger.typeName}: {e.Message}");
                }
            }

            Log($"[Buff Trigger] 导出完成 - 成功: {exportedCount}/{selectedTriggers.Count}");
        }

        private void ExportBuffEnums()
        {
            try
            {
                BuffJSONExporter.ExportBuffEnums();
                Log("[Buff Enum] 枚举导出完成");
            }
            catch (Exception e)
            {
                Log($"[Buff Enum Error] {e.Message}");
            }
        }

        #endregion

        #region 工具方法

        private void Log(string message)
        {
            logText += $"[{DateTime.Now:HH:mm:ss}] {message}\n";
            Debug.Log($"[RAGExport] {message}");
        }

        #endregion
    }
}
