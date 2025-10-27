using UnityEngine;
using UnityEngine.UIElements;
using SkillSystem.Actions;

namespace SkillSystem.Editor
{
    public enum ResizeHandle
    {
        None,
        Left,
        Right
    }

    public class SkillActionElement : VisualElement
    {
        private ISkillAction action;
        private SkillEditorWindow editorWindow;
        private int trackIndex;
        private int actionIndex;

        // UI Elements
        private Label actionLabel;
        private Label durationLabel;
        private VisualElement leftHandle;
        private VisualElement rightHandle;

        // Drag and resize state
        private bool isDragging = false;
        private bool isResizing = false;
        private ResizeHandle activeResizeHandle = ResizeHandle.None;
        private Vector2 dragStartPosition;
        private int originalFrame;
        private int originalDuration;

        public ISkillAction Action => action;
        public int TrackIndex => trackIndex;
        public int ActionIndex => actionIndex;
        public bool IsDragging => isDragging;
        public bool IsResizing => isResizing;
        public ResizeHandle ActiveResizeHandle => activeResizeHandle;

        public SkillActionElement(ISkillAction action, int trackIndex, int actionIndex, SkillEditorWindow editorWindow)
        {
            this.action = action;
            this.trackIndex = trackIndex;
            this.actionIndex = actionIndex;
            this.editorWindow = editorWindow;

            CreateActionElement();
            UpdateAppearance();
            UpdatePosition();
        }

        private void CreateActionElement()
        {
            AddToClassList("skill-action");

            // Action label
            actionLabel = new Label(action.GetDisplayName());
            actionLabel.AddToClassList("action-label");
            this.Add(actionLabel);

            // Duration label
            durationLabel = new Label($"{action.duration}f");
            durationLabel.AddToClassList("action-duration-label");
            this.Add(durationLabel);

            // Resize handles
            leftHandle = new VisualElement();
            leftHandle.AddToClassList("action-resize-handle");
            leftHandle.AddToClassList("left");
            this.Add(leftHandle);

            rightHandle = new VisualElement();
            rightHandle.AddToClassList("action-resize-handle");
            rightHandle.AddToClassList("right");
            this.Add(rightHandle);

            // Event handlers
            RegisterCallback<MouseDownEvent>(OnMouseDown);
            RegisterCallback<MouseMoveEvent>(OnMouseMove);
            RegisterCallback<MouseUpEvent>(OnMouseUp);
            RegisterCallback<MouseLeaveEvent>(OnMouseLeave);

            // Handle events
            leftHandle.RegisterCallback<MouseDownEvent>(evt => StartResize(ResizeHandle.Left, evt));
            rightHandle.RegisterCallback<MouseDownEvent>(evt => StartResize(ResizeHandle.Right, evt));

            // Selection event
            RegisterCallback<MouseDownEvent>(evt =>
            {
                if (evt.button == 0 && !isResizing)
                {
                    editorWindow.SelectAction(this.trackIndex, this.actionIndex);
                    evt.StopPropagation();
                }
            });

            // Context menu for deletion
            this.AddManipulator(new ContextualMenuManipulator((evt =>
            {
                evt.menu.AppendAction("Delete Action", _ => editorWindow.DeleteAction(this.trackIndex, this.actionIndex));
            })));
        }

        private void OnMouseDown(MouseDownEvent evt)
        {
            if (evt.button == 0 && activeResizeHandle == ResizeHandle.None)
            {
                isDragging = true;
                dragStartPosition = evt.mousePosition;
                originalFrame = action.frame;
                this.CaptureMouse();
                evt.StopPropagation();
            }
        }

        private void OnMouseMove(MouseMoveEvent evt)
        {
            if (isDragging)
            {
                Vector2 delta = evt.mousePosition - dragStartPosition;
                int frameDelta = Mathf.RoundToInt(delta.x / editorWindow.FrameWidth);
                int newFrame = Mathf.Clamp(originalFrame + frameDelta, 0,
                    editorWindow.CurrentSkillData.totalDuration - action.duration);

                if (newFrame != action.frame)
                {
                    action.frame = newFrame;
                    UpdatePosition();
                    editorWindow.MarkDirty();
                }
            }
            else if (isResizing)
            {
                Vector2 delta = evt.mousePosition - dragStartPosition;
                int frameDelta = Mathf.RoundToInt(delta.x / editorWindow.FrameWidth);

                if (activeResizeHandle == ResizeHandle.Left)
                {
                    int newFrame = Mathf.Clamp(originalFrame + frameDelta, 0, originalFrame + originalDuration - 1);
                    int newDuration = originalDuration - (newFrame - originalFrame);

                    if (newDuration > 0)
                    {
                        action.frame = newFrame;
                        action.duration = newDuration;
                        UpdatePosition();
                        UpdateAppearance();
                        editorWindow.MarkDirty();
                    }
                }
                else if (activeResizeHandle == ResizeHandle.Right)
                {
                    int newDuration = Mathf.Clamp(originalDuration + frameDelta, 1,
                        editorWindow.CurrentSkillData.totalDuration - action.frame);

                    if (newDuration != action.duration)
                    {
                        action.duration = newDuration;
                        UpdatePosition();
                        UpdateAppearance();
                        editorWindow.MarkDirty();
                    }
                }
            }
        }

        private void OnMouseUp(MouseUpEvent evt)
        {
            if (isDragging)
            {
                isDragging = false;
                this.ReleaseMouse();
            }

            if (isResizing)
            {
                isResizing = false;
                activeResizeHandle = ResizeHandle.None;
                this.ReleaseMouse();
            }
        }

        private void OnMouseLeave(MouseLeaveEvent evt)
        {
            // Keep dragging/resizing when mouse leaves the element
        }

        private void StartResize(ResizeHandle handle, MouseDownEvent evt)
        {
            if (evt.button == 0)
            {
                isResizing = true;
                activeResizeHandle = handle;
                dragStartPosition = evt.mousePosition;
                originalFrame = action.frame;
                originalDuration = action.duration;
                this.CaptureMouse();
                evt.StopPropagation();
            }
        }

        public void UpdatePosition()
        {
            this.style.left = action.frame * editorWindow.FrameWidth;
            this.style.width = action.duration * editorWindow.FrameWidth;
        }

        public void UpdateAppearance()
        {
            // Update color based on action type and enabled state
            var actionColor = GetActionTypeColor();
            this.style.backgroundColor = action.enabled ? actionColor : Color.gray;

            // Update labels
            actionLabel.text = action.GetDisplayName();
            durationLabel.text = $"{action.duration}f";

            // Update enabled state
            if (!action.enabled)
            {
                AddToClassList("disabled");
            }
            else
            {
                RemoveFromClassList("disabled");
            }
        }

        private Color GetActionTypeColor()
        {
            // Assign distinct colors based on action type
            switch (action)
            {
                case SkillSystem.Actions.LogAction _:
                    return new Color(0.4f, 0.8f, 0.4f); // Green for Log actions
                case SkillSystem.Actions.CollisionAction _:
                    return new Color(0.8f, 0.4f, 0.4f); // Red for Collision actions
                case SkillSystem.Actions.AnimationAction _:
                    return new Color(0.4f, 0.4f, 0.8f); // Blue for Animation actions
                default:
                    return new Color(0.6f, 0.6f, 0.6f); // Gray for unknown types
            }
        }

        public void SetSelected(bool selected)
        {
            if (selected)
            {
                AddToClassList("selected");
            }
            else
            {
                RemoveFromClassList("selected");
            }
        }

        public void UpdateIndices(int newTrackIndex, int newActionIndex)
        {
            trackIndex = newTrackIndex;
            actionIndex = newActionIndex;
        }

        /// <summary>
        /// Sets the execution state for visual feedback during skill execution
        /// </summary>
        /// <param name="isExecuting">Whether the action is currently being executed</param>
        /// <param name="isTicking">Whether the action is in its ticking phase</param>
        public void SetExecutionState(bool isExecuting, bool isTicking)
        {
            // Remove all execution state classes first
            RemoveFromClassList("executing");
            RemoveFromClassList("ticking");
            RemoveFromClassList("entered");

            if (isExecuting)
            {
                AddToClassList("executing");

                if (isTicking)
                {
                    AddToClassList("ticking");
                }
                else
                {
                    AddToClassList("entered");
                }

                // Add visual glow effect for executing actions
                this.style.borderTopWidth = 2;
                this.style.borderRightWidth = 2;
                this.style.borderBottomWidth = 2;
                this.style.borderLeftWidth = 2;
                this.style.borderTopColor = Color.yellow;
                this.style.borderRightColor = Color.yellow;
                this.style.borderBottomColor = Color.yellow;
                this.style.borderLeftColor = Color.yellow;
            }
            else
            {
                // Reset border when not executing
                this.style.borderTopWidth = 0;
                this.style.borderRightWidth = 0;
                this.style.borderBottomWidth = 0;
                this.style.borderLeftWidth = 0;
            }
        }
    }
}