using UnityEngine;
using Unity.Cinemachine;
using SkillSystem.Actions;
using System.Collections;

namespace TrainingGround.Visualizer
{
    /// <summary>
    /// 镜头效果可视化器 - 实现CameraAction的镜头效�?
    /// 使用Cinemachine Impulse实现专业的震屏效�?
    /// </summary>
    public class CameraActionVisualizer : SkillVisualizerBase<CameraAction>
    {
        private CinemachineImpulseSource impulseSource;
        private Camera.TrainingGroundCameraController cameraController;

        // 当前效果状�?
        private struct CameraEffectState
        {
            public Vector3 originalPosition;
            public Quaternion originalRotation;
            public float originalFOV;
            public bool isActive;
        }

        private CameraEffectState currentState;

        void Awake()
        {
            // 获取或创建Impulse Source
            impulseSource = GetComponent<CinemachineImpulseSource>();
            if (impulseSource == null)
            {
                impulseSource = gameObject.AddComponent<CinemachineImpulseSource>();
                ConfigureImpulseSource();
            }

            // 查找相机控制�?
            cameraController = FindObjectOfType<Camera.TrainingGroundCameraController>();
        }

        private void ConfigureImpulseSource()
        {
            // 配置默认的Impulse参数
            impulseSource.ImpulseDefinition.ImpulseDuration = 0.2f;
            impulseSource.ImpulseDefinition.ImpulseShape = CinemachineImpulseDefinition.ImpulseShapes.Rumble;

            // 设置衰减
            impulseSource.ImpulseDefinition.TimeEnvelope.AttackTime = 0.05f;
            impulseSource.ImpulseDefinition.TimeEnvelope.SustainTime = 0.1f;
            impulseSource.ImpulseDefinition.TimeEnvelope.DecayTime = 0.05f;
        }

        protected override void OnVisualizeEnter(CameraAction action, GameObject caster)
        {
            Debug.Log($"[CameraActionVisualizer] Applying camera effects from {caster.name}");

            // 保存当前相机状�?
            SaveCameraState();

            // 应用震屏效果
            if (action.shakeIntensity > 0)
            {
                ApplyShakeEffect(action);
            }

            // 应用缩放效果
            if (Mathf.Abs(action.zoomScale - 1f) > 0.01f)
            {
                ApplyZoomEffect(action);
            }

            // 应用位移效果
            if (action.positionOffset != Vector3.zero)
            {
                ApplyPositionOffset(action);
            }

            // 应用旋转效果
            if (action.rotationOffset != Vector3.zero)
            {
                ApplyRotationOffset(action);
            }
        }

        protected override void OnVisualizeTick(CameraAction action, GameObject caster, int relativeFrame)
        {
            // 镜头效果在Tick中持续更�?
            // 大部分效果由Cinemachine自动处理，这里可以添加自定义的持续效�?
        }

        protected override void OnVisualizeExit(CameraAction action, GameObject caster)
        {
            // 恢复相机状态（带渐出效果）
            RestoreCameraState(action.fadeOutTime);

            Debug.Log("[CameraActionVisualizer] Camera effects ended");
        }

        /// <summary>
        /// 应用震屏效果 - 使用Cinemachine Impulse
        /// </summary>
        private void ApplyShakeEffect(CameraAction action)
        {
            if (impulseSource == null) return;

            // 配置震屏参数
            impulseSource.ImpulseDefinition.ImpulseDuration = action.duration / 60f; // 转换帧到�?

            // 根据强度生成Impulse
            Vector3 velocity = Random.insideUnitSphere * action.shakeIntensity;
            impulseSource.GenerateImpulse(velocity);

            Debug.Log($"[CameraActionVisualizer] Shake applied: intensity={action.shakeIntensity}, duration={action.duration}");
        }

        /// <summary>
        /// 应用缩放效果
        /// </summary>
        private void ApplyZoomEffect(CameraAction action)
        {
            if (cameraController == null || cameraController.MainVirtualCamera == null) return;

            // 计算目标FOV
            // float currentFOV = cameraController.MainVirtualCamera.Lens.FieldOfView;
            // float targetFOV = currentFOV / action.zoomScale;

            // 平滑过渡到目标FOV（已禁用，避免晕眩）
            // cameraController.ZoomCamera(targetFOV, action.fadeInTime);

            Debug.Log($"[CameraActionVisualizer] Zoom effect disabled to prevent motion sickness");
        }

        /// <summary>
        /// 应用位移偏移
        /// </summary>
        private void ApplyPositionOffset(CameraAction action)
        {
            if (cameraController == null || cameraController.MainVirtualCamera == null) return;

            var followComponent = cameraController.MainVirtualCamera.GetComponent<CinemachineFollow>();
            if (followComponent != null)
            {
                Vector3 newOffset = followComponent.FollowOffset + action.positionOffset;
                cameraController.SetFollowOffset(newOffset, action.fadeInTime);
            }

            Debug.Log($"[CameraActionVisualizer] Position offset applied: {action.positionOffset}");
        }

        /// <summary>
        /// 应用旋转偏移
        /// </summary>
        private void ApplyRotationOffset(CameraAction action)
        {
            if (cameraController == null || cameraController.MainVirtualCamera == null) return;

            var rotationComposer = cameraController.MainVirtualCamera.GetComponent<CinemachineRotationComposer>();
            if (rotationComposer != null)
            {
                // 旋转偏移通过TrackedObjectOffset实现
                // Vector3 newOffset = rotationComposer.TrackedObjectOffset + action.rotationOffset; // 暂时注释
              Vector3 newOffset = Vector3.zero + action.rotationOffset;
                cameraController.SetLookAtOffset(newOffset);
            }

            Debug.Log($"[CameraActionVisualizer] Rotation offset applied: {action.rotationOffset}");
        }

        /// <summary>
        /// 保存当前相机状�?
        /// </summary>
        private void SaveCameraState()
        {
            if (cameraController == null || cameraController.MainVirtualCamera == null)
            {
                currentState.isActive = false;
                return;
            }

            var vcam = cameraController.MainVirtualCamera;
            var followComponent = vcam.GetComponent<CinemachineFollow>();

            if (followComponent != null)
            {
                currentState.originalPosition = followComponent.FollowOffset;
            }

            currentState.originalFOV = vcam.Lens.FieldOfView;
            currentState.isActive = true;

            Debug.Log("[CameraActionVisualizer] Camera state saved");
        }

        /// <summary>
        /// 恢复相机状�?
        /// </summary>
        private void RestoreCameraState(float fadeOutTime)
        {
            if (!currentState.isActive) return;

            if (cameraController != null && cameraController.MainVirtualCamera != null)
            {
                // 恢复FOV（已禁用�?
                // cameraController.ZoomCamera(currentState.originalFOV, fadeOutTime);

                // 恢复位移偏移
                cameraController.SetFollowOffset(currentState.originalPosition, fadeOutTime);
            }

            currentState.isActive = false;

            Debug.Log("[CameraActionVisualizer] Camera state restored");
        }

        public override void Cleanup()
        {
            // 确保清理时恢复相机状�?
            if (currentState.isActive)
            {
                RestoreCameraState(0.2f);
            }
        }

        #region 公共接口 - 提供给技能系统调�?

        /// <summary>
        /// 快速触发震屏效果（不依赖CameraAction�?
        /// </summary>
        public void QuickShake(float intensity = 1f)
        {
            if (impulseSource != null)
            {
                Vector3 velocity = Random.insideUnitSphere * intensity;
                impulseSource.GenerateImpulse(velocity);
            }
        }

        /// <summary>
        /// 快速缩放（不依赖CameraAction�?
        /// </summary>
        public void QuickZoom(float scale, float duration = 0.5f)
        {
            // FOV 变化已禁用，避免晕眩
            // if (cameraController != null && cameraController.MainVirtualCamera != null)
            // {
            //     float currentFOV = cameraController.MainVirtualCamera.Lens.FieldOfView;
            //     float targetFOV = currentFOV / scale;
            //     cameraController.ZoomCamera(targetFOV, duration);
            // }
            Debug.Log("[CameraActionVisualizer] QuickZoom disabled");
        }

        #endregion
    }
}
