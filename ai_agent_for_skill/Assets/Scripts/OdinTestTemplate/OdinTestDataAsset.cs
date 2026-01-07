using UnityEngine;
using Sirenix.OdinInspector;
using Sirenix.Serialization;

namespace OdinTestTemplate
{
    /// <summary>
    /// Odin序列化测试数据的ScriptableObject容器
    /// 可以在Unity中创建资产文件保存测试数据
    /// </summary>
    [CreateAssetMenu(fileName = "OdinTestData", menuName = "Odin Test/Test Data Asset")]
    public class OdinTestDataAsset : SerializedScriptableObject
    {
        [Title("Odin序列化测试数据")]
        [InfoBox("此资产包含各种数据类型用于测试Odin JSON序列化")]
        [HideLabel]
        public OdinSerializationTestData testData = new OdinSerializationTestData();
        
        [Button("初始化自引用数据", ButtonSizes.Medium)]
        private void InitializeSelfReferences()
        {
            if (testData.selfRef != null)
            {
                testData.selfRef.child = new SelfReferencingClass { name = "Child1" };
                testData.selfRef.child.child = new SelfReferencingClass { name = "GrandChild" };
                testData.selfRef.children.Clear();
                testData.selfRef.children.Add(new SelfReferencingClass { name = "ListChild1" });
                testData.selfRef.children.Add(new SelfReferencingClass { name = "ListChild2" });
            }
            Debug.Log("[OdinTestDataAsset] 自引用数据已初始化");
        }
        
        [Button("重置为默认值", ButtonSizes.Medium)]
        private void ResetToDefaults()
        {
            testData = new OdinSerializationTestData();
            InitializeSelfReferences();
            Debug.Log("[OdinTestDataAsset] 数据已重置为默认值");
        }
    }
}
