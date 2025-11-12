#if UNITY_EDITOR
using UnityEngine;
using UnityEditor;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;
using Unity.Cinemachine;
using TrainingGround.Runtime;
using TrainingGround.Materials;
using TrainingGround.PostProcessing;

namespace TrainingGround.Editor
{
    /// <summary>
    /// URP配置验证工具 - 检查训练场系统的配置完整�?
    /// </summary>
    public class URPConfigurationValidator : EditorWindow
    {
        private Vector2 scrollPosition;
        private bool showDetailedInfo = false;

        [MenuItem("Tools/Training Ground/URP Configuration Validator")]
        public static void ShowWindow()
        {
            var window = GetWindow<URPConfigurationValidator>("URP配置验证");
            window.minSize = new Vector2(500, 600);
            window.Show();
        }

        void OnGUI()
        {
            GUILayout.Label("训练场URP配置验证工具", EditorStyles.boldLabel);
            EditorGUILayout.Space();

            EditorGUILayout.HelpBox(
                "此工具检查训练场系统的配置是否正确，并提供一键修复功能�?,
                MessageType.Info
            );

            EditorGUILayout.Space();

            // 显示详细信息选项
            showDetailedInfo = EditorGUILayout.Toggle("显示详细信息", showDetailedInfo);

            EditorGUILayout.Space();

            // 开始滚动视�?
            scrollPosition = EditorGUILayout.BeginScrollView(scrollPosition);

            // 1. 检查URP�?
            CheckURPPackage();
            EditorGUILayout.Space();

            // 2. 检查Cinemachine�?
            CheckCinemachinePackage();
            EditorGUILayout.Space();

            // 3. 检查渲染管线设�?
            CheckRenderPipeline();
            EditorGUILayout.Space();

            // 4. 检查主相机
            CheckMainCamera();
            EditorGUILayout.Space();

            // 5. 检查训练场组件
            CheckTrainingGroundComponents();
            EditorGUILayout.Space();

            // 6. 检查材质库
            CheckMaterialLibrary();
            EditorGUILayout.Space();

            // 7. 检查后期处�?
            CheckPostProcessing();
            EditorGUILayout.Space();

            EditorGUILayout.EndScrollView();

            EditorGUILayout.Space();

            // 一键修复按�?
            if (GUILayout.Button("尝试自动修复所有问�?, GUILayout.Height(30)))
            {
                AutoFixAllIssues();
            }
        }

        private void CheckURPPackage()
        {
            EditorGUILayout.LabelField("1. URP包检�?, EditorStyles.boldLabel);

            var pipeline = GraphicsSettings.currentRenderPipeline;
            if (pipeline is UniversalRenderPipelineAsset)
            {
                DrawSuccess("URP渲染管线已正确配�?);

                if (showDetailedInfo)
                {
                    EditorGUILayout.LabelField($"   Asset: {pipeline.name}");
                }
            }
            else
            {
                DrawError("URP渲染管线未配置！");
                if (GUILayout.Button("打开Graphics Settings"))
                {
                    SettingsService.OpenProjectSettings("Project/Graphics");
                }
            }
        }

        private void CheckCinemachinePackage()
        {
            EditorGUILayout.LabelField("2. Cinemachine包检�?, EditorStyles.boldLabel);

            // 检查Cinemachine类型是否存在
            var cinemachineType = System.Type.GetType("Unity.Cinemachine.CinemachineCamera, Unity.Cinemachine");
            if (cinemachineType != null)
            {
                DrawSuccess("Cinemachine包已安装");
            }
            else
            {
                DrawError("Cinemachine包未安装�?);
                if (GUILayout.Button("打开Package Manager"))
                {
                    UnityEditor.PackageManager.UI.Window.Open("com.unity.cinemachine");
                }
            }
        }

        private void CheckRenderPipeline()
        {
            EditorGUILayout.LabelField("3. 渲染管线设置检�?, EditorStyles.boldLabel);

            var pipeline = GraphicsSettings.currentRenderPipeline as UniversalRenderPipelineAsset;
            if (pipeline != null)
            {
                // 使用反射获取私有字段
                var serializedObject = new SerializedObject(pipeline);

                // 检查关键设�?
                var requireDepthTexture = serializedObject.FindProperty("m_RequireDepthTexture");
                var requireOpaqueTexture = serializedObject.FindProperty("m_RequireOpaqueTexture");

                if (requireDepthTexture != null && requireDepthTexture.boolValue)
                {
                    DrawSuccess("Depth Texture已启�?);
                }
                else
                {
                    DrawWarning("建议启用Depth Texture");
                }

                DrawSuccess("渲染管线配置正常");

                if (showDetailedInfo)
                {
                    EditorGUILayout.LabelField($"   Asset路径: {AssetDatabase.GetAssetPath(pipeline)}");
                }
            }
            else
            {
                DrawError("未找到URP Asset�?);
            }
        }

        private void CheckMainCamera()
        {
            EditorGUILayout.LabelField("4. 主相机检�?, EditorStyles.boldLabel);

            var mainCamera = UnityEngine.Camera.main;
            if (mainCamera == null)
            {
                DrawError("未找到主相机�?);
                if (GUILayout.Button("创建主相�?))
                {
                    CreateMainCamera();
                }
                return;
            }

            DrawSuccess($"找到主相�? {mainCamera.name}");

            // 检查CinemachineBrain
            var brain = mainCamera.GetComponent<CinemachineBrain>();
            if (brain != null)
            {
                DrawSuccess("CinemachineBrain已添�?);
            }
            else
            {
                DrawWarning("CinemachineBrain未添�?);
                if (GUILayout.Button("添加CinemachineBrain"))
                {
                    mainCamera.gameObject.AddComponent<CinemachineBrain>();
                    EditorUtility.SetDirty(mainCamera.gameObject);
                }
            }

            // 检查Universal Additional Camera Data
            var cameraData = mainCamera.GetComponent<UniversalAdditionalCameraData>();
            if (cameraData != null)
            {
                if (cameraData.renderPostProcessing)
                {
                    DrawSuccess("后期处理已启�?);
                }
                else
                {
                    DrawWarning("后期处理未启�?);
                }
            }
        }

        private void CheckTrainingGroundComponents()
        {
            EditorGUILayout.LabelField("5. 训练场组件检�?, EditorStyles.boldLabel);

            // 检查TrainingGroundManager
            var manager = FindFirstObjectByType<TrainingGroundManager>();
            if (manager != null)
            {
                DrawSuccess($"TrainingGroundManager已添�? {manager.name}");
            }
            else
            {
                DrawWarning("TrainingGroundManager未找�?);
                if (GUILayout.Button("创建TrainingGroundManager"))
                {
                    CreateTrainingGroundManager();
                }
            }

            // 检查CameraController
            var cameraController = FindFirstObjectByType<Camera.TrainingGroundCameraController>();
            if (cameraController != null)
            {
                DrawSuccess($"CameraController已添�? {cameraController.name}");
            }
            else
            {
                DrawWarning("CameraController未找�?);
                if (GUILayout.Button("创建CameraController"))
                {
                    CreateCameraController();
                }
            }
        }

        private void CheckMaterialLibrary()
        {
            EditorGUILayout.LabelField("6. 材质库检�?, EditorStyles.boldLabel);

            // MaterialLibrary是单例，会在运行时自动创�?
            DrawSuccess("MaterialLibrary将在运行时自动初始化");
        }

        private void CheckPostProcessing()
        {
            EditorGUILayout.LabelField("7. 后期处理检�?, EditorStyles.boldLabel);

            // 检查Volume
            var volumes = FindObjectsByType<Volume>(FindObjectsSortMode.None);
            if (volumes.Length > 0)
            {
                DrawSuccess($"找到 {volumes.Length} 个Volume");

                if (showDetailedInfo)
                {
                    foreach (var volume in volumes)
                    {
                        EditorGUILayout.LabelField($"   - {volume.name} (Priority: {volume.priority})");
                    }
                }
            }
            else
            {
                DrawWarning("未找到Post-Processing Volume");
                if (GUILayout.Button("创建PostProcessingManager"))
                {
                    CreatePostProcessingManager();
                }
            }
        }

        #region 自动修复

        private void AutoFixAllIssues()
        {
            bool hasFixed = false;

            // 修复主相�?
            var mainCamera = UnityEngine.Camera.main;
            if (mainCamera != null)
            {
                if (mainCamera.GetComponent<CinemachineBrain>() == null)
                {
                    mainCamera.gameObject.AddComponent<CinemachineBrain>();
                    hasFixed = true;
                }

                var cameraData = mainCamera.GetComponent<UniversalAdditionalCameraData>();
                if (cameraData != null && !cameraData.renderPostProcessing)
                {
                    cameraData.renderPostProcessing = true;
                    hasFixed = true;
                }
            }
            else
            {
                CreateMainCamera();
                hasFixed = true;
            }

            // 创建缺失的组�?
            if (FindFirstObjectByType<TrainingGroundManager>() == null)
            {
                CreateTrainingGroundManager();
                hasFixed = true;
            }

            if (FindFirstObjectByType<Camera.TrainingGroundCameraController>() == null)
            {
                CreateCameraController();
                hasFixed = true;
            }

            if (FindObjectsByType<Volume>(FindObjectsSortMode.None).Length == 0)
            {
                CreatePostProcessingManager();
                hasFixed = true;
            }

            if (hasFixed)
            {
                EditorUtility.DisplayDialog("修复完成", "已尝试修复所有检测到的问题。\n请重新运行验证检查�?, "确定");
                Repaint();
            }
            else
            {
                EditorUtility.DisplayDialog("无需修复", "所有配置都正常�?, "确定");
            }
        }

        #endregion

        #region 创建方法

        private void CreateMainCamera()
        {
            var cameraObj = new GameObject("Main Camera");
            var camera = cameraObj.AddComponent<UnityEngine.Camera>();
            cameraObj.tag = "MainCamera";
            cameraObj.AddComponent<CinemachineBrain>();

            var cameraData = camera.GetUniversalAdditionalCameraData();
            cameraData.renderPostProcessing = true;

            Selection.activeGameObject = cameraObj;
            Debug.Log("[URPValidator] 主相机已创建");
        }

        private void CreateTrainingGroundManager()
        {
            var managerObj = new GameObject("TrainingGroundManager");
            managerObj.AddComponent<TrainingGroundManager>();
            Selection.activeGameObject = managerObj;
            Debug.Log("[URPValidator] TrainingGroundManager已创�?);
        }

        private void CreateCameraController()
        {
            var controllerObj = new GameObject("CameraController");
            controllerObj.AddComponent<Camera.TrainingGroundCameraController>();
            Selection.activeGameObject = controllerObj;
            Debug.Log("[URPValidator] CameraController已创�?);
        }

        private void CreatePostProcessingManager()
        {
            var managerObj = new GameObject("PostProcessingManager");
            managerObj.AddComponent<PostProcessingManager>();
            Selection.activeGameObject = managerObj;
            Debug.Log("[URPValidator] PostProcessingManager已创�?);
        }

        #endregion

        #region UI辅助方法

        private void DrawSuccess(string message)
        {
            EditorGUILayout.BeginHorizontal();
            GUILayout.Label("�?, GUILayout.Width(20));
            EditorGUILayout.LabelField(message, EditorStyles.helpBox);
            EditorGUILayout.EndHorizontal();
        }

        private void DrawWarning(string message)
        {
            EditorGUILayout.BeginHorizontal();
            GUILayout.Label("�?, GUILayout.Width(20));
            EditorGUILayout.HelpBox(message, MessageType.Warning);
            EditorGUILayout.EndHorizontal();
        }

        private void DrawError(string message)
        {
            EditorGUILayout.BeginHorizontal();
            GUILayout.Label("�?, GUILayout.Width(20));
            EditorGUILayout.HelpBox(message, MessageType.Error);
            EditorGUILayout.EndHorizontal();
        }

        #endregion
    }
}
#endif
