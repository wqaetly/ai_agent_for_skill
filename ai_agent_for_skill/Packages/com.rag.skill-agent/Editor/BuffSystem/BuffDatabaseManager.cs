using System;
using System.Collections.Generic;
using System.IO;
using UnityEditor;
using UnityEngine;

namespace RAG.BuffSystem
{
    /// <summary>
    /// Manages BuffDescriptionDatabase operations including load, create and save
    /// </summary>
    public class BuffDatabaseManager
    {
        private BuffDescriptionDatabase database;
        private string databasePath;
        private Action<string> logAction;

        public BuffDescriptionDatabase Database => database;

        public BuffDatabaseManager(string databasePath, Action<string> logAction = null)
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
            database = AssetDatabase.LoadAssetAtPath<BuffDescriptionDatabase>(databasePath);
            if (database != null)
            {
                Log($"[Database] Loaded successfully: {database.totalEffects} Effects, {database.totalTriggers} Triggers");
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

                database = ScriptableObject.CreateInstance<BuffDescriptionDatabase>();
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
        /// Save all effect entries to database
        /// </summary>
        /// <param name="effectEntries">List of effect entries to save</param>
        /// <returns>Number of entries saved</returns>
        public int SaveEffectsToDatabase(List<BuffEffectEntry> effectEntries)
        {
            if (database == null)
            {
                CreateDatabase();
            }

            int savedCount = 0;
            foreach (var entry in effectEntries)
            {
                var data = new BuffEffectDescriptionData
                {
                    typeName = entry.typeName,
                    fullTypeName = entry.fullTypeName,
                    namespaceName = entry.namespaceName,
                    assemblyName = entry.assemblyName,
                    displayName = entry.displayName,
                    description = entry.description,
                    category = entry.category,
                    lastModifiedTime = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss")
                };

                // Save parameter info
                if (entry.parameters != null)
                {
                    data.parameters = new List<BuffParameterInfo>(entry.parameters);
                }

                database.AddOrUpdateEffect(data);
                savedCount++;
            }

            EditorUtility.SetDirty(database);
            AssetDatabase.SaveAssets();
            Log($"[Save] Saved {savedCount} Effect descriptions to database");
            return savedCount;
        }

        /// <summary>
        /// Save all trigger entries to database
        /// </summary>
        /// <param name="triggerEntries">List of trigger entries to save</param>
        /// <returns>Number of entries saved</returns>
        public int SaveTriggersToDatabase(List<BuffTriggerEntry> triggerEntries)
        {
            if (database == null)
            {
                CreateDatabase();
            }

            int savedCount = 0;
            foreach (var entry in triggerEntries)
            {
                var data = new BuffTriggerDescriptionData
                {
                    typeName = entry.typeName,
                    fullTypeName = entry.fullTypeName,
                    namespaceName = entry.namespaceName,
                    assemblyName = entry.assemblyName,
                    displayName = entry.displayName,
                    description = entry.description,
                    category = entry.category,
                    lastModifiedTime = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss")
                };

                // Save parameter info
                if (entry.parameters != null)
                {
                    data.parameters = new List<BuffParameterInfo>(entry.parameters);
                }

                database.AddOrUpdateTrigger(data);
                savedCount++;
            }

            EditorUtility.SetDirty(database);
            AssetDatabase.SaveAssets();
            Log($"[Save] Saved {savedCount} Trigger descriptions to database");
            return savedCount;
        }

        private void Log(string message)
        {
            logAction?.Invoke(message);
        }
    }
}

