using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using Cysharp.Threading.Tasks;
using SkillSystem.Actions;
using UnityEditor;
using UnityEngine;

namespace RAG
{
    /// <summary>
    /// Handles AI-powered description generation for Actions using DeepSeek
    /// </summary>
    public class AIDescriptionGenerator
    {
        private DeepSeekClient deepSeekClient;
        private RAGConfig config;
        private Action<string> logAction;
        private Action<float> progressAction;

        public bool IsGenerating { get; private set; }
        public float Progress { get; private set; }

        public AIDescriptionGenerator(RAGConfig config, Action<string> logAction = null, Action<float> progressAction = null)
        {
            this.config = config;
            this.logAction = logAction;
            this.progressAction = progressAction;
        }

        /// <summary>
        /// Get or create DeepSeek client
        /// </summary>
        private DeepSeekClient GetDeepSeekClient()
        {
            if (deepSeekClient == null && !string.IsNullOrEmpty(RAGConfig.DeepSeekApiKey))
            {
                deepSeekClient = new DeepSeekClient(RAGConfig.DeepSeekApiKey);
            }
            return deepSeekClient;
        }

        /// <summary>
        /// Reset the client (e.g., when API key changes)
        /// </summary>
        public void ResetClient()
        {
            deepSeekClient = null;
        }

        /// <summary>
        /// Generate descriptions for selected entries
        /// </summary>
        public async UniTask<(int successCount, int failCount)> GenerateDescriptionsForSelectedAsync(List<ActionEntry> actionEntries)
        {
            var selectedEntries = actionEntries.Where(e => e.isSelected).ToList();
            if (selectedEntries.Count == 0)
            {
                EditorUtility.DisplayDialog("No Selection", "Please select Actions to generate descriptions for", "OK");
                return (0, 0);
            }

            return await GenerateDescriptionsAsync(selectedEntries);
        }

        /// <summary>
        /// Generate descriptions for entries missing descriptions
        /// </summary>
        public async UniTask<(int successCount, int failCount)> GenerateDescriptionsForMissingAsync(List<ActionEntry> actionEntries)
        {
            var missingEntries = actionEntries.Where(e => string.IsNullOrEmpty(e.description)).ToList();
            if (missingEntries.Count == 0)
            {
                EditorUtility.DisplayDialog("No Generation Needed", "All Actions already have descriptions", "OK");
                return (0, 0);
            }

            if (!EditorUtility.DisplayDialog(
                "Batch Generation Confirmation",
                $"Will generate descriptions for {missingEntries.Count} Actions without descriptions\n\nEstimated time: {missingEntries.Count * 3} seconds\n\nContinue?",
                "Continue",
                "Cancel"))
            {
                return (0, 0);
            }

            return await GenerateDescriptionsAsync(missingEntries);
        }

        /// <summary>
        /// Generate descriptions for a list of entries
        /// </summary>
        public async UniTask<(int successCount, int failCount)> GenerateDescriptionsAsync(List<ActionEntry> entries)
        {
            if (string.IsNullOrEmpty(RAGConfig.DeepSeekApiKey))
            {
                EditorUtility.DisplayDialog("API Key Missing", "Please configure DeepSeek API Key first", "OK");
                return (0, 0);
            }

            var client = GetDeepSeekClient();
            if (client == null)
            {
                EditorUtility.DisplayDialog("Client Initialization Failed", "Unable to create DeepSeek client", "OK");
                return (0, 0);
            }

            IsGenerating = true;
            Progress = 0;
            int successCount = 0;
            int failCount = 0;

            Log($"\n[AI Generation] Starting description generation for {entries.Count} Actions...");

            for (int i = 0; i < entries.Count; i++)
            {
                var entry = entries[i];
                Progress = (float)(i + 1) / entries.Count * 100f;
                UpdateProgress(Progress);

                EditorUtility.DisplayProgressBar(
                    "AI Generate Description",
                    $"Processing: {entry.typeName} ({i + 1}/{entries.Count})",
                    Progress / 100f);

                try
                {
                    string sourceCode = GetActionSourceCode(entry.typeName);
                    if (string.IsNullOrEmpty(sourceCode))
                    {
                        Log($"  ⚠️ {entry.typeName}: Unable to get source code, skipped");
                        failCount++;
                        continue;
                    }

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
                        entry.parameterDescriptions = result.GetAllParameterDescriptions();
                        int paramCount = entry.parameterDescriptions.Count;

                        Log($"  ✅ {entry.typeName}: Generated successfully with {paramCount} parameter descriptions");
                        successCount++;
                    }
                    else
                    {
                        Log($"  ❌ {entry.typeName}: {result.error}");
                        failCount++;
                    }

                    await UniTask.Delay(config.aiRequestInterval);
                }
                catch (Exception e)
                {
                    Log($"  ❌ {entry.typeName}: Exception - {e.Message}");
                    failCount++;
                }
            }

            EditorUtility.ClearProgressBar();
            IsGenerating = false;
            Progress = 100;
            UpdateProgress(100);

            Log($"[AI Generation] Complete - Success: {successCount}, Failed: {failCount}");

            return (successCount, failCount);
        }

        /// <summary>
        /// Get the source code for an Action type
        /// </summary>
        public string GetActionSourceCode(string typeName)
        {
            try
            {
                var actionType = Assembly.GetAssembly(typeof(ISkillAction))
                    .GetTypes()
                    .FirstOrDefault(t => t.Name == typeName);

                if (actionType == null)
                {
                    return null;
                }

                var guids = AssetDatabase.FindAssets($"t:MonoScript {typeName}");
                foreach (var guid in guids)
                {
                    string path = AssetDatabase.GUIDToAssetPath(guid);
                    var script = AssetDatabase.LoadAssetAtPath<MonoScript>(path);
                    if (script != null && script.GetClass() == actionType)
                    {
                        string fullPath = Path.GetFullPath(path);
                        if (File.Exists(fullPath))
                        {
                            return File.ReadAllText(fullPath);
                        }
                    }
                }

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
                Debug.LogError($"Failed to get Action source code: {typeName} - {e.Message}");
                return null;
            }
        }

        private void Log(string message)
        {
            logAction?.Invoke(message);
        }

        private void UpdateProgress(float progress)
        {
            progressAction?.Invoke(progress);
        }
    }
}
