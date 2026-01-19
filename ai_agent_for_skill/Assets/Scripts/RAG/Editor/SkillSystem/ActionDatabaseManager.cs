using System;
using System.Collections.Generic;
using System.IO;
using UnityEditor;
using UnityEngine;

namespace RAG
{
    /// <summary>
    /// Manages ActionDescriptionDatabase operations including load, create and save
    /// </summary>
    public class ActionDatabaseManager
    {
        private ActionDescriptionDatabase database;
        private string databasePath;
        private Action<string> logAction;

        public ActionDescriptionDatabase Database => database;

        public ActionDatabaseManager(string databasePath, Action<string> logAction = null)
        {
            this.databasePath = databasePath;
            this.logAction = logAction;
        }

        /// <summary>
        /// Load the database from asset path
        /// </summary>
        /// <returns>True if database was loaded or created successfully</returns>
        public bool LoadDatabase()
        {
            database = AssetDatabase.LoadAssetAtPath<ActionDescriptionDatabase>(databasePath);
            if (database != null)
            {
                Log($"[Database] Loaded successfully: {database.totalActions} Actions");
                return true;
            }
            else
            {
                Log("[Database] Not found, creating new...");
                return CreateDatabase();
            }
        }

        /// <summary>
        /// Create a new database at the configured path
        /// </summary>
        /// <returns>True if database was created successfully</returns>
        public bool CreateDatabase()
        {
            try
            {
                string directory = Path.GetDirectoryName(databasePath);
                if (!string.IsNullOrEmpty(directory) && !Directory.Exists(directory))
                {
                    Directory.CreateDirectory(directory);
                }

                database = ScriptableObject.CreateInstance<ActionDescriptionDatabase>();
                AssetDatabase.CreateAsset(database, databasePath);
                AssetDatabase.SaveAssets();
                Log("[Database] Created successfully");
                return true;
            }
            catch (Exception e)
            {
                Log($"[Database] Creation failed: {e.Message}");
                return false;
            }
        }

        /// <summary>
        /// Save all action entries to database
        /// </summary>
        /// <param name="actionEntries">List of action entries to save</param>
        /// <returns>Number of entries saved</returns>
        public int SaveAllToDatabase(List<ActionEntry> actionEntries)
        {
            if (database == null)
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
                    
                    // Save parameter descriptions
                    if (entry.parameterDescriptions != null && entry.parameterDescriptions.Count > 0)
                    {
                        data.parameterDescriptions = new SerializableDictionary<string, string>();
                        foreach (var kvp in entry.parameterDescriptions)
                        {
                            data.parameterDescriptions[kvp.Key] = kvp.Value;
                        }
                    }
                    
                    database.AddOrUpdateAction(data);
                    savedCount++;
                }
            }

            EditorUtility.SetDirty(database);
            AssetDatabase.SaveAssets();
            Log($"[Save] Saved {savedCount} Action descriptions to database");
            return savedCount;
        }

        private void Log(string message)
        {
            logAction?.Invoke(message);
        }
    }
}
