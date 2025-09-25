using UnityEngine;
using SkillSystem.Runtime;
using SkillSystem.Data;
using SkillSystem.Actions;

namespace SkillSystem.Runtime
{
    public class SkillPlayerController : MonoBehaviour
    {
        [Header("Skill Player Reference")]
        [SerializeField] private SkillPlayer skillPlayer;

        [Header("Debug Controls")]
        [SerializeField] private bool showDebugGUI = true;
        [SerializeField] private KeyCode playKey = KeyCode.Space;
        [SerializeField] private KeyCode stopKey = KeyCode.S;
        [SerializeField] private KeyCode pauseKey = KeyCode.P;

        [Header("Test Skill")]
        [SerializeField] private string testSkillPath = "";

        private void Awake()
        {
            if (skillPlayer == null)
            {
                skillPlayer = GetComponent<SkillPlayer>();
                if (skillPlayer == null)
                {
                    skillPlayer = gameObject.AddComponent<SkillPlayer>();
                }
            }

            // Subscribe to events
            skillPlayer.OnSkillStarted += OnSkillStarted;
            skillPlayer.OnSkillFinished += OnSkillFinished;
            skillPlayer.OnFrameChanged += OnFrameChanged;
            skillPlayer.OnActionExecuted += OnActionExecuted;
        }

        private void OnDestroy()
        {
            // Unsubscribe from events
            if (skillPlayer != null)
            {
                skillPlayer.OnSkillStarted -= OnSkillStarted;
                skillPlayer.OnSkillFinished -= OnSkillFinished;
                skillPlayer.OnFrameChanged -= OnFrameChanged;
                skillPlayer.OnActionExecuted -= OnActionExecuted;
            }
        }

        private void Update()
        {
            HandleInput();
        }

        private void HandleInput()
        {
            if (Input.GetKeyDown(playKey))
            {
                if (skillPlayer.IsPlaying)
                {
                    skillPlayer.ResumeSkill();
                }
                else
                {
                    if (!string.IsNullOrEmpty(testSkillPath))
                    {
                        skillPlayer.LoadAndPlaySkill(testSkillPath);
                    }
                    else
                    {
                        skillPlayer.PlaySkill();
                    }
                }
            }

            if (Input.GetKeyDown(stopKey))
            {
                skillPlayer.StopSkill();
            }

            if (Input.GetKeyDown(pauseKey))
            {
                if (skillPlayer.IsPlaying)
                {
                    skillPlayer.PauseSkill();
                }
                else
                {
                    skillPlayer.ResumeSkill();
                }
            }
        }

        private void OnGUI()
        {
            if (!showDebugGUI) return;

            GUILayout.BeginArea(new Rect(10, 10, 300, 200));
            GUILayout.BeginVertical("box");

            GUILayout.Label("Skill Player Controller", GUI.skin.label);

            if (skillPlayer.CurrentSkillData != null)
            {
                GUILayout.Label($"Skill: {skillPlayer.CurrentSkillData.skillName}");
                GUILayout.Label($"Frame: {skillPlayer.CurrentFrame}/{skillPlayer.CurrentSkillData.totalDuration}");
                GUILayout.Label($"Progress: {skillPlayer.Progress:P1}");
                GUILayout.Label($"Playing: {skillPlayer.IsPlaying}");
                GUILayout.Label($"Active Actions: {skillPlayer.GetActiveActions().Count}");
            }
            else
            {
                GUILayout.Label("No skill loaded");
            }

            GUILayout.Space(10);

            GUILayout.BeginHorizontal();
            if (GUILayout.Button("Play"))
            {
                if (!string.IsNullOrEmpty(testSkillPath))
                {
                    skillPlayer.LoadAndPlaySkill(testSkillPath);
                }
                else
                {
                    skillPlayer.PlaySkill();
                }
            }

            if (GUILayout.Button("Stop"))
            {
                skillPlayer.StopSkill();
            }

            if (GUILayout.Button("Pause"))
            {
                if (skillPlayer.IsPlaying)
                {
                    skillPlayer.PauseSkill();
                }
                else
                {
                    skillPlayer.ResumeSkill();
                }
            }
            GUILayout.EndHorizontal();

            GUILayout.Space(5);
            GUILayout.Label("Controls:");
            GUILayout.Label($"Play/Resume: {playKey}");
            GUILayout.Label($"Stop: {stopKey}");
            GUILayout.Label($"Pause: {pauseKey}");

            GUILayout.EndVertical();
            GUILayout.EndArea();
        }

        // Event handlers
        private void OnSkillStarted(SkillData skillData)
        {
            Debug.Log($"Skill started: {skillData.skillName}");
        }

        private void OnSkillFinished(SkillData skillData)
        {
            Debug.Log($"Skill finished: {skillData.skillName}");
        }

        private void OnFrameChanged(int frame)
        {
            // Debug.Log($"Frame changed to: {frame}");
        }

        private void OnActionExecuted(ISkillAction action)
        {
            Debug.Log($"Action executed: {action.GetActionName()} at frame {action.frame}");
        }
    }
}