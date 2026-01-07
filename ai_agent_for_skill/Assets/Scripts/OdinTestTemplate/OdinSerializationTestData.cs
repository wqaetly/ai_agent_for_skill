using System;
using System.Collections.Generic;
using UnityEngine;
using Sirenix.OdinInspector;
using Sirenix.Serialization;

namespace OdinTestTemplate
{
    /// <summary>
    /// Odin序列化测试模板类
    /// 包含几乎所有常见数据类型和嵌套情况，用于生成完整的Odin JSON测试样本
    /// </summary>
    [Serializable]
    public class OdinSerializationTestData
    {
        #region 基础类型 (Primitive Types)
        
        [FoldoutGroup("基础类型")]
        [LabelText("布尔值")]
        public bool boolValue = true;
        
        [FoldoutGroup("基础类型")]
        [LabelText("字节")]
        public byte byteValue = 255;
        
        [FoldoutGroup("基础类型")]
        [LabelText("短整型")]
        public short shortValue = -32768;
        
        [FoldoutGroup("基础类型")]
        [LabelText("整型")]
        public int intValue = 42;
        
        [FoldoutGroup("基础类型")]
        [LabelText("长整型")]
        public long longValue = 9223372036854775807L;
        
        [FoldoutGroup("基础类型")]
        [LabelText("单精度浮点")]
        public float floatValue = 3.14159f;
        
        [FoldoutGroup("基础类型")]
        [LabelText("双精度浮点")]
        public double doubleValue = 2.718281828459045;
        
        [FoldoutGroup("基础类型")]
        [LabelText("字符")]
        public char charValue = 'A';
        
        [FoldoutGroup("基础类型")]
        [LabelText("字符串")]
        public string stringValue = "Hello, Odin!";
        
        [FoldoutGroup("基础类型")]
        [LabelText("空字符串")]
        public string emptyString = "";
        
        [FoldoutGroup("基础类型")]
        [LabelText("特殊字符字符串")]
        public string specialCharsString = "包含特殊字符: \n\t\"引号\" 和 \\反斜杠\\";
        
        #endregion
        
        #region Unity内置类型 (Unity Built-in Types)
        
        [FoldoutGroup("Unity类型")]
        [LabelText("Vector2")]
        public Vector2 vector2Value = new Vector2(1.5f, 2.5f);
        
        [FoldoutGroup("Unity类型")]
        [LabelText("Vector3")]
        public Vector3 vector3Value = new Vector3(1.0f, 2.0f, 3.0f);
        
        [FoldoutGroup("Unity类型")]
        [LabelText("Vector4")]
        public Vector4 vector4Value = new Vector4(1.0f, 2.0f, 3.0f, 4.0f);
        
        [FoldoutGroup("Unity类型")]
        [LabelText("Vector2Int")]
        public Vector2Int vector2IntValue = new Vector2Int(10, 20);
        
        [FoldoutGroup("Unity类型")]
        [LabelText("Vector3Int")]
        public Vector3Int vector3IntValue = new Vector3Int(1, 2, 3);
        
        [FoldoutGroup("Unity类型")]
        [LabelText("Quaternion")]
        public Quaternion quaternionValue = Quaternion.Euler(45f, 90f, 0f);
        
        [FoldoutGroup("Unity类型")]
        [LabelText("Color")]
        public Color colorValue = new Color(1f, 0.5f, 0.25f, 1f);
        
        [FoldoutGroup("Unity类型")]
        [LabelText("Color32")]
        public Color32 color32Value = new Color32(255, 128, 64, 255);
        
        [FoldoutGroup("Unity类型")]
        [LabelText("Rect")]
        public Rect rectValue = new Rect(0, 0, 100, 50);
        
        [FoldoutGroup("Unity类型")]
        [LabelText("RectInt")]
        public RectInt rectIntValue = new RectInt(10, 20, 200, 100);
        
        [FoldoutGroup("Unity类型")]
        [LabelText("Bounds")]
        public Bounds boundsValue = new Bounds(Vector3.zero, new Vector3(10, 10, 10));
        
        [FoldoutGroup("Unity类型")]
        [LabelText("BoundsInt")]
        public BoundsInt boundsIntValue = new BoundsInt(0, 0, 0, 5, 5, 5);
        
        [FoldoutGroup("Unity类型")]
        [LabelText("AnimationCurve")]
        public AnimationCurve animationCurve = AnimationCurve.EaseInOut(0f, 0f, 1f, 1f);
        
        [FoldoutGroup("Unity类型")]
        [LabelText("Gradient")]
        public Gradient gradientValue = new Gradient();
        
        [FoldoutGroup("Unity类型")]
        [LabelText("LayerMask")]
        public LayerMask layerMaskValue = 1;
        
        #endregion
        
        #region 枚举类型 (Enum Types)
        
        [FoldoutGroup("枚举类型")]
        [LabelText("简单枚举")]
        public SimpleEnum simpleEnumValue = SimpleEnum.OptionB;
        
        [FoldoutGroup("枚举类型")]
        [LabelText("带值枚举")]
        public ValuedEnum valuedEnumValue = ValuedEnum.Medium;
        
        [FoldoutGroup("枚举类型")]
        [LabelText("标志枚举")]
        public FlagsEnum flagsEnumValue = FlagsEnum.Read | FlagsEnum.Write;
        
        #endregion
        
        #region 数组类型 (Array Types)
        
        [FoldoutGroup("数组类型")]
        [LabelText("整型数组")]
        public int[] intArray = new int[] { 1, 2, 3, 4, 5 };
        
        [FoldoutGroup("数组类型")]
        [LabelText("字符串数组")]
        public string[] stringArray = new string[] { "Apple", "Banana", "Cherry" };
        
        [FoldoutGroup("数组类型")]
        [LabelText("Vector3数组")]
        public Vector3[] vector3Array = new Vector3[] 
        { 
            new Vector3(0, 0, 0), 
            new Vector3(1, 1, 1), 
            new Vector3(2, 2, 2) 
        };
        
        [FoldoutGroup("数组类型")]
        [LabelText("空数组")]
        public float[] emptyArray = new float[0];
        
        [FoldoutGroup("数组类型")]
        [LabelText("二维数组")]
        public int[,] twoDimensionalArray = new int[,] { { 1, 2, 3 }, { 4, 5, 6 } };
        
        [FoldoutGroup("数组类型")]
        [LabelText("锯齿数组")]
        public int[][] jaggedArray = new int[][] 
        { 
            new int[] { 1, 2 }, 
            new int[] { 3, 4, 5 }, 
            new int[] { 6 } 
        };
        
        #endregion
        
        #region 集合类型 (Collection Types)
        
        [FoldoutGroup("集合类型")]
        [LabelText("List<int>")]
        public List<int> intList = new List<int> { 10, 20, 30, 40, 50 };
        
        [FoldoutGroup("集合类型")]
        [LabelText("List<string>")]
        public List<string> stringList = new List<string> { "First", "Second", "Third" };
        
        [FoldoutGroup("集合类型")]
        [LabelText("List<Vector3>")]
        public List<Vector3> vector3List = new List<Vector3> 
        { 
            Vector3.zero, 
            Vector3.one, 
            Vector3.up 
        };
        
        [FoldoutGroup("集合类型")]
        [LabelText("空List")]
        public List<int> emptyList = new List<int>();
        
        [FoldoutGroup("集合类型")]
        [LabelText("Dictionary<string, int>")]
        [OdinSerialize]
        public Dictionary<string, int> stringIntDict = new Dictionary<string, int>
        {
            { "health", 100 },
            { "mana", 50 },
            { "stamina", 75 }
        };
        
        [FoldoutGroup("集合类型")]
        [LabelText("Dictionary<int, string>")]
        [OdinSerialize]
        public Dictionary<int, string> intStringDict = new Dictionary<int, string>
        {
            { 1, "One" },
            { 2, "Two" },
            { 3, "Three" }
        };
        
        [FoldoutGroup("集合类型")]
        [LabelText("HashSet<string>")]
        [OdinSerialize]
        public HashSet<string> stringHashSet = new HashSet<string> { "A", "B", "C" };
        
        [FoldoutGroup("集合类型")]
        [LabelText("Queue<int>")]
        [OdinSerialize]
        public Queue<int> intQueue = new Queue<int>(new[] { 1, 2, 3 });
        
        [FoldoutGroup("集合类型")]
        [LabelText("Stack<string>")]
        [OdinSerialize]
        public Stack<string> stringStack = new Stack<string>(new[] { "Bottom", "Middle", "Top" });
        
        #endregion
        
        #region 可空类型 (Nullable Types)
        
        [FoldoutGroup("可空类型")]
        [LabelText("可空整型(有值)")]
        public int? nullableIntWithValue = 42;
        
        [FoldoutGroup("可空类型")]
        [LabelText("可空整型(空)")]
        public int? nullableIntNull = null;
        
        [FoldoutGroup("可空类型")]
        [LabelText("可空浮点(有值)")]
        public float? nullableFloatWithValue = 3.14f;
        
        [FoldoutGroup("可空类型")]
        [LabelText("可空布尔(空)")]
        public bool? nullableBoolNull = null;
        
        [FoldoutGroup("可空类型")]
        [LabelText("可空枚举")]
        public SimpleEnum? nullableEnum = SimpleEnum.OptionA;
        
        #endregion
        
        #region 嵌套对象 (Nested Objects)
        
        [FoldoutGroup("嵌套对象")]
        [LabelText("简单嵌套对象")]
        public NestedSimpleClass nestedSimple = new NestedSimpleClass();
        
        [FoldoutGroup("嵌套对象")]
        [LabelText("深层嵌套对象")]
        public NestedDeepClass nestedDeep = new NestedDeepClass();
        
        [FoldoutGroup("嵌套对象")]
        [LabelText("空嵌套对象")]
        public NestedSimpleClass nullNestedObject = null;
        
        [FoldoutGroup("嵌套对象")]
        [LabelText("嵌套对象列表")]
        public List<NestedSimpleClass> nestedObjectList = new List<NestedSimpleClass>
        {
            new NestedSimpleClass { name = "Item1", value = 100 },
            new NestedSimpleClass { name = "Item2", value = 200 }
        };
        
        [FoldoutGroup("嵌套对象")]
        [LabelText("嵌套对象字典")]
        [OdinSerialize]
        public Dictionary<string, NestedSimpleClass> nestedObjectDict = new Dictionary<string, NestedSimpleClass>
        {
            { "first", new NestedSimpleClass { name = "First", value = 1 } },
            { "second", new NestedSimpleClass { name = "Second", value = 2 } }
        };
        
        #endregion
        
        #region 结构体 (Struct Types)
        
        [FoldoutGroup("结构体")]
        [LabelText("自定义结构体")]
        public CustomStruct customStruct = new CustomStruct 
        { 
            id = 1, 
            position = new Vector3(1, 2, 3), 
            isActive = true 
        };
        
        [FoldoutGroup("结构体")]
        [LabelText("结构体数组")]
        public CustomStruct[] structArray = new CustomStruct[]
        {
            new CustomStruct { id = 1, position = Vector3.zero, isActive = true },
            new CustomStruct { id = 2, position = Vector3.one, isActive = false }
        };
        
        #endregion
        
        #region 多态类型 (Polymorphic Types)
        
        [FoldoutGroup("多态类型")]
        [LabelText("基类引用(派生类A)")]
        [OdinSerialize]
        public BaseClass polymorphicA = new DerivedClassA { baseName = "DerivedA", derivedAValue = 100 };
        
        [FoldoutGroup("多态类型")]
        [LabelText("基类引用(派生类B)")]
        [OdinSerialize]
        public BaseClass polymorphicB = new DerivedClassB { baseName = "DerivedB", derivedBText = "Hello" };
        
        [FoldoutGroup("多态类型")]
        [LabelText("多态列表")]
        [OdinSerialize]
        public List<BaseClass> polymorphicList = new List<BaseClass>
        {
            new DerivedClassA { baseName = "A1", derivedAValue = 10 },
            new DerivedClassB { baseName = "B1", derivedBText = "Text1" },
            new DerivedClassA { baseName = "A2", derivedAValue = 20 }
        };
        
        #endregion
        
        #region 接口类型 (Interface Types)
        
        [FoldoutGroup("接口类型")]
        [LabelText("接口实现A")]
        [OdinSerialize]
        public ITestInterface interfaceImplA = new InterfaceImplA { id = 1, valueA = 100 };
        
        [FoldoutGroup("接口类型")]
        [LabelText("接口实现B")]
        [OdinSerialize]
        public ITestInterface interfaceImplB = new InterfaceImplB { id = 2, textB = "Interface B" };
        
        [FoldoutGroup("接口类型")]
        [LabelText("接口列表")]
        [OdinSerialize]
        public List<ITestInterface> interfaceList = new List<ITestInterface>
        {
            new InterfaceImplA { id = 1, valueA = 10 },
            new InterfaceImplB { id = 2, textB = "Hello" }
        };
        
        #endregion
        
        #region Unity资源引用 (Unity Asset References)
        
        [FoldoutGroup("Unity资源引用")]
        [LabelText("GameObject引用")]
        public GameObject gameObjectRef;
        
        [FoldoutGroup("Unity资源引用")]
        [LabelText("Transform引用")]
        public Transform transformRef;
        
        [FoldoutGroup("Unity资源引用")]
        [LabelText("Sprite引用")]
        public Sprite spriteRef;
        
        [FoldoutGroup("Unity资源引用")]
        [LabelText("Material引用")]
        public Material materialRef;
        
        [FoldoutGroup("Unity资源引用")]
        [LabelText("AudioClip引用")]
        public AudioClip audioClipRef;
        
        [FoldoutGroup("Unity资源引用")]
        [LabelText("Texture2D引用")]
        public Texture2D texture2DRef;
        
        #endregion
        
        #region 特殊情况 (Special Cases)
        
        [FoldoutGroup("特殊情况")]
        [LabelText("自引用对象")]
        [OdinSerialize]
        public SelfReferencingClass selfRef = new SelfReferencingClass { name = "Root" };
        
        [FoldoutGroup("特殊情况")]
        [LabelText("泛型类")]
        [OdinSerialize]
        public GenericClass<int> genericInt = new GenericClass<int> { value = 42, items = new List<int> { 1, 2, 3 } };
        
        [FoldoutGroup("特殊情况")]
        [LabelText("泛型类(字符串)")]
        [OdinSerialize]
        public GenericClass<string> genericString = new GenericClass<string> { value = "Hello", items = new List<string> { "A", "B" } };
        
        [FoldoutGroup("特殊情况")]
        [LabelText("复杂嵌套字典")]
        [OdinSerialize]
        public Dictionary<string, List<Vector3>> complexNestedDict = new Dictionary<string, List<Vector3>>
        {
            { "path1", new List<Vector3> { Vector3.zero, Vector3.one } },
            { "path2", new List<Vector3> { Vector3.up, Vector3.down, Vector3.left } }
        };
        
        [FoldoutGroup("特殊情况")]
        [LabelText("元组")]
        [OdinSerialize]
        public (int id, string name, Vector3 pos) tupleValue = (1, "Test", new Vector3(1, 2, 3));
        
        #endregion
    }
    
    #region 辅助枚举定义
    
    public enum SimpleEnum
    {
        OptionA,
        OptionB,
        OptionC
    }
    
    public enum ValuedEnum
    {
        Low = 10,
        Medium = 50,
        High = 100
    }
    
    [Flags]
    public enum FlagsEnum
    {
        None = 0,
        Read = 1,
        Write = 2,
        Execute = 4,
        All = Read | Write | Execute
    }
    
    #endregion
    
    #region 辅助结构体定义
    
    [Serializable]
    public struct CustomStruct
    {
        public int id;
        public Vector3 position;
        public bool isActive;
    }
    
    #endregion
    
    #region 辅助类定义
    
    [Serializable]
    public class NestedSimpleClass
    {
        public string name = "Default";
        public int value = 0;
        public Vector3 position = Vector3.zero;
        public Color color = Color.white;
    }
    
    [Serializable]
    public class NestedDeepClass
    {
        public string id = "deep-001";
        public NestedSimpleClass level1 = new NestedSimpleClass { name = "Level1" };
        public NestedLevel2 level2 = new NestedLevel2();
        
        [Serializable]
        public class NestedLevel2
        {
            public string name = "Level2";
            public NestedLevel3 level3 = new NestedLevel3();
            
            [Serializable]
            public class NestedLevel3
            {
                public string name = "Level3";
                public int deepValue = 999;
                public List<int> deepList = new List<int> { 1, 2, 3 };
            }
        }
    }
    
    [Serializable]
    public class BaseClass
    {
        public string baseName = "Base";
    }
    
    [Serializable]
    public class DerivedClassA : BaseClass
    {
        public int derivedAValue = 0;
    }
    
    [Serializable]
    public class DerivedClassB : BaseClass
    {
        public string derivedBText = "";
    }
    
    public interface ITestInterface
    {
        int id { get; set; }
    }
    
    [Serializable]
    public class InterfaceImplA : ITestInterface
    {
        [field: SerializeField]
        public int id { get; set; }
        public int valueA;
    }
    
    [Serializable]
    public class InterfaceImplB : ITestInterface
    {
        [field: SerializeField]
        public int id { get; set; }
        public string textB;
    }
    
    [Serializable]
    public class SelfReferencingClass
    {
        public string name;
        public SelfReferencingClass child;
        public List<SelfReferencingClass> children = new List<SelfReferencingClass>();
    }
    
    [Serializable]
    public class GenericClass<T>
    {
        public T value;
        public List<T> items = new List<T>();
    }
    
    #endregion
}
