using System.Text.RegularExpressions;
using UnityEngine;

namespace RAGSystem
{
    /// <summary>
    /// Odin JSON 标准化器
    /// 将 Odin 序列化的 Unity 类型裸值转换为标准键值对格式，以便标准 JSON 解析器处理
    /// </summary>
    public static class OdinJsonStandardizer
    {
        /// <summary>
        /// 标准化 Odin JSON 字符串，使其兼容标准 JSON 解析器
        /// </summary>
        /// <param name="odinJson">Odin 序列化的 JSON 字符串</param>
        /// <returns>标准化后的 JSON 字符串</returns>
        public static string Standardize(string odinJson)
        {
            if (string.IsNullOrEmpty(odinJson))
            {
                return odinJson;
            }

            string result = odinJson;

            // 处理 Vector3 裸值
            result = StandardizeVector3(result);

            // 处理 Vector2 裸值
            result = StandardizeVector2(result);

            // 处理 Quaternion 裸值
            result = StandardizeQuaternion(result);

            // 处理 Color 裸值
            result = StandardizeColor(result);

            // 处理 Vector4 裸值
            result = StandardizeVector4(result);

            return result;
        }

        /// <summary>
        /// 标准化 Vector3 类型
        /// 从: {"$type":"...Vector3...", x, y, z}
        /// 到: {"$type":"...Vector3...", "x":x, "y":y, "z":z}
        /// </summary>
        private static string StandardizeVector3(string json)
        {
            // 匹配模式：
            // "$type": "...Vector3..." 后跟三个数值（可能包含空格、换行）
            // 数值可以是整数或浮点数（包括负数和科学计数法）
            var pattern = @"(\""?\$type\""?\s*:\s*\""[^\""]*Vector3[^\""]*\""\s*,)\s*" +
                         @"(-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)\s*,\s*" +
                         @"(-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)\s*,\s*" +
                         @"(-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)";

            var replacement = @"$1 ""x"":$2, ""y"":$3, ""z"":$4";

            return Regex.Replace(json, pattern, replacement, RegexOptions.Multiline);
        }

        /// <summary>
        /// 标准化 Vector2 类型
        /// </summary>
        private static string StandardizeVector2(string json)
        {
            var pattern = @"(\""?\$type\""?\s*:\s*\""[^\""]*Vector2[^\""]*\""\s*,)\s*" +
                         @"(-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)\s*,\s*" +
                         @"(-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)";

            var replacement = @"$1 ""x"":$2, ""y"":$3";

            return Regex.Replace(json, pattern, replacement, RegexOptions.Multiline);
        }

        /// <summary>
        /// 标准化 Quaternion 类型
        /// 从: {"$type":"...Quaternion...", x, y, z, w}
        /// 到: {"$type":"...Quaternion...", "x":x, "y":y, "z":z, "w":w}
        /// </summary>
        private static string StandardizeQuaternion(string json)
        {
            var pattern = @"(\""?\$type\""?\s*:\s*\""[^\""]*Quaternion[^\""]*\""\s*,)\s*" +
                         @"(-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)\s*,\s*" +
                         @"(-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)\s*,\s*" +
                         @"(-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)\s*,\s*" +
                         @"(-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)";

            var replacement = @"$1 ""x"":$2, ""y"":$3, ""z"":$4, ""w"":$5";

            return Regex.Replace(json, pattern, replacement, RegexOptions.Multiline);
        }

        /// <summary>
        /// 标准化 Color 类型
        /// 从: {"$type":"...Color...", r, g, b, a}
        /// 到: {"$type":"...Color...", "r":r, "g":g, "b":b, "a":a}
        /// </summary>
        private static string StandardizeColor(string json)
        {
            var pattern = @"(\""?\$type\""?\s*:\s*\""[^\""]*Color[^\""]*\""\s*,)\s*" +
                         @"(-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)\s*,\s*" +
                         @"(-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)\s*,\s*" +
                         @"(-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)\s*,\s*" +
                         @"(-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)";

            var replacement = @"$1 ""r"":$2, ""g"":$3, ""b"":$4, ""a"":$5";

            return Regex.Replace(json, pattern, replacement, RegexOptions.Multiline);
        }

        /// <summary>
        /// 标准化 Vector4 类型
        /// </summary>
        private static string StandardizeVector4(string json)
        {
            var pattern = @"(\""?\$type\""?\s*:\s*\""[^\""]*Vector4[^\""]*\""\s*,)\s*" +
                         @"(-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)\s*,\s*" +
                         @"(-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)\s*,\s*" +
                         @"(-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)\s*,\s*" +
                         @"(-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)";

            var replacement = @"$1 ""x"":$2, ""y"":$3, ""z"":$4, ""w"":$5";

            return Regex.Replace(json, pattern, replacement, RegexOptions.Multiline);
        }

        /// <summary>
        /// 反向转换：将标准 JSON 转回 Odin 裸值格式（如果需要）
        /// </summary>
        public static string ToOdinFormat(string standardJson)
        {
            if (string.IsNullOrEmpty(standardJson))
            {
                return standardJson;
            }

            string result = standardJson;

            // Vector3: {"$type":"...", "x":1, "y":2, "z":3} → {"$type":"...", 1, 2, 3}
            result = Regex.Replace(
                result,
                @"(\""?\$type\""?\s*:\s*\""[^\""]*Vector3[^\""]*\""\s*,)\s*" +
                @"\""x\""\s*:\s*(-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)\s*,\s*" +
                @"\""y\""\s*:\s*(-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)\s*,\s*" +
                @"\""z\""\s*:\s*(-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)",
                @"$1 $2, $3, $4",
                RegexOptions.Multiline
            );

            // 可以添加其他类型的反向转换...

            return result;
        }

#if UNITY_EDITOR
        /// <summary>
        /// 测试方法（仅在编辑器模式下可用）
        /// </summary>
        [UnityEditor.MenuItem("Tools/Test Odin JSON Standardizer")]
        public static void TestStandardizer()
        {
            string testJson = @"{
                ""position"": {
                    ""$type"": ""7|UnityEngine.Vector3, UnityEngine.CoreModule"",
                    1.5,
                    2.0,
                    3.5
                },
                ""rotation"": {
                    ""$type"": ""UnityEngine.Quaternion, UnityEngine.CoreModule"",
                    0,
                    0,
                    0,
                    1
                }
            }";

            string result = Standardize(testJson);
            Debug.Log("Original:\n" + testJson);
            Debug.Log("\nStandardized:\n" + result);
        }
#endif
    }
}
