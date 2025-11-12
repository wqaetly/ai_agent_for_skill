using UnityEngine;
using Unity.Cinemachine;
using Unity.Cinemachine.TargetTracking;

namespace TrainingGround.Camera
{
    /// <summary>
    /// 相机视角模式
    /// </summary>
    public enum CameraViewMode
    {
        ThirdPerson,  // 第三人称跟随
        TopDown       // LOL风格俯视�?
    }

    /// <summary>
    /// 训练场专业相机控制器 - 基于Cinemachine
    /// 提供第三人称跟随、LOL风格俯视角、动态镜头切换、震屏等商业级功�?
    /// </summary>
    public class TrainingGroundCameraController : MonoBehaviour
    {
        [Header("相机目标")]
        [SerializeField] private Transform followTarget;
        [SerializeField] private Transform lookAtTarget;

        [Header("Cinemachine虚拟相机")]
        [SerializeField] private CinemachineCamera mainVirtualCamera;
        [SerializeField] private CinemachineCamera skillCastCamera;

        [Header("视角模式")]
        [SerializeField] private CameraViewMode viewMode = CameraViewMode.TopDown;

        [Header("第三人称跟随设置")]
        [SerializeField] private Vector3 thirdPersonOffset = new Vector3(0f, 3f, -6f);
        [SerializeField] private float thirdPersonFOV = 60f;

        [Header("俯视角设置（LOL风格�?)]
        [SerializeField] private Vector3 topDownOffset = new Vector3(0f, 15f, -8f);
        [SerializeField] private float topDownFOV = 50f;
        [SerializeField] private float topDownAngle = 45f; // 俯视角度

        [Header("通用设置")]
        [SerializeField] private float followDamping = 1f;

        [Header("观察设置")]
        [SerializeField] private Vector3 lookAtOffset = new Vector3(0f, 1.5f, 0f);
        [SerializeField] private float lookAtDamping = 1f;

        [Header("技能释放镜�?)]
        [SerializeField] private bool enableSkillCamera = true;
        [SerializeField] private Vector3 skillCameraOffset = new Vector3(2f, 2f, -4f);
        [SerializeField] private float skillCameraFOV = 45f;
        [SerializeField] private float normalCameraFOV = 60f;

        [Header("震屏设置")]
        [SerializeField] private CinemachineImpulseSource impulseSource;
        [SerializeField] private float defaultShakeForce = 1f;

        // 组件引用
        private CinemachineFollow followComponent;
        private CinemachineRotationComposer rotationComposer;
        private UnityEngine.Camera mainCamera;

        // 状�?
        private bool isInSkillMode = false;

        void Awake()
        {
            // 获取主相�?
            mainCamera = UnityEngine.Camera.main;
            if (mainCamera == null)
            {
                mainCamera = FindFirstObjectByType<UnityEngine.Camera>();
            }

            // 确保主相机有CinemachineBrain
            if (mainCamera != null && mainCamera.GetComponent<CinemachineBrain>() == null)
            {
                mainCamera.gameObject.AddComponent<CinemachineBrain>();
            }

            // 创建虚拟相机（如果不存在�?
            if (mainVirtualCamera == null)
            {
                CreateMainVirtualCamera();
            }

            // 设置Impulse Source
            if (impulseSource == null)
            {
                impulseSource = gameObject.GetComponent<CinemachineImpulseSource>();
                if (impulseSource == null)
                {
                    impulseSource = gameObject.AddComponent<CinemachineImpulseSource>();
                }
            }

            // 配置组件
            ConfigureVirtualCamera();
        }

        void Start()
        {
            // 自动查找玩家 - 添加空值检�?
            if (followTarget == null)
            {
                GameObject player = GameObject.FindGameObjectWithTag("Player");
                if (player != null && player.transform != null)
                {
                    SetFollowTarget(player.transform);
                }
                else
                {
                    Debug.LogWarning("[CameraController] No Player object found with valid transform");
                }
            }
        }

        /// <summary>
        /// 设置跟随目标
        /// </summary>
        public void SetFollowTarget(Transform target)
        {
            // 添加空值检�?
            if (target == null)
            {
                Debug.LogWarning("[CameraController] Cannot set null follow target");
                return;
            }

            followTarget = target;
            lookAtTarget = target;

            if (mainVirtualCamera != null)
            {
                mainVirtualCamera.Follow = followTarget;
                mainVirtualCamera.LookAt = lookAtTarget;
            }

            Debug.Log($"[CameraController] Follow target set to: {target.name}");
        }

        /// <summary>
        /// 创建主虚拟相�?
        /// </summary>
        private void CreateMainVirtualCamera()
        {
            GameObject vcamObj = new GameObject("CM_MainVirtualCamera");
            vcamObj.transform.SetParent(transform);
            mainVirtualCamera = vcamObj.AddComponent<CinemachineCamera>();
            mainVirtualCamera.Priority.Value = 10;

            Debug.Log("[CameraController] Main virtual camera created");
        }

        /// <summary>
        /// 配置虚拟相机组件
        /// </summary>
        private void ConfigureVirtualCamera()
        {
            if (mainVirtualCamera == null) return;

            // 设置目标
            mainVirtualCamera.Follow = followTarget;
            mainVirtualCamera.LookAt = lookAtTarget;

            // 根据视角模式配置相机
            Vector3 currentOffset;
            float currentFOV;

            if (viewMode == CameraViewMode.TopDown)
            {
                currentOffset = topDownOffset;
                currentFOV = topDownFOV;
            }
            else
            {
                currentOffset = thirdPersonOffset;
                currentFOV = thirdPersonFOV;
            }

            // 配置Follow组件
            var followComponent = mainVirtualCamera.GetComponent<CinemachineFollow>();
            if (followComponent == null)
            {
                followComponent = mainVirtualCamera.gameObject.AddComponent<CinemachineFollow>();
            }
            followComponent.FollowOffset = currentOffset;

            // 禁用位置阻尼，移除相机拖尾效�?
            followComponent.TrackerSettings = new TrackerSettings
            {
                BindingMode = BindingMode.WorldSpace,
                PositionDamping = Vector3.zero,  // 设为 0 = 无阻�?
                AngularDampingMode = AngularDampingMode.Euler,
                RotationDamping = Vector3.zero,
                QuaternionDamping = 0
            };

            // 配置旋转组件（观察目标）
            var rotationComposer = mainVirtualCamera.GetComponent<CinemachineRotationComposer>();
            if (rotationComposer == null)
            {
                rotationComposer = mainVirtualCamera.gameObject.AddComponent<CinemachineRotationComposer>();
            }

            // 禁用旋转阻尼，移除相机旋转延�?
            rotationComposer.Damping = Vector2.zero;  // 设为 0 = 无阻�?

            // 设置Lens参数
            var lens = mainVirtualCamera.Lens;
            lens.FieldOfView = currentFOV;
            mainVirtualCamera.Lens = lens;

            Debug.Log($"[CameraController] Virtual camera configured - Mode: {viewMode}");
        }

        /// <summary>
        /// 触发震屏效果
        /// </summary>
        /// <param name="force">震动强度 (0-2)</param>
        /// <param name="duration">持续时间（秒�?/param>
        public void TriggerCameraShake(float force = -1f, float duration = 0.2f)
        {
            if (impulseSource == null) return;

            float actualForce = force > 0 ? force : defaultShakeForce;

            // 触发Impulse
            impulseSource.GenerateImpulse(actualForce);

            Debug.Log($"[CameraController] Camera shake triggered: force={actualForce}, duration={duration}");
        }

        /// <summary>
        /// 切换到技能释放镜�?
        /// </summary>
        public void SwitchToSkillCamera()
        {
            if (!enableSkillCamera || mainVirtualCamera == null) return;

            isInSkillMode = true;

            // 调整FOV
            var lens = mainVirtualCamera.Lens;
            lens.FieldOfView = skillCameraFOV;
            mainVirtualCamera.Lens = lens;

            // 调整跟随偏移
            var followComponent = mainVirtualCamera.GetComponent<CinemachineFollow>();
            if (followComponent != null)
            {
                followComponent.FollowOffset = skillCameraOffset;
            }

            Debug.Log("[CameraController] Switched to skill camera mode");
        }

        /// <summary>
        /// 切换回普通镜�?
        /// </summary>
        public void SwitchToNormalCamera()
        {
            if (!isInSkillMode || mainVirtualCamera == null) return;

            isInSkillMode = false;

            // 恢复FOV
            var lens = mainVirtualCamera.Lens;
            lens.FieldOfView = normalCameraFOV;
            mainVirtualCamera.Lens = lens;

            // 恢复跟随偏移 - 使用正确的偏移量
            var followComponent = mainVirtualCamera.GetComponent<CinemachineFollow>();
            if (followComponent != null)
            {
                Vector3 normalOffset = viewMode == CameraViewMode.TopDown ? topDownOffset : thirdPersonOffset;
                followComponent.FollowOffset = normalOffset;
            }

            Debug.Log("[CameraController] Switched to normal camera mode");
        }

        /// <summary>
        /// 平滑缩放相机FOV
        /// </summary>
        public void ZoomCamera(float targetFOV, float duration = 0.5f)
        {
            if (mainVirtualCamera == null) return;

            StartCoroutine(ZoomCameraCoroutine(targetFOV, duration));
        }

        private System.Collections.IEnumerator ZoomCameraCoroutine(float targetFOV, float duration)
        {
            float elapsed = 0f;
            var lens = mainVirtualCamera.Lens;
            float startFOV = lens.FieldOfView;

            while (elapsed < duration)
            {
                elapsed += Time.deltaTime;
                float t = elapsed / duration;

                lens.FieldOfView = Mathf.Lerp(startFOV, targetFOV, t);
                mainVirtualCamera.Lens = lens;

                yield return null;
            }

            lens.FieldOfView = targetFOV;
            mainVirtualCamera.Lens = lens;
        }

        /// <summary>
        /// 切换视角模式
        /// </summary>
        public void SwitchViewMode(CameraViewMode newMode)
        {
            if (viewMode == newMode) return;

            viewMode = newMode;
            ConfigureVirtualCamera();

            Debug.Log($"[CameraController] Switched to view mode: {viewMode}");
        }

        /// <summary>
        /// 切换到俯视角模式
        /// </summary>
        public void SwitchToTopDownView()
        {
            SwitchViewMode(CameraViewMode.TopDown);
        }

        /// <summary>
        /// 切换到第三人称模�?
        /// </summary>
        public void SwitchToThirdPersonView()
        {
            SwitchViewMode(CameraViewMode.ThirdPerson);
        }

        /// <summary>
        /// 设置相机跟随偏移
        /// </summary>
        public void SetFollowOffset(Vector3 offset, float transitionTime = 1f)
        {
            if (viewMode == CameraViewMode.TopDown)
            {
                topDownOffset = offset;
            }
            else
            {
                thirdPersonOffset = offset;
            }

            var followComponent = mainVirtualCamera?.GetComponent<CinemachineFollow>();
            if (followComponent != null)
            {
                followComponent.FollowOffset = offset;
            }
        }

        /// <summary>
        /// 设置观察偏移
        /// </summary>
        public void SetLookAtOffset(Vector3 offset)
        {
            lookAtOffset = offset;

            var rotationComposer = mainVirtualCamera?.GetComponent<CinemachineRotationComposer>();
            if (rotationComposer != null)
            {
                // rotationComposer.TrackedObjectOffset = offset; // 暂时注释，需要检查正确的API
            }
        }

        #region 公共访问�?

        public Transform FollowTarget => followTarget;
        public bool IsInSkillMode => isInSkillMode;
        public CinemachineCamera MainVirtualCamera => mainVirtualCamera;
        public CameraViewMode ViewMode => viewMode;

        #endregion

        #region Editor工具

#if UNITY_EDITOR
        [ContextMenu("Auto Setup Camera")]
        private void AutoSetupCamera()
        {
            // 查找玩家
            GameObject player = GameObject.FindGameObjectWithTag("Player");
            if (player != null)
            {
                SetFollowTarget(player.transform);
            }

            // 配置相机
            ConfigureVirtualCamera();

            Debug.Log("[CameraController] Auto setup completed");
        }
#endif

        #endregion
    }
}
