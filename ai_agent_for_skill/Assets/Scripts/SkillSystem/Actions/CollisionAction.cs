using System;
using UnityEngine;
using Sirenix.OdinInspector;

namespace SkillSystem.Actions
{
    [Serializable]
    public class CollisionAction : ISkillAction
    {
        [SerializeField]
        [LabelText("Collision Shape")]
        public CollisionShape shape = CollisionShape.Sphere;

        [SerializeField]
        [LabelText("Position")]
        public Vector3 position = Vector3.zero;

        [SerializeField]
        [LabelText("Size")]
        public Vector3 size = Vector3.one;

        [SerializeField]
        [LabelText("Layer Mask")]
        public LayerMask layerMask = -1;

        [SerializeField]
        [LabelText("Damage")]
        [MinValue(0)]
        public float damage = 10f;

        public enum CollisionShape
        {
            Sphere,
            Box,
            Capsule
        }

        public override string GetActionName()
        {
            return "Collision Action";
        }

        public override void Execute()
        {
            Collider[] colliders = null;

            switch (shape)
            {
                case CollisionShape.Sphere:
                    colliders = Physics.OverlapSphere(position, size.x, layerMask);
                    break;
                case CollisionShape.Box:
                    colliders = Physics.OverlapBox(position, size * 0.5f, Quaternion.identity, layerMask);
                    break;
                case CollisionShape.Capsule:
                    colliders = Physics.OverlapCapsule(
                        position + Vector3.up * size.y * 0.5f,
                        position - Vector3.up * size.y * 0.5f,
                        size.x, layerMask);
                    break;
            }

            if (colliders != null)
            {
                foreach (var collider in colliders)
                {
                    Debug.Log($"Hit: {collider.name} with damage: {damage}");
                    // Here you could implement damage dealing logic
                }
            }
        }

    }
}