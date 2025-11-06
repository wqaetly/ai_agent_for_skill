using UnityEngine;
using UnityEngine.UIElements;
using UnityEditor;
using UnityEditor.UIElements;
using SkillSystem.Data;

namespace SkillSystem.Editor
{
    /// <summary>
    /// 播放控制器 - 负责技能播放和帧控制
    /// 职责：播放/暂停控制、帧数控制、播放状态管理、时长管理
    /// </summary>
    public class PlaybackController
    {
        private readonly SkillEditorWindow editor;

        // Playback state
        private bool isPlaying = false;
        private float playSpeed = 1.0f;
        private float lastPlayTime;

        // UI Elements
        private Button playButton;
        private IntegerField currentFrameField;
        private SliderInt frameSlider;
        private IntegerField totalDurationField;
        private Button setDurationButton;
        private Label frameInfoLabel;

        // State management
        private bool isUpdatingFrameControls = false;

        public bool IsPlaying => isPlaying;
        public float PlaySpeed { get => playSpeed; set => playSpeed = value; }

        public PlaybackController(SkillEditorWindow editor)
        {
            this.editor = editor;
        }

        public void Initialize(VisualElement rootElement)
        {
            // Get UI element references
            playButton = rootElement.Q<Button>("play-button");
            currentFrameField = rootElement.Q<IntegerField>("current-frame");
            frameSlider = rootElement.Q<SliderInt>("frame-slider");
            totalDurationField = rootElement.Q<IntegerField>("total-duration");
            setDurationButton = rootElement.Q<Button>("set-duration-button");
            frameInfoLabel = rootElement.Q<Label>("frame-info");

            BindEvents();
        }

        private void BindEvents()
        {
            // Playback control
            if (playButton != null)
                playButton.clicked += TogglePlayback;

            // Frame control events
            if (currentFrameField != null)
                currentFrameField.RegisterValueChangedCallback(evt => editor.SetCurrentFrame(evt.newValue));
            if (frameSlider != null)
                frameSlider.RegisterValueChangedCallback(evt => editor.SetCurrentFrame(evt.newValue));
            if (setDurationButton != null)
                setDurationButton.clicked += () => editor.SetTotalDuration(totalDurationField.value);
        }

        public void UpdateFrameControls(SkillData skillData, int currentFrame)
        {
            if (isUpdatingFrameControls || skillData == null) return;
            isUpdatingFrameControls = true;

            int maxFrame = skillData.totalDuration; // Allow up to totalDuration

            // Update frame controls
            if (currentFrameField != null)
                currentFrameField.value = currentFrame;

            if (frameSlider != null)
            {
                frameSlider.lowValue = 0;
                frameSlider.highValue = maxFrame;
                frameSlider.value = currentFrame;
            }

            // Update duration display
            if (totalDurationField != null)
                totalDurationField.value = skillData.totalDuration;

            if (frameInfoLabel != null)
                frameInfoLabel.text = $"Frame: {currentFrame}/{skillData.totalDuration} (Duration: {skillData.totalDuration})";

            // Update play button
            UpdatePlayButton();

            isUpdatingFrameControls = false;
        }

        private void UpdatePlayButton()
        {
            if (playButton == null) return;

            playButton.text = isPlaying ? "Stop" : "Play";
            playButton.RemoveFromClassList("playing");
            if (isPlaying)
                playButton.AddToClassList("playing");
        }

        private void TogglePlayback()
        {
            isPlaying = !isPlaying;
            if (isPlaying)
            {
                lastPlayTime = Time.realtimeSinceStartup;
                // Start skill execution when playback starts
                editor.StartSkillExecution();
            }
            else
            {
                // Stop skill execution when playback stops
                editor.StopSkillExecution();
            }
            UpdatePlayButton();
        }

        public void UpdatePlayback(SkillData skillData, int currentFrame)
        {
            if (!isPlaying || skillData == null) return;

            float currentTime = Time.realtimeSinceStartup;
            float deltaTime = currentTime - lastPlayTime;
            lastPlayTime = currentTime;

            float frameAdvance = deltaTime * skillData.frameRate * playSpeed;
            int newFrame = Mathf.RoundToInt(currentFrame + frameAdvance);

            if (newFrame >= skillData.totalDuration)
            {
                newFrame = 0; // Loop
                // isPlaying = false; // Or stop at end
            }

            editor.SetCurrentFrame(newFrame);
        }

        public void StopPlayback()
        {
            if (isPlaying)
            {
                isPlaying = false;
                // Stop skill execution when playback stops
                editor.StopSkillExecution();
                UpdatePlayButton();
            }
        }

        public void SetFrame(int frame, SkillData skillData)
        {
            if (skillData == null) return;

            // Allow frame range from 0 to totalDuration (inclusive) to match ruler display
            int clampedFrame = Mathf.Clamp(frame, 0, skillData.totalDuration);

            // Notify editor about frame change
            editor.OnFrameChanged(clampedFrame);
        }

        public void SetTotalDuration(int newDuration, SkillData skillData, int currentFrame)
        {
            if (skillData == null) return;

            if (newDuration < 1) newDuration = 1;

            // Clamp current frame if needed
            int clampedFrame = Mathf.Clamp(currentFrame, 0, newDuration - 1);

            // Update skill data
            skillData.totalDuration = newDuration;

            // Clamp actions that extend beyond new duration
            foreach (var track in skillData.tracks)
            {
                // 防御性检查：track.actions 可能在反序列化时为 null
                if (track.actions == null) continue;

                foreach (var action in track.actions)
                {
                    // 防御性检查：action 可能为 null
                    if (action == null) continue;

                    if (action.frame >= newDuration)
                    {
                        action.frame = newDuration - 1;
                    }
                    if (action.frame + action.duration > newDuration)
                    {
                        action.duration = newDuration - action.frame;
                        if (action.duration < 1) action.duration = 1;
                    }
                }
            }

            // Notify editor about duration change
            editor.OnDurationChanged(clampedFrame);
        }

        public void OnTimelineMouseDown(MouseDownEvent evt, float frameWidth, float scrollOffset)
        {
            if (evt.button == 0) // Left click
            {
                // Use RoundToInt to allow reaching the last frame more easily
                int clickedFrame = Mathf.RoundToInt((evt.localMousePosition.x + scrollOffset) / frameWidth);
                editor.SetCurrentFrame(clickedFrame);
            }
        }
    }
}