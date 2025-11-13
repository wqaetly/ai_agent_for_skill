using UnityEngine;
using UnityEngine.UIElements;
using UnityEditor;
using UnityEditor.UIElements;
using System.Linq;
using SkillSystem.Data;
using SkillSystem.Actions;
using Sirenix.OdinInspector.Editor;
using Sirenix.OdinInspector;

namespace SkillSystem.Editor
{
    /// <summary>
    /// Action检视器 - 负责属性编辑和显示
    /// 职责：Action属性编辑、Track属性编辑、技能属性编辑、Inspector UI管理
    /// </summary>
    public class ActionInspector
    {
        private readonly SkillEditorWindow editor;
        private ScrollView inspectorContent;

        public ActionInspector(SkillEditorWindow editor)
        {
            this.editor = editor;
        }

        public void Initialize(VisualElement rootElement)
        {
            inspectorContent = rootElement.Q<ScrollView>("inspector-content");
        }

        private void Cleanup()
        {
            if (currentPropertyTree != null)
            {
                currentPropertyTree.Dispose();
                currentPropertyTree = null;
            }
        }

        public void Dispose()
        {
            Cleanup();
        }

        public void RefreshInspector(SkillData skillData, int selectedTrackIndex, int selectedActionIndex, int currentFrame)
        {
            if (inspectorContent == null) return;

            // Clear previous content and dispose any existing property tree
            Cleanup();
            inspectorContent.Clear();

            if (selectedTrackIndex >= 0 && selectedTrackIndex < skillData.tracks.Count)
            {
                var selectedTrack = skillData.tracks[selectedTrackIndex];

                if (selectedActionIndex >= 0 && selectedActionIndex < selectedTrack.actions.Count)
                {
                    var selectedAction = selectedTrack.actions[selectedActionIndex];
                    CreateActionInspector(selectedAction, skillData);
                }
                else
                {
                    CreateTrackInspector(selectedTrack, selectedTrackIndex, currentFrame);
                }
            }
            else
            {
                CreateSkillInspector(skillData);
            }
        }

        private void CreateActionInspector(ISkillAction action, SkillData skillData)
        {
            var titleLabel = new Label($"Selected Action: {action.GetDisplayName()}");
            titleLabel.style.unityFontStyleAndWeight = FontStyle.Bold;
            inspectorContent.Add(titleLabel);

            CreateActionProperties(action, skillData);

            // 添加REQ-04 AI参数助手面板
            AddSmartActionPanel(action, skillData);
        }

        private PropertyTree currentPropertyTree;

        private void CreateActionProperties(ISkillAction action, SkillData skillData)
        {
            // Add a separator
            AddSeparator();

            // Dispose previous property tree to prevent layout issues
            if (currentPropertyTree != null)
            {
                currentPropertyTree.Dispose();
                currentPropertyTree = null;
            }

            // Create new property tree and ensure proper lifecycle management
            currentPropertyTree = PropertyTree.Create(action);

            // Use Odin for all additional properties with proper error handling
            var odinContainer = new IMGUIContainer(() =>
            {
                try
                {
                    if (currentPropertyTree != null)
                    {
                        GUILayout.BeginVertical();
                        currentPropertyTree.Draw(false);
                        GUILayout.EndVertical();
                    }
                }
                catch (System.Exception e)
                {
                    GUILayout.Label($"Error drawing properties: {e.Message}");
                }
            });
            inspectorContent.Add(odinContainer);
        }

        /// <summary>
        /// 添加AI参数助手面板（REQ-04）
        /// </summary>
        private void AddSmartActionPanel(ISkillAction action, SkillData skillData)
        {
            // 查找当前选中的Track
            int selectedTrackIndex = editor.GetSelectedTrackIndex();
            var track = (selectedTrackIndex >= 0 && selectedTrackIndex < skillData.tracks.Count)
                ? skillData.tracks[selectedTrackIndex]
                : null;

            if (track == null)
                return;

            // RAG功能已迁移到WebUI，使用菜单: Tools → SkillAgent → 打开Web UI
            // 或访问 http://localhost:3000/rag 进行技能推荐

            // 注释掉原有的SmartActionInspector（已废弃，依赖已删除的EditorRAGClient）
            /*
            var smartPanelContainer = new IMGUIContainer(() =>
            {
                try
                {
                    SkillSystem.RAG.SmartActionInspectorEnhanced.DrawSmartPanel(
                        action,
                        skillData.skillName,
                        track.trackName,
                        selectedTrackIndex
                    );
                }
                catch (System.Exception e)
                {
                    GUILayout.Label($"Error drawing smart panel: {e.Message}");
                }
            });

            inspectorContent.Add(smartPanelContainer);
            */
        }

        private void CreateTrackInspector(SkillTrack track, int trackIndex, int currentFrame)
        {
            var titleLabel = new Label($"Selected Track: {track.trackName}");
            titleLabel.style.unityFontStyleAndWeight = FontStyle.Bold;
            inspectorContent.Add(titleLabel);

            CreateTrackProperties(track, trackIndex, currentFrame);
        }

        private void CreateTrackProperties(SkillTrack track, int trackIndex, int currentFrame)
        {
            // Track name
            var nameField = new TextField("Track Name");
            nameField.value = track.trackName;
            nameField.RegisterValueChangedCallback(evt =>
            {
                track.trackName = evt.newValue;
                editor.MarkDirty();
            });
            inspectorContent.Add(nameField);

            // Enabled toggle
            var enabledToggle = new Toggle("Enabled");
            enabledToggle.value = track.enabled;
            enabledToggle.RegisterValueChangedCallback(evt =>
            {
                track.enabled = evt.newValue;
                editor.OnTrackPropertyChanged();
            });
            inspectorContent.Add(enabledToggle);

            // Usage instructions
            var instructionsLabel = new Label("✨ How to add Actions:");
            instructionsLabel.style.unityFontStyleAndWeight = FontStyle.Bold;
            instructionsLabel.style.color = new Color(0.8f, 0.9f, 1.0f);
            instructionsLabel.style.marginBottom = 3;
            inspectorContent.Add(instructionsLabel);

            var instructionsText = new Label("1. Use buttons below to add at current frame\n2. Right-click on track timeline to add at specific position");
            instructionsText.style.fontSize = 10;
            instructionsText.style.color = new Color(0.7f, 0.7f, 0.7f);
            instructionsText.style.marginBottom = 8;
            instructionsText.style.whiteSpace = WhiteSpace.Normal;
            inspectorContent.Add(instructionsText);

            // Add actions list
            var actionsCount = track.actions?.Count ?? 0;
            var actionsLabel = new Label($"Actions ({actionsCount})");
            actionsLabel.style.unityFontStyleAndWeight = FontStyle.Bold;
            actionsLabel.style.marginTop = 5;
            inspectorContent.Add(actionsLabel);

            // Add Action buttons
            CreateActionButtons(trackIndex, currentFrame);

            // List existing actions
            CreateActionsList(track, trackIndex);

            // Use Odin for additional properties with proper error handling
            var trackOdinContainer = new IMGUIContainer(() =>
            {
                try
                {
                    var propertyTree = PropertyTree.Create(track);
                    GUILayout.BeginVertical();
                    propertyTree.Draw(false);
                    GUILayout.EndVertical();
                    propertyTree.Dispose();
                }
                catch (System.Exception e)
                {
                    GUILayout.Label($"Error drawing track properties: {e.Message}");
                }
            });
            inspectorContent.Add(trackOdinContainer);
        }

        private void CreateActionButtons(int trackIndex, int currentFrame)
        {
            var addActionContainer = new VisualElement();
            addActionContainer.style.flexDirection = FlexDirection.Row;
            addActionContainer.style.marginBottom = 8;
            addActionContainer.style.flexWrap = Wrap.Wrap;

            var addLogBtn = new Button(() => editor.AddActionToTrack<SkillSystem.Actions.LogAction>(trackIndex, currentFrame));
            addLogBtn.text = $"+ Log (F{currentFrame})";
            addLogBtn.style.marginRight = 3;
            addLogBtn.style.marginBottom = 2;
            addLogBtn.style.backgroundColor = new Color(0.2f, 0.6f, 0.8f);
            addActionContainer.Add(addLogBtn);

            var addCollisionBtn = new Button(() => editor.AddActionToTrack<SkillSystem.Actions.CollisionAction>(trackIndex, currentFrame));
            addCollisionBtn.text = $"+ Collision (F{currentFrame})";
            addCollisionBtn.style.marginRight = 3;
            addCollisionBtn.style.marginBottom = 2;
            addCollisionBtn.style.backgroundColor = new Color(0.8f, 0.4f, 0.2f);
            addActionContainer.Add(addCollisionBtn);

            var addAnimationBtn = new Button(() => editor.AddActionToTrack<SkillSystem.Actions.AnimationAction>(trackIndex, currentFrame));
            addAnimationBtn.text = $"+ Animation (F{currentFrame})";
            addAnimationBtn.style.marginBottom = 2;
            addAnimationBtn.style.backgroundColor = new Color(0.4f, 0.8f, 0.3f);
            addActionContainer.Add(addAnimationBtn);

            inspectorContent.Add(addActionContainer);
        }

        private void CreateActionsList(SkillTrack track, int trackIndex)
        {
            // 防御性检查：track.actions 可能在反序列化时为 null
            if (track.actions == null) return;

            for (int i = 0; i < track.actions.Count; i++)
            {
                var action = track.actions[i];
                // 防御性检查：action 可能为 null
                if (action == null) continue;
                var actionContainer = new VisualElement();
                actionContainer.style.flexDirection = FlexDirection.Row;
                actionContainer.style.alignItems = Align.Center;
                actionContainer.style.marginTop = 2;

                var actionLabel = new Label($"{action.GetDisplayName()} (Frame {action.frame})");
                actionLabel.style.flexGrow = 1;
                actionContainer.Add(actionLabel);

                int actionIndex = i; // Capture for closure
                var selectBtn = new Button(() => editor.SelectAction(trackIndex, actionIndex));
                selectBtn.text = "Select";
                selectBtn.style.width = 50;
                selectBtn.style.height = 16;
                selectBtn.style.fontSize = 8;
                selectBtn.style.marginRight = 2;
                actionContainer.Add(selectBtn);

                var deleteBtn = new Button(() => editor.DeleteAction(trackIndex, actionIndex));
                deleteBtn.text = "X";
                deleteBtn.style.width = 20;
                deleteBtn.style.height = 16;
                deleteBtn.style.fontSize = 8;
                actionContainer.Add(deleteBtn);

                inspectorContent.Add(actionContainer);
            }
        }

        private void CreateSkillInspector(SkillData skillData)
        {
            var titleLabel = new Label("Skill Properties");
            titleLabel.style.unityFontStyleAndWeight = FontStyle.Bold;
            inspectorContent.Add(titleLabel);

            // Usage guide when no track is selected
            CreateUsageGuide();

            // Create skill property fields
            CreateSkillProperties(skillData);
        }

        private void CreateUsageGuide()
        {
            var guideLabel = new Label("💡 Quick Start Guide:");
            guideLabel.style.unityFontStyleAndWeight = FontStyle.Bold;
            guideLabel.style.color = new Color(1.0f, 0.9f, 0.6f);
            guideLabel.style.marginTop = 10;
            inspectorContent.Add(guideLabel);

            var guideText = new Label("1. Click on a track header to select it\n2. Use Inspector buttons or right-click timeline to add actions\n3. Click on actions to edit their properties");
            guideText.style.fontSize = 10;
            guideText.style.color = new Color(0.8f, 0.8f, 0.8f);
            guideText.style.marginBottom = 10;
            guideText.style.whiteSpace = WhiteSpace.Normal;
            inspectorContent.Add(guideText);
        }

        private void CreateSkillProperties(SkillData skillData)
        {
            // Skill name
            var nameField = new TextField("Skill Name");
            nameField.value = skillData.skillName;
            nameField.RegisterValueChangedCallback(evt =>
            {
                skillData.skillName = evt.newValue;
                editor.MarkDirty();
            });
            inspectorContent.Add(nameField);

            // Total duration
            var durationField = new IntegerField("Total Duration");
            durationField.value = skillData.totalDuration;
            durationField.RegisterValueChangedCallback(evt =>
            {
                skillData.totalDuration = Mathf.Max(1, evt.newValue);
                editor.OnSkillPropertyChanged();
            });
            inspectorContent.Add(durationField);

            // Frame rate
            var frameRateField = new IntegerField("Frame Rate");
            frameRateField.value = skillData.frameRate;
            frameRateField.RegisterValueChangedCallback(evt =>
            {
                skillData.frameRate = Mathf.Max(1, evt.newValue);
                editor.MarkDirty();
            });
            inspectorContent.Add(frameRateField);

            // Use Odin for additional properties with proper error handling
            var skillOdinContainer = new IMGUIContainer(() =>
            {
                try
                {
                    var propertyTree = PropertyTree.Create(skillData);
                    GUILayout.BeginVertical();
                    propertyTree.Draw(false);
                    GUILayout.EndVertical();
                    propertyTree.Dispose();
                }
                catch (System.Exception e)
                {
                    GUILayout.Label($"Error drawing skill properties: {e.Message}");
                }
            });
            inspectorContent.Add(skillOdinContainer);
        }

        private void AddSeparator()
        {
            var separator = new VisualElement();
            separator.style.height = 1;
            separator.style.backgroundColor = new Color(0.3f, 0.3f, 0.3f);
            separator.style.marginTop = 5;
            separator.style.marginBottom = 5;
            inspectorContent.Add(separator);
        }

    }
}