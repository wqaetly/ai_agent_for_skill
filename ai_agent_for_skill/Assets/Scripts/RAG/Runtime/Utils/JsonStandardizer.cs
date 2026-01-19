using System.Text.RegularExpressions;
using UnityEngine;

namespace RAGBuilder
{
    /// <summary>
    /// JSON Standardizer for Unity types
    /// Converts Odin serialized Unity type bare values to standard key-value format
    /// </summary>
    public static class JsonStandardizer
    {
        /// <summary>
        /// Standardize JSON string for compatibility with standard JSON parsers
        /// </summary>
        /// <param name="json">Input JSON string</param>
        /// <returns>Standardized JSON string</returns>
        public static string Standardize(string json)
        {
            if (string.IsNullOrEmpty(json))
            {
                return json;
            }

            string result = json;

            // Process Vector3 bare values
            result = StandardizeVector3(result);

            // Process Vector2 bare values
            result = StandardizeVector2(result);

            // Process Quaternion bare values
            result = StandardizeQuaternion(result);

            // Process Color bare values
            result = StandardizeColor(result);

            // Process Vector4 bare values
            result = StandardizeVector4(result);

            return result;
        }

        /// <summary>
        /// Standardize Vector3 type
        /// From: {"$type":"...Vector3...", x, y, z}
        /// To: {"$type":"...Vector3...", "x":x, "y":y, "z":z}
        /// </summary>
        private static string StandardizeVector3(string json)
        {
            var pattern = @"(\""?\$type\""?\s*:\s*\""[^\""]*Vector3[^\""]*\""\s*,)\s*" +
                         @"(-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)\s*,\s*" +
                         @"(-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)\s*,\s*" +
                         @"(-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)";

            var replacement = @"$1 ""x"":$2, ""y"":$3, ""z"":$4";

            return Regex.Replace(json, pattern, replacement, RegexOptions.Multiline);
        }

        /// <summary>
        /// Standardize Vector2 type
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
        /// Standardize Quaternion type
        /// From: {"$type":"...Quaternion...", x, y, z, w}
        /// To: {"$type":"...Quaternion...", "x":x, "y":y, "z":z, "w":w}
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
        /// Standardize Color type
        /// From: {"$type":"...Color...", r, g, b, a}
        /// To: {"$type":"...Color...", "r":r, "g":g, "b":b, "a":a}
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
        /// Standardize Vector4 type
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
        /// Reverse conversion: Convert standard JSON back to Odin bare value format (if needed)
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

            return result;
        }
    }
}
