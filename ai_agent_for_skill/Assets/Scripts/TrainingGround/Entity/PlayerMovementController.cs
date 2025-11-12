using UnityEngine;
using UnityEngine.InputSystem;

namespace TrainingGround.Entity
{
    /// <summary>
    /// 玩家角色移动控制器
    /// 纯Transform控制的WASD八向移动，支持相机相对移动和Shift奔跑
    /// </summary>
    public class PlayerMovementController : MonoBehaviour
    {
        [Header("移动速度配置")]
        [SerializeField] private float walkSpeed = 5f; // 行走速度
        [SerializeField] private float runSpeed = 10f; // 奔跑速度
        [SerializeField] private float rotationSpeed = 10f; // 转向平滑速度

        [Header("相机引用")]
        [SerializeField] private Transform cameraTransform; // 主相机Transform（用于计算相对移动）

        private Vector3 moveDirection; // 当前移动方向
        private Vector3 currentVelocity; // 当前速度（用于外部查询）
        private bool isMovementEnabled = true; // 移动是否启用（技能期间可能禁用）

        private void Start()
        {
            // 检查并移除CharacterController（已废弃，改用纯Transform控制）
            var cc = GetComponent<CharacterController>();
            if (cc != null)
            {
                Debug.LogWarning("[PlayerMovementController] 检测到CharacterController组件，已自动移除。现在使用纯Transform控制。");
                Destroy(cc);
            }

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

            Debug.Log($"[PlayerMovementController] 初始化完成 - isMovementEnabled: {isMovementEnabled}");
        }

        private void LateUpdate()
        {
            if (isMovementEnabled)
            {
                HandleMovementInput();
            }
            else
            {
                currentVelocity = Vector3.zero;
            }
        }

        /// <summary>
        /// 处理移动输入（WASD + Shift奔跑）
        /// </summary>
        private void HandleMovementInput()
        {
            // 检查键盘是否可用
            if (Keyboard.current == null)
            {
                currentVelocity = Vector3.zero;
                Debug.LogWarning("[PlayerMovementController] Keyboard.current is null!");
                return;
            }

            // 获取WASD输入（使用新 Input System）
            float horizontal = 0f;
            float vertical = 0f;

            if (Keyboard.current.wKey.isPressed) vertical += 1f;
            if (Keyboard.current.sKey.isPressed) vertical -= 1f;
            if (Keyboard.current.aKey.isPressed) horizontal -= 1f;
            if (Keyboard.current.dKey.isPressed) horizontal += 1f;

            // 计算移动向量（相机相对）
            Vector3 inputDirection = new Vector3(horizontal, 0f, vertical);

            // 调试日志（仅在有输入时打印）
            if (inputDirection.magnitude > 0.01f)
            {
                Debug.Log($"[PlayerMovementController] Input: H={horizontal}, V={vertical}, Enabled={isMovementEnabled}");
            }

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

                // 执行移动（直接修改Transform.position）
                Vector3 oldPos = transform.position;
                Vector3 movement = moveDirection * currentSpeed * Time.deltaTime;
                transform.position += movement;
                Vector3 newPos = transform.position;

                // 调试：检查位置是否真的变化了
                if ((newPos - oldPos).magnitude < 0.001f && movement.magnitude > 0.001f)
                {
                    Debug.LogWarning($"[PlayerMovementController] 位置未改变！可能被其他组件阻止。Movement={movement.magnitude}");
                }

                // 记录速度
                currentVelocity = moveDirection * currentSpeed;
            }
            else
            {
                currentVelocity = Vector3.zero;
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
            return currentVelocity.magnitude;
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

        /// <summary>
        /// 启用/禁用移动控制（技能系统调用）
        /// </summary>
        public void SetMovementEnabled(bool enabled)
        {
            isMovementEnabled = enabled;
        }

        /// <summary>
        /// 获取移动是否启用
        /// </summary>
        public bool IsMovementEnabled()
        {
            return isMovementEnabled;
        }
    }
}
