using System.IO;
using UnityEngine;
using Sirenix.Serialization;

namespace OdinTestTemplate
{
    /// <summary>
    /// Odin JSON序列化工具类
    /// 提供静态方法用于序列化测试数据
    /// </summary>
    public static class OdinJsonExporter
    {
        /// <summary>
        /// 将测试数据序列化为Odin JSON字符串
        /// </summary>
        public static string SerializeToJson(OdinSerializationTestData data, bool prettyPrint = true)
        {
            byte[] bytes = SerializationUtility.SerializeValue(data, DataFormat.JSON);
            string json = System.Text.Encoding.UTF8.GetString(bytes);
            
            // Odin的JSON序列化已经是格式化的，无需额外处理
            
            return json;
        }
        
        /// <summary>
        /// 将测试数据导出到文件
        /// </summary>
        public static void ExportToFile(OdinSerializationTestData data, string filePath, bool prettyPrint = true)
        {
            string json = SerializeToJson(data, prettyPrint);
            
            string directory = Path.GetDirectoryName(filePath);
            if (!string.IsNullOrEmpty(directory) && !Directory.Exists(directory))
            {
                Directory.CreateDirectory(directory);
            }
            
            File.WriteAllText(filePath, json, System.Text.Encoding.UTF8);
            Debug.Log($"[OdinJsonExporter] Exported to: {filePath}");
        }
        
        /// <summary>
        /// 创建带有完整自引用数据的测试实例
        /// </summary>
        public static OdinSerializationTestData CreateFullTestData()
        {
            var data = new OdinSerializationTestData();
            
            // 初始化自引用结构
            if (data.selfRef != null)
            {
                data.selfRef.child = new SelfReferencingClass { name = "Child1" };
                data.selfRef.child.child = new SelfReferencingClass { name = "GrandChild" };
                data.selfRef.children.Add(new SelfReferencingClass { name = "ListChild1" });
                data.selfRef.children.Add(new SelfReferencingClass { name = "ListChild2" });
            }
            
            return data;
        }
        
        /// <summary>
        /// 快速导出默认测试数据到指定路径
        /// </summary>
        public static void QuickExport(string filePath)
        {
            var data = CreateFullTestData();
            ExportToFile(data, filePath);
        }
    }
}
