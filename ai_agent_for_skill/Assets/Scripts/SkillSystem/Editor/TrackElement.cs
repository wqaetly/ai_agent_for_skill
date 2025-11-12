using UnityEngine;
using UnityEngine.UIElements;
using UnityEditor.UIElements;
using SkillSystem.Data;
using System.Linq;

namespace SkillSystem.Editor
{
    public class TrackElement : VisualElement
    {
        private SkillTrack track;
        private SkillEditorWindow editorWindow;
        private int trackIndex;

        // UI Elements
        private TextField nameField;
        private Toggle enabledToggle;
        private Button deleteButton;

        public SkillTrack Track => track;
        public int TrackIndex => trackIndex;

        public TrackElement(SkillTrack track, int trackIndex, SkillEditorWindow editorWindow)
        {
            this.track = track;
            this.trackIndex = trackIndex;
            this.editorWindow = editorWindow;

            CreateHeader();
            CreateTrackRow();
            UpdateAppearance();
        }

        private void CreateHeader()
        {
            var header = new VisualElement();
            header.AddToClassList("track-header");

            nameField = new TextField();
            nameField.AddToClassList("track-name-field");
            nameField.value = track.trackName;
            nameField.RegisterValueChangedCallback(evt =>
            {
                track.trackName = evt.newValue;
                editorWindow.MarkDirty();
            });


            enabledToggle = new Toggle();
            enabledToggle.AddToClassList("track-enabled-toggle");
            enabledToggle.value = track.enabled;
            enabledToggle.RegisterValueChangedCallback(evt =>
            {
                track.enabled = evt.newValue;
                UpdateAppearance();
                editorWindow.MarkDirty();
            });

            deleteButton = new Button(() => editorWindow.DeleteTrack(this.trackIndex));
            deleteButton.AddToClassList("track-delete-button");
            deleteButton.text = "X";

            header.Add(nameField);
            header.Add(enabledToggle);
            header.Add(deleteButton);

            // Header click event for selection
            header.RegisterCallback<MouseDownEvent>(evt =>
            {
                if (evt.button == 0)
                {
                    editorWindow.SelectTrack(this.trackIndex);
                    evt.StopPropagation();
                }
            });

            this.Add(header);
        }

        private void CreateTrackRow()
        {
            var trackRow = new VisualElement();
            trackRow.AddToClassList("track-row");
            trackRow.name = $"track-row-{trackIndex}";

            // 确保track row有合适的尺寸和交互能力
            trackRow.style.minHeight = 30;
            // 宽度由CSS控制，确保无限长背景
            trackRow.pickingMode = PickingMode.Position; // 确保能接收鼠标事件

            // 直接为track row设置右键菜单
            SetupTrackRowContextMenu(trackRow);

            this.Add(trackRow);
        }

        private void SetupTrackRowContextMenu(VisualElement trackRow)
        {
            trackRow.RegisterCallback<MouseDownEvent>(evt =>
            {
                if (evt.button == 1) // 右键
                {
                    int targetFrame = GetFrameFromPosition(evt.localMousePosition.x);
                    editorWindow.ShowActionSelectorAndAdd(this.trackIndex, targetFrame);
                    evt.StopPropagation();
                }
            });
        }

        private int GetFrameFromPosition(float xPosition)
        {
            // 专业坐标转换，参考Unity Timeline实现
            float scrollOffset = editorWindow.GetCurrentScrollOffset();
            int frame = Mathf.FloorToInt((xPosition + scrollOffset) / editorWindow.FrameWidth);
            return Mathf.Clamp(frame, 0, editorWindow.CurrentSkillData.totalDuration - 1);
        }

        private void UpdateAppearance()
        {
            if (!track.enabled)
            {
                AddToClassList("disabled");
            }
            else
            {
                RemoveFromClassList("disabled");
            }
        }


        public void SetSelected(bool selected)
        {
            var header = this.Children().FirstOrDefault();
            if (header != null)
            {
                if (selected)
                {
                    header.AddToClassList("selected");
                }
                else
                {
                    header.RemoveFromClassList("selected");
                }
            }

            var trackRow = this.Q<VisualElement>($"track-row-{trackIndex}");
            if (trackRow != null)
            {
                if (selected)
                {
                    trackRow.AddToClassList("selected");
                }
                else
                {
                    trackRow.RemoveFromClassList("selected");
                }
            }
        }

        public void UpdateTrackIndex(int newIndex)
        {
            trackIndex = newIndex;
            var trackRow = this.Q<VisualElement>($"track-row-{trackIndex}");
            if (trackRow != null)
            {
                trackRow.name = $"track-row-{newIndex}";
            }
        }

        public VisualElement GetTrackRow()
        {
            return this.Q<VisualElement>($"track-row-{trackIndex}");
        }
    }
}