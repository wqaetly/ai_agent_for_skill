using UnityEngine;
using System.Collections.Generic;
using SkillSystem.Actions;
using TrainingGround.Entity;

namespace TrainingGround.Visualizer
{
    /// <summary>
    /// 移动可视化器 - 显示位移、冲刺、传送等移动效果
    /// </summary>
    public class MovementVisualizer : SkillVisualizerBase<MovementAction>
    {
        private Dictionary<MovementAction, Vector3> startPositions = new Dictionary<MovementAction, Vector3>();

        protected override void OnVisualizeEnter(MovementAction action, GameObject caster)
        {
            Debug.Log($"[MovementVisualizer] Visualizing movement from {caster.name}");

            // 记录起始位置
            startPositions[action] = caster.transform.position;

            // 创建轨迹预测�?
            CreateTrajectoryLine(action, caster);
        }

        protected override void OnVisualizeTick(MovementAction action, GameObject caster, int relativeFrame)
        {
            // 执行移动
            ExecuteMovement(action, caster, relativeFrame);
        }

        protected override void OnVisualizeExit(MovementAction action, GameObject caster)
        {
            // 清理起始位置记录
            startPositions.Remove(action);
        }

        private void CreateTrajectoryLine(MovementAction action, GameObject caster)
        {
            // 创建虚线轨迹
            Vector3 startPos = caster.transform.position;
            Vector3 endPos = CalculateEndPosition(action, caster);

            // 使用LineRenderer绘制轨迹
            GameObject lineObject = new GameObject("MovementTrajectory");
            lineObject.transform.position = Vector3.zero;

            var lineRenderer = lineObject.AddComponent<LineRenderer>();
            lineRenderer.positionCount = 2;
            lineRenderer.SetPosition(0, startPos);
            lineRenderer.SetPosition(1, endPos);
            lineRenderer.startWidth = 0.1f;
            lineRenderer.endWidth = 0.1f;

            var material = new Material(Shader.Find("Sprites/Default"));
            material.color = new Color(0f, 1f, 1f, 0.5f); // 青色半透明
            lineRenderer.material = material;

            // 1秒后销�?
            Object.Destroy(lineObject, 1f);
        }

        private Vector3 CalculateEndPosition(MovementAction action, GameObject caster)
        {
            Vector3 endPosition = caster.transform.position;

            switch (action.movementType)
            {
                case MovementType.Dash:
                case MovementType.Teleport:
                    // 向前移动
                    endPosition = caster.transform.position + caster.transform.forward * action.distance;
                    break;

                case MovementType.TowardsTarget:
                    // 朝向目标
                    var playerCharacter = caster.GetComponent<PlayerCharacter>();
                    var target = playerCharacter?.GetCurrentTarget();
                    if (target != null)
                    {
                        Vector3 direction = (target.GetPosition() - caster.transform.position).normalized;
                        endPosition = caster.transform.position + direction * action.distance;
                    }
                    else
                    {
                        endPosition = caster.transform.position + caster.transform.forward * action.distance;
                    }
                    break;

                case MovementType.Knockback:
                    // 击退（向后）
                    endPosition = caster.transform.position - caster.transform.forward * action.distance;
                    break;
            }

            return endPosition;
        }

        private void ExecuteMovement(MovementAction action, GameObject caster, int relativeFrame)
        {
            // 获取起始位置
            if (!startPositions.TryGetValue(action, out Vector3 startPos))
            {
                startPos = caster.transform.position;
            }

            // 计算目标位置
            Vector3 endPos = CalculateEndPosition(action, caster);

            // 计算移动进度
            float totalDuration = action.duration / 30f; // 假设30FPS
            float currentTime = relativeFrame / 30f;
            float t = Mathf.Clamp01(currentTime / totalDuration);

            // 根据移动类型选择插值方�?
            Vector3 newPosition;
            switch (action.movementType)
            {
                case MovementType.Dash:
                    // 快速移动（EaseOut�?
                    newPosition = Vector3.Lerp(startPos, endPos, EaseOut(t));
                    break;

                case MovementType.Teleport:
                    // 瞬移（第一帧直接到达）
                    newPosition = relativeFrame == 0 ? endPos : caster.transform.position;
                    break;

                case MovementType.TowardsTarget:
                case MovementType.Knockback:
                    // 线性移�?
                    newPosition = Vector3.Lerp(startPos, endPos, t);
                    break;

                default:
                    newPosition = caster.transform.position;
                    break;
            }

            // 应用移动
            var entity = caster.GetComponent<IEntity>();
            if (entity != null)
            {
                entity.SetPosition(newPosition);
            }
            else
            {
                caster.transform.position = newPosition;
            }

            // 创建残影效果（Dash时）
            if (action.movementType == MovementType.Dash && relativeFrame % 3 == 0)
            {
                CreateAfterimage(caster);
            }
        }

        private void CreateAfterimage(GameObject caster)
        {
            // 创建简单的残影（半透明克隆�?
            var renderers = caster.GetComponentsInChildren<Renderer>();
            foreach (var renderer in renderers)
            {
                GameObject afterimage = GameObject.CreatePrimitive(PrimitiveType.Cube);
                afterimage.name = "Afterimage";
                afterimage.transform.position = renderer.transform.position;
                afterimage.transform.rotation = renderer.transform.rotation;
                afterimage.transform.localScale = renderer.transform.lossyScale;

                // 移除碰撞�?
                Object.Destroy(afterimage.GetComponent<Collider>());

                // 设置半透明材质
                var afterimageRenderer = afterimage.GetComponent<Renderer>();
                if (afterimageRenderer != null)
                {
                    var material = new Material(Shader.Find("Standard"));
                    material.color = new Color(0.5f, 0.5f, 1f, 0.3f);
                    material.SetFloat("_Mode", 3); // Transparent
                    material.SetInt("_SrcBlend", (int)UnityEngine.Rendering.BlendMode.SrcAlpha);
                    material.SetInt("_DstBlend", (int)UnityEngine.Rendering.BlendMode.OneMinusSrcAlpha);
                    material.SetInt("_ZWrite", 0);
                    material.DisableKeyword("_ALPHATEST_ON");
                    material.EnableKeyword("_ALPHABLEND_ON");
                    material.DisableKeyword("_ALPHAPREMULTIPLY_ON");
                    material.renderQueue = 3000;
                    afterimageRenderer.material = material;
                }

                // 0.5秒后销�?
                Object.Destroy(afterimage, 0.5f);
            }
        }

        private float EaseOut(float t)
        {
            return 1f - Mathf.Pow(1f - t, 3f);
        }
    }
}
