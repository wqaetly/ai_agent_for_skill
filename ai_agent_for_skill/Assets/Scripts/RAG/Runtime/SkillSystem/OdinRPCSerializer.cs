using System;
using System.Text;
using UnityEngine;
using Sirenix.Serialization;
using SerializationUtility = Sirenix.Serialization.SerializationUtility;

namespace RAGSystem
{
    /// <summary>
    /// Odin RPC 序列化器
    /// 用于 RPC 通信的序列化，输出标准化的 JSON 格式（兼容标准 JSON 解析器）
    /// </summary>
    public static class OdinRPCSerializer
    {
        private static readonly DataFormat Format = DataFormat.JSON;

        /// <summary>
        /// 序列化对象为标准化的 JSON 字符串（用于网络传输）
        /// </summary>
        /// <typeparam name="T">要序列化的对象类型</typeparam>
        /// <param name="value">要序列化的对象</param>
        /// <param name="standardize">是否标准化 JSON（将 Unity 类型裸值转为键值对），默认为 true</param>
        /// <returns>JSON 字符串</returns>
        public static string Serialize<T>(T value, bool standardize = true)
        {
            if (value == null)
            {
                return "null";
            }

            try
            {
                // 使用 Odin 序列化
                byte[] bytes = SerializationUtility.SerializeValue(value, Format);
                string json = Encoding.UTF8.GetString(bytes);

                // 标准化 JSON（如果需要）
                if (standardize)
                {
                    json = OdinJsonStandardizer.Standardize(json);
                }

                return json;
            }
            catch (Exception e)
            {
                Debug.LogError($"[OdinRPCSerializer] Failed to serialize {typeof(T).Name}: {e.Message}\n{e.StackTrace}");
                return null;
            }
        }

        /// <summary>
        /// 反序列化 JSON 字符串为对象
        /// </summary>
        /// <typeparam name="T">目标对象类型</typeparam>
        /// <param name="json">JSON 字符串（支持标准 JSON 和 Odin JSON）</param>
        /// <returns>反序列化的对象</returns>
        public static T Deserialize<T>(string json)
        {
            if (string.IsNullOrEmpty(json))
            {
                Debug.LogWarning("[OdinRPCSerializer] Cannot deserialize null or empty JSON string");
                return default(T);
            }

            try
            {
                byte[] bytes = Encoding.UTF8.GetBytes(json);
                return SerializationUtility.DeserializeValue<T>(bytes, Format);
            }
            catch (Exception e)
            {
                Debug.LogError($"[OdinRPCSerializer] Failed to deserialize to {typeof(T).Name}: {e.Message}\n{e.StackTrace}");
                return default(T);
            }
        }

        /// <summary>
        /// 尝试反序列化 JSON 字符串
        /// </summary>
        /// <typeparam name="T">目标对象类型</typeparam>
        /// <param name="json">JSON 字符串</param>
        /// <param name="result">输出参数：反序列化结果</param>
        /// <returns>是否成功反序列化</returns>
        public static bool TryDeserialize<T>(string json, out T result)
        {
            try
            {
                result = Deserialize<T>(json);
                return result != null;
            }
            catch
            {
                result = default(T);
                return false;
            }
        }

        /// <summary>
        /// 序列化对象为字节数组（用于二进制传输）
        /// </summary>
        public static byte[] SerializeToBytes<T>(T value)
        {
            if (value == null)
            {
                return null;
            }

            try
            {
                return SerializationUtility.SerializeValue(value, DataFormat.Binary);
            }
            catch (Exception e)
            {
                Debug.LogError($"[OdinRPCSerializer] Failed to serialize {typeof(T).Name} to bytes: {e.Message}");
                return null;
            }
        }

        /// <summary>
        /// 从字节数组反序列化对象
        /// </summary>
        public static T DeserializeFromBytes<T>(byte[] bytes)
        {
            if (bytes == null || bytes.Length == 0)
            {
                Debug.LogWarning("[OdinRPCSerializer] Cannot deserialize null or empty bytes");
                return default(T);
            }

            try
            {
                return SerializationUtility.DeserializeValue<T>(bytes, DataFormat.Binary);
            }
            catch (Exception e)
            {
                Debug.LogError($"[OdinRPCSerializer] Failed to deserialize bytes to {typeof(T).Name}: {e.Message}");
                return default(T);
            }
        }

#if UNITY_EDITOR
        /// <summary>
        /// 测试序列化和反序列化（仅编辑器模式）
        /// </summary>
        [UnityEditor.MenuItem("Tools/Test Odin RPC Serializer")]
        public static void TestSerializer()
        {
            // 测试简单对象
            var testObj = new TestData
            {
                name = "Test Skill",
                value = 42,
                position = new Vector3(1.5f, 2.0f, 3.5f),
                rotation = Quaternion.identity
            };

            // 序列化
            string json = Serialize(testObj);
            Debug.Log("Serialized JSON:\n" + json);

            // 反序列化
            var deserialized = Deserialize<TestData>(json);
            if (deserialized != null)
            {
                Debug.Log($"Deserialized: {deserialized.name}, {deserialized.value}, {deserialized.position}");
            }

            // 测试字节序列化
            byte[] bytes = SerializeToBytes(testObj);
            Debug.Log($"Binary size: {bytes?.Length ?? 0} bytes");

            var fromBytes = DeserializeFromBytes<TestData>(bytes);
            if (fromBytes != null)
            {
                Debug.Log($"From bytes: {fromBytes.name}, {fromBytes.value}");
            }
        }

        [Serializable]
        private class TestData
        {
            public string name;
            public int value;
            public Vector3 position;
            public Quaternion rotation;
        }
#endif
    }
}
