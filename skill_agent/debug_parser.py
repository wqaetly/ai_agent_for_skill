"""调试 Odin JSON 解析器"""
import sys
sys.path.insert(0, '.')

from core.odin_json_parser import parse_odin_json_raw
import json

# 读取文件
with open('e:/Study/wqaetly/ai_agent_for_skill/ai_agent_for_skill/OdinTestOutput/odin_test_data.json', 'r', encoding='utf-8-sig') as f:
    json_str = f.read()

# 手动执行预处理
if json_str.startswith('\ufeff'):
    json_str = json_str[1:]

result = []
i = 0
n = len(json_str)
stack = []

while i < n:
    c = json_str[i]
    
    if c in ' \t\n\r':
        result.append(c)
        i += 1
        continue
    
    if c == '"':
        result.append(c)
        i += 1
        while i < n:
            c2 = json_str[i]
            result.append(c2)
            i += 1
            if c2 == '\\' and i < n:
                result.append(json_str[i])
                i += 1
            elif c2 == '"':
                break
        if stack and stack[-1][3] == 'object':
            stack[-1][2] = False
        continue
    
    if c == '{':
        if stack and stack[-1][3] == 'object' and stack[-1][1] and not stack[-1][2]:
            bare_idx = stack[-1][0]
            result.append(f'"{bare_idx}": ')
            stack[-1][0] += 1
        
        result.append(c)
        i += 1
        lookahead = json_str[i:i+300]
        first_brace = lookahead.find('}')
        if first_brace > 0:
            lookahead = lookahead[:first_brace]
        has_type = '"$type"' in lookahead
        stack.append([0, has_type, False, 'object'])
        continue
    
    if c == '}':
        result.append(c)
        i += 1
        if stack:
            stack.pop()
        if stack and stack[-1][3] == 'object':
            stack[-1][2] = False
        continue
    
    if c == '[':
        result.append(c)
        i += 1
        stack.append([0, False, False, 'array'])
        continue
    
    if c == ']':
        result.append(c)
        i += 1
        if stack:
            stack.pop()
        if stack and stack[-1][3] == 'object':
            stack[-1][2] = False
        continue
    
    if c == ':':
        result.append(c)
        i += 1
        if stack and stack[-1][3] == 'object':
            stack[-1][2] = True
        continue
    
    if c == ',':
        result.append(c)
        i += 1
        if stack and stack[-1][3] == 'object':
            stack[-1][2] = False
        continue
    
    if stack and stack[-1][3] == 'object' and stack[-1][1] and not stack[-1][2]:
        if c in '-0123456789tfn':
            if c == 't' and json_str[i:i+4] == 'true':
                bare_idx = stack[-1][0]
                result.append(f'"{bare_idx}": true')
                stack[-1][0] += 1
                i += 4
                continue
            elif c == 'f' and json_str[i:i+5] == 'false':
                bare_idx = stack[-1][0]
                result.append(f'"{bare_idx}": false')
                stack[-1][0] += 1
                i += 5
                continue
            elif c == 'n' and json_str[i:i+4] == 'null':
                bare_idx = stack[-1][0]
                result.append(f'"{bare_idx}": null')
                stack[-1][0] += 1
                i += 4
                continue
            elif c in '-0123456789':
                num_chars = []
                while i < n and json_str[i] in '-+0123456789.eE':
                    num_chars.append(json_str[i])
                    i += 1
                num_str = ''.join(num_chars)
                bare_idx = stack[-1][0]
                result.append(f'"{bare_idx}": {num_str}')
                stack[-1][0] += 1
                continue
    
    if c == '$' and json_str[i:i+5] == '$iref':
        ref_start = i
        while i < n and json_str[i] not in ',}\n\r\t ':
            i += 1
        ref_str = json_str[ref_start:i]
        result.append(f'"{ref_str}"')
        if stack and stack[-1][3] == 'object':
            stack[-1][2] = False
        continue
    
    if stack and (stack[-1][2] or stack[-1][3] == 'array'):
        if c in '-0123456789':
            num_chars = []
            while i < n and json_str[i] in '-+0123456789.eE':
                num_chars.append(json_str[i])
                i += 1
            num_str = ''.join(num_chars)
            result.append(num_str)
            if stack[-1][3] == 'object':
                stack[-1][2] = False
            continue
        elif c == 't' and json_str[i:i+4] == 'true':
            result.append('true')
            i += 4
            if stack[-1][3] == 'object':
                stack[-1][2] = False
            continue
        elif c == 'f' and json_str[i:i+5] == 'false':
            result.append('false')
            i += 5
            if stack[-1][3] == 'object':
                stack[-1][2] = False
            continue
        elif c == 'n' and json_str[i:i+4] == 'null':
            result.append('null')
            i += 4
            if stack[-1][3] == 'object':
                stack[-1][2] = False
            continue
    
    result.append(c)
    i += 1

processed_json = ''.join(result)

# 尝试解析
try:
    parsed = json.loads(processed_json)
    print("解析成功!")
except json.JSONDecodeError as e:
    print(f"JSON 解析错误: {e}")
    print(f"错误位置: 行 {e.lineno}, 列 {e.colno}")
    
    # 显示错误位置附近的内容
    lines = processed_json.split('\n')
    error_line = e.lineno - 1
    start_line = max(0, error_line - 3)
    end_line = min(len(lines), error_line + 4)
    
    print("\n处理后的JSON（错误位置附近）:")
    for idx in range(start_line, end_line):
        marker = ">>> " if idx == error_line else "    "
        print(f"{marker}{idx+1}: {lines[idx]}")
    
    # 显示错误附近的内容
    # 重新处理以获取处理后的JSON
    from core.odin_json_parser import parse_odin_json_raw
    
    # 手动执行预处理部分
    if json_str.startswith('\ufeff'):
        json_str = json_str[1:]
    
    result = []
    i = 0
    n = len(json_str)
    stack = []
    
    while i < n:
        c = json_str[i]
        
        if c in ' \t\n\r':
            result.append(c)
            i += 1
            continue
        
        if c == '"':
            start = i
            result.append(c)
            i += 1
            while i < n:
                c2 = json_str[i]
                result.append(c2)
                i += 1
                if c2 == '\\' and i < n:
                    result.append(json_str[i])
                    i += 1
                elif c2 == '"':
                    break
            continue
        
        if c == '{':
            result.append(c)
            i += 1
            lookahead = json_str[i:i+200]
            has_type = '"$type"' in lookahead.split('}')[0] if '}' in lookahead else '"$type"' in lookahead
            stack.append([0, has_type, False])
            continue
        
        if c == '}':
            result.append(c)
            i += 1
            if stack:
                stack.pop()
            continue
        
        if c == '[':
            result.append(c)
            i += 1
            continue
        
        if c == ']':
            result.append(c)
            i += 1
            continue
        
        if c == ':':
            result.append(c)
            i += 1
            if stack:
                stack[-1][2] = True
            continue
        
        if c == ',':
            result.append(c)
            i += 1
            if stack:
                stack[-1][2] = False
            continue
        
        if stack and stack[-1][1] and not stack[-1][2]:
            if c in '-0123456789tfn':
                value_start = i
                if c == 't' and json_str[i:i+4] == 'true':
                    bare_idx = stack[-1][0]
                    result.append(f'"{bare_idx}": ')
                    stack[-1][0] += 1
                    result.append('true')
                    i += 4
                    continue
                elif c == 'f' and json_str[i:i+5] == 'false':
                    bare_idx = stack[-1][0]
                    result.append(f'"{bare_idx}": ')
                    stack[-1][0] += 1
                    result.append('false')
                    i += 5
                    continue
                elif c == 'n' and json_str[i:i+4] == 'null':
                    bare_idx = stack[-1][0]
                    result.append(f'"{bare_idx}": ')
                    stack[-1][0] += 1
                    result.append('null')
                    i += 4
                    continue
                elif c in '-0123456789':
                    num_chars = []
                    while i < n and json_str[i] in '-+0123456789.eE':
                        num_chars.append(json_str[i])
                        i += 1
                    num_str = ''.join(num_chars)
                    bare_idx = stack[-1][0]
                    result.append(f'"{bare_idx}": {num_str}')
                    stack[-1][0] += 1
                    continue
        
        if c == '$' and json_str[i:i+5] == '$iref':
            ref_start = i
            while i < n and json_str[i] not in ',}\n\r\t ':
                i += 1
            ref_str = json_str[ref_start:i]
            result.append(f'"{ref_str}"')
            continue
        
        result.append(c)
        i += 1
        if stack:
            stack[-1][2] = False
    
    processed_json = ''.join(result)
    
    # 显示错误位置附近的内容
    lines = processed_json.split('\n')
    error_line = e.lineno - 1
    start_line = max(0, error_line - 3)
    end_line = min(len(lines), error_line + 4)
    
    print("\n处理后的JSON（错误位置附近）:")
    for i in range(start_line, end_line):
        marker = ">>> " if i == error_line else "    "
        print(f"{marker}{i+1}: {lines[i]}")
