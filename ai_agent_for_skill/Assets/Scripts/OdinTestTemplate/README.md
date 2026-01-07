# Odin序列化测试模板

用于生成包含各种数据类型的Odin JSON测试样本，帮助完善Python端的Odin解析器。

## 包含的数据类型

| 类别 | 类型 |
|------|------|
| 基础类型 | bool, byte, short, int, long, float, double, char, string |
| Unity类型 | Vector2/3/4, Vector2Int/3Int, Quaternion, Color, Color32, Rect, Bounds, AnimationCurve, Gradient, LayerMask |
| 枚举类型 | 简单枚举, 带值枚举, Flags枚举 |
| 数组类型 | 一维数组, 二维数组, 锯齿数组 |
| 集合类型 | List, Dictionary, HashSet, Queue, Stack |
| 可空类型 | int?, float?, bool?, enum? |
| 嵌套对象 | 简单嵌套, 深层嵌套(3层), 嵌套列表, 嵌套字典 |
| 结构体 | 自定义struct |
| 多态类型 | 基类引用派生类, 多态列表 |
| 接口类型 | 接口实现, 接口列表 |
| Unity资源 | GameObject, Transform, Sprite, Material, AudioClip, Texture2D |
| 特殊情况 | 自引用, 泛型类, 复杂嵌套字典, 元组 |

## 使用方法

### 方法1: 使用Editor窗口
1. Unity菜单: `Tools > Odin Test > Serialization Test Window`
2. 设置导出目录和文件名
3. 点击"导出为Odin JSON"

### 方法2: 创建ScriptableObject资产
1. Project窗口右键: `Create > Odin Test > Test Data Asset`
2. 在Inspector中编辑数据
3. 使用Editor窗口导出

### 方法3: 代码调用
```csharp
// 快速导出
OdinJsonExporter.QuickExport("path/to/output.json");

// 自定义数据
var data = OdinJsonExporter.CreateFullTestData();
data.intValue = 100;
OdinJsonExporter.ExportToFile(data, "path/to/output.json");
```

## 文件说明

- `OdinSerializationTestData.cs` - 主测试数据类
- `OdinTestDataAsset.cs` - ScriptableObject容器
- `OdinJsonExporter.cs` - 序列化工具类
- `Editor/OdinSerializationTestWindow.cs` - Editor窗口
