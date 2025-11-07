using UnityEngine;
using UnityEngine.InputSystem;

namespace TrainingGround.Entity
{
    /// <summary>
    /// 玩家角色移动控制器
    /// 使用CharacterController实现WASD八向移动，支持相机相对移动和Shift奔跑
    /// </summary>
    [RequireComponent(typeof(CharacterController))]
    public class PlayerMovementController : MonoBehaviour
    {
        [Header("移动速度配置")]
        [SerializeField] private float walkSpeed = 5f; // 行走速度
        [SerializeField] private float runSpeed = 10f; // 奔跑速度
        [SerializeField] private float rotationSpeed = 10f; // 转向平滑速度

        [Header("相机引用")]
        [SerializeField] private Transform cameraTransform; // 主相机Transform（用于计算相对移动）

        private CharacterController characterController;
        private Vector3 moveDirection; // 当前移动方向

        private void Awake()
        {
            characterController = GetComponent<CharacterController>();
        }

        private void Start()
        {
            // 如果没有手动设置相机引用，自动查找主相机
            if (cameraTransform == null)
            {
                UnityEngine.Camera mainCamera = UnityEngine.Camera.main;
                if (mainCamera != null)
                {
                    cameraTransform = mainCamera.transform;
                }
                else
                {
                    Debug.LogWarning("PlayerMovementController: 未找到主相机，移动方向将基于世界坐标");
                }
            }
        }

        private void Update()
        {
            HandleMovementInput();
        }

        /// <summary>
        /// 处理移动输入（WASD + Shift奔跑）
        /// </summary>
        private void HandleMovementInput()
        {
            // 检查键盘是否可用
            if (Keyboard.current == null) return;

            // 获取WASD输入（使用新 Input System）
            float horizontal = 0f;
            float vertical = 0f;

            if (Keyboard.current.wKey.isPressed) vertical += 1f;
            if (Keyboard.current.sKey.isPressed) vertical -= 1f;
            if (Keyboard.current.aKey.isPressed) horizontal -= 1f;
            if (Keyboard.current.dKey.isPressed) horizontal += 1f;

            // 计算移动向量（相机相对）
            Vector3 inputDirection = new Vector3(horizontal, 0f, vertical);

            // 如果有输入，计算移动方向
            if (inputDirection.magnitude > 0.1f)
            {
                // 基于相机朝向计算相对移动方向
                Vector3 cameraForward;
                Vector3 cameraRight;

                if (cameraTransform != null)
                {
                    // 获取相机的前向和右向（忽略Y轴倾斜，保持水平移动）
                    cameraForward = cameraTransform.forward;
                    cameraForward.y = 0f;
                    cameraForward.Normalize();

                    cameraRight = cameraTransform.right;
                    cameraRight.y = 0f;
                    cameraRight.Normalize();
                }
                else
                {
                    // 如果没有相机引用，使用世界坐标轴
                    cameraForward = Vector3.forward;
                    cameraRight = Vector3.right;
                }

                // 计算最终移动方向（相机前向 * 垂直输入 + 相机右向 * 水平输入）
                moveDirection = (cameraForward * vertical + cameraRight * horizontal).normalized;

                // 角色朝向移动方向（平滑旋转）
                if (moveDirection.magnitude > 0.1f)
                {
                    Quaternion targetRotation = Quaternion.LookRotation(moveDirection);
                    transform.rotation = Quaternion.Slerp(transform.rotation, targetRotation, rotationSpeed * Time.deltaTime);
                }

                // 检测是否按住Shift奔跑
                bool isRunning = Keyboard.current.leftShiftKey.isPressed || Keyboard.current.rightShiftKey.isPressed;
                float currentSpeed = isRunning ? runSpeed : walkSpeed;

                // 执行移动（CharacterController.Move）
                Vector3 movement = moveDirection * currentSpeed * Time.deltaTime;
                characterController.Move(movement);
            }
        }

        /// <summary>
        /// 设置相机引用（由TrainingGroundManager调用）
        /// </summary>
        public void SetCamera(Transform camera)
        {
            cameraTransform = camera;
        }

        /// <summary>
        /// 获取当前移动速度（用于动画系统）
        /// </summary>
        public float GetCurrentSpeed()
        {
            return characterController.velocity.magnitude;
        }

        /// <summary>
        /// 获取是否正在奔跑（用于动画系统）
        /// </summary>
        public bool IsRunning()
        {
            if (Keyboard.current == null) return false;
            return Keyboard.current.leftShiftKey.isPressed || Keyboard.current.rightShiftKey.isPressed;
        }

        /// <summary>
        /// 获取归一化的移动方向（用于动画系统）
        /// </summary>
        public Vector3 GetMoveDirection()
        {
            return moveDirection;
        }
    }
}
