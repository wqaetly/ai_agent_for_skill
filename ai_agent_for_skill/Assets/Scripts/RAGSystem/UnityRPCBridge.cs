using System;
using System.Collections.Generic;
using Cysharp.Threading.Tasks;
using Newtonsoft.Json.Linq;
using UnityEngine;

namespace RAGSystem
{
    /// <summary>
    /// Unity RPC桥接�?    /// 将Unity技能系统的功能暴露给RPC服务�?    /// </summary>
    public class UnityRPCBridge : MonoBehaviour
    {
        [Header("依赖")]
        [SerializeField] private UnityRPCClient rpcClient;

        // 委托定义
        public delegate UniTask<JObject> RPCHandler(JObject @params);

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
            // 技能管理方�?            RegisterMethod("CreateSkill", HandleCreateSkill);
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
        public async UniTask<JObject> HandleRPCCall(string method, JObject @params)
        {
            if (!rpcMethods.TryGetValue(method, out var handler))
            {
                throw new Exception($"Method '{method}' not found");
            }

            return await handler(@params);
        }

        // ==================== RPC方法实现 ====================

        /// <summary>
        /// 创建技�?        /// </summary>
        private async UniTask<JObject> HandleCreateSkill(JObject @params)
        {
            try
            {
                string skillName = @params["skillName"]?.ToString();
                JObject config = @params["config"] as JObject;

                Debug.Log($"[RPCBridge] Creating skill: {skillName}");

                // TODO: 调用实际的技能创建逻辑
                // 例如：SkillEditorWindow.CreateSkillFromJSON(skillName, config.ToString());

                // 临时返回成功响应
                return new JObject
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
                return new JObject
                {
                    ["success"] = false,
                    ["error"] = e.Message
                };
            }
        }

        /// <summary>
        /// 更新技�?        /// </summary>
        private async UniTask<JObject> HandleUpdateSkill(JObject @params)
        {
            try
            {
                string skillId = @params["skillId"]?.ToString();
                JObject config = @params["config"] as JObject;

                Debug.Log($"[RPCBridge] Updating skill: {skillId}");

                // TODO: 实现技能更新逻辑

                return new JObject
                {
                    ["success"] = true,
                    ["skill_id"] = skillId,
                    ["message"] = "Skill updated successfully (stub)"
                };
            }
            catch (Exception e)
            {
                Debug.LogError($"[RPCBridge] UpdateSkill error: {e.Message}");
                return new JObject
                {
                    ["success"] = false,
                    ["error"] = e.Message
                };
            }
        }

        /// <summary>
        /// 删除技�?        /// </summary>
        private async UniTask<JObject> HandleDeleteSkill(JObject @params)
        {
            try
            {
                string skillId = @params["skillId"]?.ToString();

                Debug.Log($"[RPCBridge] Deleting skill: {skillId}");

                // TODO: 实现技能删除逻辑

                return new JObject
                {
                    ["success"] = true,
                    ["skill_id"] = skillId,
                    ["message"] = "Skill deleted successfully (stub)"
                };
            }
            catch (Exception e)
            {
                Debug.LogError($"[RPCBridge] DeleteSkill error: {e.Message}");
                return new JObject
                {
                    ["success"] = false,
                    ["error"] = e.Message
                };
            }
        }

        /// <summary>
        /// 获取技能列�?        /// </summary>
        private async UniTask<JObject> HandleGetSkillList(JObject @params)
        {
            try
            {
                Debug.Log("[RPCBridge] Getting skill list");

                // TODO: 实现获取技能列表逻辑
                var skills = new JArray
                {
                    new JObject
                    {
                        ["skill_id"] = "skill_001",
                        ["skill_name"] = "FireBall",
                        ["file_path"] = "Assets/Skills/FireBall.json"
                    },
                    new JObject
                    {
                        ["skill_id"] = "skill_002",
                        ["skill_name"] = "IceBlast",
                        ["file_path"] = "Assets/Skills/IceBlast.json"
                    }
                };

                return new JObject
                {
                    ["success"] = true,
                    ["skills"] = skills,
                    ["count"] = skills.Count
                };
            }
            catch (Exception e)
            {
                Debug.LogError($"[RPCBridge] GetSkillList error: {e.Message}");
                return new JObject
                {
                    ["success"] = false,
                    ["error"] = e.Message
                };
            }
        }

        /// <summary>
        /// 验证技能配�?        /// </summary>
        private async UniTask<JObject> HandleValidateConfig(JObject @params)
        {
            try
            {
                JObject config = @params["config"] as JObject;

                Debug.Log("[RPCBridge] Validating config");

                // TODO: 实现配置验证逻辑
                bool isValid = true;
                var errors = new JArray();

                return new JObject
                {
                    ["valid"] = isValid,
                    ["errors"] = errors
                };
            }
            catch (Exception e)
            {
                Debug.LogError($"[RPCBridge] ValidateConfig error: {e.Message}");
                return new JObject
                {
                    ["valid"] = false,
                    ["errors"] = new JArray { e.Message }
                };
            }
        }

        /// <summary>
        /// 应用参数推荐
        /// </summary>
        private async UniTask<JObject> HandleApplyParameters(JObject @params)
        {
            try
            {
                string actionType = @params["actionType"]?.ToString();
                JObject parameters = @params["parameters"] as JObject;

                Debug.Log($"[RPCBridge] Applying parameters to {actionType}");

                // TODO: 实现参数应用逻辑

                return new JObject
                {
                    ["success"] = true,
                    ["action_type"] = actionType,
                    ["applied_parameters"] = parameters
                };
            }
            catch (Exception e)
            {
                Debug.LogError($"[RPCBridge] ApplyParameters error: {e.Message}");
                return new JObject
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
        public void OnWebNotification(string eventType, JObject data)
        {
            Debug.Log($"[RPCBridge] Web notification: {eventType}");

            // 可以在这里处理Web UI的通知
            // 例如：索引更新完成、技能生成完成等
        }
    }
}
