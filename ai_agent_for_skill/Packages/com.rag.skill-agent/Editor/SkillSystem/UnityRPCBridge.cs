using System;
using System.Collections.Generic;
using Cysharp.Threading.Tasks;
using UnityEngine;

namespace RAGSystem
{
    /// <summary>
    /// Unity RPC桥接层
    /// 将Unity技能系统的功能暴露给RPC服务器
    /// </summary>
    public class UnityRPCBridge : MonoBehaviour
    {
        [Header("依赖")]
        [SerializeField] private UnityRPCClient rpcClient;

        // 委托定义
        public delegate UniTask<Dictionary<string, object>> RPCHandler(Dictionary<string, object> @params);

        // 注册的RPC方法
        private Dictionary<string, RPCHandler> rpcMethods = new Dictionary<string, RPCHandler>();

        // ==================== Unity生命周期 ====================

        private void Awake()
        {
            if (rpcClient == null)
            {
                rpcClient = GetComponent<UnityRPCClient>();
            }

            // 注册RPC方法
            RegisterRPCMethods();
        }

        /// <summary>
        /// 注册所有可被远程调用的方法
        /// </summary>
        private void RegisterRPCMethods()
        {
            // 技能管理方法
            RegisterMethod("CreateSkill", HandleCreateSkill);
            RegisterMethod("UpdateSkill", HandleUpdateSkill);
            RegisterMethod("DeleteSkill", HandleDeleteSkill);
            RegisterMethod("GetSkillList", HandleGetSkillList);
            RegisterMethod("ValidateConfig", HandleValidateConfig);
            RegisterMethod("ApplyParameters", HandleApplyParameters);

            Debug.Log($"[RPCBridge] Registered {rpcMethods.Count} RPC methods");
        }

        /// <summary>
        /// 注册RPC方法
        /// </summary>
        private void RegisterMethod(string methodName, RPCHandler handler)
        {
            rpcMethods[methodName] = handler;
            Debug.Log($"[RPCBridge] Registered method: {methodName}");
        }

        /// <summary>
        /// 处理来自服务器的RPC调用
        /// </summary>
        public async UniTask<Dictionary<string, object>> HandleRPCCall(string method, Dictionary<string, object> @params)
        {
            if (!rpcMethods.TryGetValue(method, out var handler))
            {
                throw new Exception($"Method '{method}' not found");
            }

            return await handler(@params);
        }

        // ==================== RPC方法实现 ====================

        /// <summary>
        /// 创建技能
        /// </summary>
        private async UniTask<Dictionary<string, object>> HandleCreateSkill(Dictionary<string, object> @params)
        {
            try
            {
                string skillName = @params.ContainsKey("skillName") ? @params["skillName"]?.ToString() : null;
                var config = @params.ContainsKey("config") ? @params["config"] as Dictionary<string, object> : null;

                Debug.Log($"[RPCBridge] Creating skill: {skillName}");

                // TODO: 调用实际的技能创建逻辑
                // 例如：SkillEditorWindow.CreateSkillFromJSON(skillName, config.ToString());

                // 临时返回成功响应
                return new Dictionary<string, object>
                {
                    ["success"] = true,
                    ["skill_id"] = Guid.NewGuid().ToString(),
                    ["skill_name"] = skillName,
                    ["message"] = "Skill created successfully (stub)"
                };
            }
            catch (Exception e)
            {
                Debug.LogError($"[RPCBridge] CreateSkill error: {e.Message}");
                return new Dictionary<string, object>
                {
                    ["success"] = false,
                    ["error"] = e.Message
                };
            }
        }

        /// <summary>
        /// 更新技能
        /// </summary>
        private async UniTask<Dictionary<string, object>> HandleUpdateSkill(Dictionary<string, object> @params)
        {
            try
            {
                string skillId = @params.ContainsKey("skillId") ? @params["skillId"]?.ToString() : null;
                var config = @params.ContainsKey("config") ? @params["config"] as Dictionary<string, object> : null;

                Debug.Log($"[RPCBridge] Updating skill: {skillId}");

                // TODO: 实现技能更新逻辑

                return new Dictionary<string, object>
                {
                    ["success"] = true,
                    ["skill_id"] = skillId,
                    ["message"] = "Skill updated successfully (stub)"
                };
            }
            catch (Exception e)
            {
                Debug.LogError($"[RPCBridge] UpdateSkill error: {e.Message}");
                return new Dictionary<string, object>
                {
                    ["success"] = false,
                    ["error"] = e.Message
                };
            }
        }

        /// <summary>
        /// 删除技能
        /// </summary>
        private async UniTask<Dictionary<string, object>> HandleDeleteSkill(Dictionary<string, object> @params)
        {
            try
            {
                string skillId = @params.ContainsKey("skillId") ? @params["skillId"]?.ToString() : null;

                Debug.Log($"[RPCBridge] Deleting skill: {skillId}");

                // TODO: 实现技能删除逻辑

                return new Dictionary<string, object>
                {
                    ["success"] = true,
                    ["skill_id"] = skillId,
                    ["message"] = "Skill deleted successfully (stub)"
                };
            }
            catch (Exception e)
            {
                Debug.LogError($"[RPCBridge] DeleteSkill error: {e.Message}");
                return new Dictionary<string, object>
                {
                    ["success"] = false,
                    ["error"] = e.Message
                };
            }
        }

        /// <summary>
        /// 获取技能列表
        /// </summary>
        private async UniTask<Dictionary<string, object>> HandleGetSkillList(Dictionary<string, object> @params)
        {
            try
            {
                Debug.Log("[RPCBridge] Getting skill list");

                // TODO: 实现获取技能列表逻辑
                var skills = new List<object>
                {
                    new Dictionary<string, object>
                    {
                        ["skill_id"] = "skill_001",
                        ["skill_name"] = "FireBall",
                        ["file_path"] = "Assets/Skills/FireBall.json"
                    },
                    new Dictionary<string, object>
                    {
                        ["skill_id"] = "skill_002",
                        ["skill_name"] = "IceBlast",
                        ["file_path"] = "Assets/Skills/IceBlast.json"
                    }
                };

                return new Dictionary<string, object>
                {
                    ["success"] = true,
                    ["skills"] = skills,
                    ["count"] = skills.Count
                };
            }
            catch (Exception e)
            {
                Debug.LogError($"[RPCBridge] GetSkillList error: {e.Message}");
                return new Dictionary<string, object>
                {
                    ["success"] = false,
                    ["error"] = e.Message
                };
            }
        }

        /// <summary>
        /// 验证技能配置
        /// </summary>
        private async UniTask<Dictionary<string, object>> HandleValidateConfig(Dictionary<string, object> @params)
        {
            try
            {
                var config = @params.ContainsKey("config") ? @params["config"] as Dictionary<string, object> : null;

                Debug.Log("[RPCBridge] Validating config");

                // TODO: 实现配置验证逻辑
                bool isValid = true;
                var errors = new List<object>();

                return new Dictionary<string, object>
                {
                    ["valid"] = isValid,
                    ["errors"] = errors
                };
            }
            catch (Exception e)
            {
                Debug.LogError($"[RPCBridge] ValidateConfig error: {e.Message}");
                return new Dictionary<string, object>
                {
                    ["valid"] = false,
                    ["errors"] = new List<object> { e.Message }
                };
            }
        }

        /// <summary>
        /// 应用参数推荐
        /// </summary>
        private async UniTask<Dictionary<string, object>> HandleApplyParameters(Dictionary<string, object> @params)
        {
            try
            {
                string actionType = @params.ContainsKey("actionType") ? @params["actionType"]?.ToString() : null;
                var parameters = @params.ContainsKey("parameters") ? @params["parameters"] as Dictionary<string, object> : null;

                Debug.Log($"[RPCBridge] Applying parameters to {actionType}");

                // TODO: 实现参数应用逻辑

                return new Dictionary<string, object>
                {
                    ["success"] = true,
                    ["action_type"] = actionType,
                    ["applied_parameters"] = parameters
                };
            }
            catch (Exception e)
            {
                Debug.LogError($"[RPCBridge] ApplyParameters error: {e.Message}");
                return new Dictionary<string, object>
                {
                    ["success"] = false,
                    ["error"] = e.Message
                };
            }
        }

        // ==================== 便捷API ====================

        /// <summary>
        /// 从Web UI接收到的通知
        /// </summary>
        public void OnWebNotification(string eventType, Dictionary<string, object> data)
        {
            Debug.Log($"[RPCBridge] Web notification: {eventType}");

            // 可以在这里处理Web UI的通知
            // 例如：索引更新完成、技能生成完成等
        }
    }
}
