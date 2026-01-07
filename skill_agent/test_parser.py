"""测试 Odin JSON 解析器"""
import sys
sys.path.insert(0, '.')

from core.odin_json_parser import OdinJsonParser

parser = OdinJsonParser()
result = parser.parse_file('e:/Study/wqaetly/ai_agent_for_skill/ai_agent_for_skill/OdinTestOutput/odin_test_data.json')

print('=== Basic Types ===')
print(f'boolValue: {result.get("boolValue")}')
print(f'intValue: {result.get("intValue")}')
print(f'stringValue: {result.get("stringValue")}')

print('\n=== Unity Types ===')
print(f'vector2Value: {result.get("vector2Value")}')
print(f'vector3Value: {result.get("vector3Value")}')
print(f'colorValue: {result.get("colorValue")}')
print(f'quaternionValue: {result.get("quaternionValue")}')

print('\n=== Collections ===')
print(f'intArray: {result.get("intArray")}')
print(f'stringList: {result.get("stringList")}')
print(f'stringIntDict: {result.get("stringIntDict")}')

print('\n=== Nested Objects ===')
print(f'nestedSimple: {result.get("nestedSimple")}')

print('\n=== Nullable ===')
print(f'nullableIntWithValue: {result.get("nullableIntWithValue")}')
print(f'nullableIntNull: {result.get("nullableIntNull")}')

print('\nParsing successful!')
