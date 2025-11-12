using System;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;
using SkillSystem.Actions;
using Sirenix.OdinInspector.Editor;

namespace SkillSystem.Editor
{
    /// <summary>
    /// Action选择器UI - 使用GenericSelector提供可扩展的Action选择界面
    /// 职责：展示所有可用Action类型，支持分类显示和搜索
    /// </summary>
    public static class ActionSelectorUI
    {
        /// <summary>
        /// 显示Action选择弹窗
        /// </summary>
        /// <param name="onActionSelected">选择Action后的回调</param>
        /// <param name="targetFrame">目标帧数（用于显示）</param>
        public static void ShowActionSelector(Action<Type> onActionSelected, int targetFrame = 0)
        {
            // 获取所有Action类型并按类别分组
            var actionsByCategory = ActionSelector.GetActionTypesByCategory();

            // 构建GenericSelector的数�?
            var selectorItems = new List<GenericSelectorItem<Type>>();

            foreach (var category in actionsByCategory)
            {
                string categoryName = category.Key;
                var actionsInCategory = category.Value;

                foreach (var actionType in actionsInCategory)
                {
                    string displayName = GetActionDisplayName(actionType);
                    string path = $"{categoryName}/{displayName}";

                    selectorItems.Add(new GenericSelectorItem<Type>(path, actionType));
                }
            }

            // 创建GenericSelector
            string title = targetFrame > 0 ?
                $"Select Action (Frame {targetFrame})" :
                "Select Action";

            var selector = new GenericSelector<Type>(title, false, selectorItems);

            // 启用单击选择
            selector.EnableSingleClickToSelect();

            // 设置选择回调
            selector.SelectionChanged += selectedTypes =>
            {
                var selectedType = selectedTypes.FirstOrDefault();
                if (selectedType != null)
                {
                    onActionSelected?.Invoke(selectedType);
                }
            };

            // 显示弹窗
            selector.ShowInPopup();
        }

        /// <summary>
        /// 显示简化的Action选择弹窗（不分类�?
        /// </summary>
        /// <param name="onActionSelected">选择Action后的回调</param>
        /// <param name="targetFrame">目标帧数（用于显示）</param>
        public static void ShowFlatActionSelector(Action<Type> onActionSelected, int targetFrame = 0)
        {
            // 获取所有Action类型
            var allActionTypes = ActionSelector.GetAllActionTypes();

            // 构建GenericSelector的数�?
            var selectorItems = allActionTypes.Select(kvp =>
                new GenericSelectorItem<Type>(kvp.Key, kvp.Value));

            // 创建GenericSelector
            string title = targetFrame > 0 ?
                $"Select Action (Frame {targetFrame})" :
                "Select Action";

            var selector = new GenericSelector<Type>(title, false, selectorItems);

            // 启用单击选择
            selector.EnableSingleClickToSelect();

            // 设置选择回调
            selector.SelectionChanged += selectedTypes =>
            {
                var selectedType = selectedTypes.FirstOrDefault();
                if (selectedType != null)
                {
                    onActionSelected?.Invoke(selectedType);
                }
            };

            // 显示弹窗
            selector.ShowInPopup();
        }

        /// <summary>
        /// 显示常用Action的快速选择菜单
        /// </summary>
        /// <param name="onActionSelected">选择Action后的回调</param>
        /// <param name="targetFrame">目标帧数（用于显示）</param>
        public static void ShowCommonActionsMenu(Action<Type> onActionSelected, int targetFrame = 0)
        {
            // 定义常用Action类型
            var commonActionNames = new[]
            {
                "Log", "Animation", "Audio", "Camera",
                "Damage", "Heal", "Buff", "Movement",
                "Projectile", "Collision"
            };

            var allActionTypes = ActionSelector.GetAllActionTypes();
            var commonActions = new List<GenericSelectorItem<Type>>();

            foreach (var actionName in commonActionNames)
            {
                var matchingAction = allActionTypes.FirstOrDefault(kvp =>
                    kvp.Key.Contains(actionName, StringComparison.OrdinalIgnoreCase));

                if (matchingAction.Value != null)
                {
                    commonActions.Add(new GenericSelectorItem<Type>(
                        $"Common/{matchingAction.Key}", matchingAction.Value));
                }
            }

            // 添加"More..."选项
            commonActions.Add(new GenericSelectorItem<Type>("More Actions...", null));

            // 创建GenericSelector
            string title = targetFrame > 0 ?
                $"Add Action (Frame {targetFrame})" :
                "Add Action";

            var selector = new GenericSelector<Type>(title, false, commonActions);
            selector.EnableSingleClickToSelect();

            // 设置选择回调
            selector.SelectionChanged += selectedTypes =>
            {
                var selectedType = selectedTypes.FirstOrDefault();

                if (selectedType == null)
                {
                    // 选择�?More Actions..."，显示完整列�?
                    ShowActionSelector(onActionSelected, targetFrame);
                }
                else
                {
                    onActionSelected?.Invoke(selectedType);
                }
            };

            // 显示弹窗
            selector.ShowInPopup();
        }

        /// <summary>
        /// 获取Action的显示名�?
        /// </summary>
        private static string GetActionDisplayName(Type actionType)
        {
            // 移除"Action"后缀，使名称更清�?
            string name = actionType.Name;
            if (name.EndsWith("Action"))
            {
                name = name.Substring(0, name.Length - 6);
            }

            // 添加空格分隔驼峰命名
            return AddSpacesToPascalCase(name);
        }

        /// <summary>
        /// 为驼峰命名添加空�?
        /// </summary>
        private static string AddSpacesToPascalCase(string text)
        {
            if (string.IsNullOrEmpty(text))
                return text;

            var result = new System.Text.StringBuilder();
            result.Append(text[0]);

            for (int i = 1; i < text.Length; i++)
            {
                if (char.IsUpper(text[i]) && char.IsLower(text[i - 1]))
                {
                    result.Append(' ');
                }
                result.Append(text[i]);
            }

            return result.ToString();
        }
    }

    /// <summary>
    /// Action选择器的扩展方法
    /// </summary>
    public static class ActionSelectorExtensions
    {
        /// <summary>
        /// 为SkillEditorWindow添加便捷的Action添加方法
        /// </summary>
        public static void ShowActionSelectorAndAdd(this SkillEditorWindow editorWindow,
            int trackIndex, int targetFrame)
        {
            ActionSelectorUI.ShowActionSelector(actionType =>
            {
                // 使用反射调用泛型方法
                var addActionMethod = typeof(SkillEditorWindow)
                    .GetMethod("AddActionToTrack")
                    .MakeGenericMethod(actionType);

                addActionMethod.Invoke(editorWindow, new object[] { trackIndex, targetFrame });
            }, targetFrame);
        }

        /// <summary>
        /// 显示常用Action快速选择
        /// </summary>
        public static void ShowCommonActionSelectorAndAdd(this SkillEditorWindow editorWindow,
            int trackIndex, int targetFrame)
        {
            ActionSelectorUI.ShowCommonActionsMenu(actionType =>
            {
                // 使用反射调用泛型方法
                var addActionMethod = typeof(SkillEditorWindow)
                    .GetMethod("AddActionToTrack")
                    .MakeGenericMethod(actionType);

                addActionMethod.Invoke(editorWindow, new object[] { trackIndex, targetFrame });
            }, targetFrame);
        }
    }
}