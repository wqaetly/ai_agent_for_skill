using System.IO;
using UnityEngine;
using UnityEditor;
using Sirenix.OdinInspector;
using Sirenix.OdinInspector.Editor;
using Sirenix.Serialization;
using SerializationUtility = Sirenix.Serialization.SerializationUtility;

namespace OdinTestTemplate.Editor
{
    /// <summary>
    /// Odin序列化测试窗口
    /// 用于生成包含各种数据类型的Odin JSON测试样本
    /// </summary>
    public class OdinSerializationTestWindow : OdinEditorWindow
    {
        [MenuItem("Tools/Odin Test/Serialization Test Window")]
        private static void OpenWindow()
        {
            GetWindow<OdinSerializationTestWindow>("Odin序列化测试").Show();
        }
        
        [Title("Odin序列化测试数据")]
        [InfoBox("此工具用于生成包含各种数据类型的Odin JSON测试样本，帮助完善Python端的Odin解析器")]
        [HideLabel]
        [InlineEditor(ObjectFieldMode = InlineEditorObjectFieldModes.Hidden)]
        public OdinSerializationTestData testData = new OdinSerializationTestData();
        
        [Title("导出设置")]
        [FolderPath(AbsolutePath = true)]
        [LabelText("导出目录")]
        public string exportPath = "";
        
        [LabelText("文件名")]
        public string fileName = "odin_test_data.json";
        
        [LabelText("格式化输出")]
        public bool prettyPrint = true;
        
        protected override void OnEnable()
        {
            base.OnEnable();
            
            // 默认导出到项目根目录
            if (string.IsNullOrEmpty(exportPath))
            {
                exportPath = Path.Combine(Application.dataPath, "..", "OdinTestOutput");
            }
            
            // 初始化自引用测试数据
            InitializeSelfReferencingData();
        }
        
        private void InitializeSelfReferencingData()
        {
            if (testData.selfRef != null)
            {
                // 创建自引用结构
                testData.selfRef.child = new SelfReferencingClass { name = "Child1" };
                testData.selfRef.child.child = new SelfReferencingClass { name = "GrandChild" };
                testData.selfRef.children.Add(new SelfReferencingClass { name = "ListChild1" });
                testData.selfRef.children.Add(new SelfReferencingClass { name = "ListChild2" });
            }
        }
        
        [Button("导出为Odin JSON", ButtonSizes.Large)]
        [GUIColor(0.4f, 0.8f, 0.4f)]
        private void ExportToOdinJson()
        {
            if (string.IsNullOrEmpty(exportPath))
            {
                EditorUtility.DisplayDialog("错误", "请设置导出目录", "确定");
                return;
            }
            
            // 确保目录存在
            if (!Directory.Exists(exportPath))
            {
                Directory.CreateDirectory(exportPath);
            }
            
            string fullPath = Path.Combine(exportPath, fileName);
            
            // 使用Odin序列化
            byte[] bytes = SerializationUtility.SerializeValue(testData, DataFormat.JSON);
            string jsonContent = System.Text.Encoding.UTF8.GetString(bytes);
            
            File.WriteAllText(fullPath, jsonContent, System.Text.Encoding.UTF8);
            
            Debug.Log($"[OdinTest] 已导出到: {fullPath}");
            EditorUtility.DisplayDialog("成功", $"已导出到:\n{fullPath}", "确定");
            
            // 在资源管理器中显示
            EditorUtility.RevealInFinder(fullPath);
        }
        
        [Button("导出为标准JSON (对比用)", ButtonSizes.Medium)]
        private void ExportToStandardJson()
        {
            if (string.IsNullOrEmpty(exportPath))
            {
                EditorUtility.DisplayDialog("错误", "请设置导出目录", "确定");
                return;
            }
            
            if (!Directory.Exists(exportPath))
            {
                Directory.CreateDirectory(exportPath);
            }
            
            string standardFileName = Path.GetFileNameWithoutExtension(fileName) + "_standard.json";
            string fullPath = Path.Combine(exportPath, standardFileName);
            
            // 使用Unity的JsonUtility（标准JSON）
            string jsonContent = JsonUtility.ToJson(testData, prettyPrint);
            
            File.WriteAllText(fullPath, jsonContent, System.Text.Encoding.UTF8);
            
            Debug.Log($"[OdinTest] 标准JSON已导出到: {fullPath}");
            EditorUtility.DisplayDialog("成功", $"标准JSON已导出到:\n{fullPath}", "确定");
        }
        
        [Button("重置测试数据", ButtonSizes.Medium)]
        [GUIColor(0.8f, 0.6f, 0.4f)]
        private void ResetTestData()
        {
            testData = new OdinSerializationTestData();
            InitializeSelfReferencingData();
            Debug.Log("[OdinTest] 测试数据已重置");
        }
        
        [Button("复制JSON到剪贴板", ButtonSizes.Medium)]
        private void CopyJsonToClipboard()
        {
            byte[] bytes = SerializationUtility.SerializeValue(testData, DataFormat.JSON);
            string jsonContent = System.Text.Encoding.UTF8.GetString(bytes);

            GUIUtility.systemCopyBuffer = jsonContent;
            Debug.Log("[OdinTest] JSON已复制到剪贴板");
        }
    }
}
