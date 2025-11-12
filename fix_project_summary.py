#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
专门修复 PROJECT_SUMMARY.md 的编码问题
"""

import sys

file_path = r'E:\Study\wqaetly\ai_agent_for_skill\PROJECT_SUMMARY.md'

print("Reading PROJECT_SUMMARY.md...")

# 读取原始字节
with open(file_path, 'rb') as f:
    raw_bytes = f.read()

print(f"File size: {len(raw_bytes)} bytes")

# 分析前100个字符的编码
print("\nFirst 100 bytes (hex):")
print(raw_bytes[:100].hex())

# 尝试UTF-8解码
try:
    content = raw_bytes.decode('utf-8', errors='strict')
    print("\n[OK] File is valid UTF-8")
    print("First 100 characters:")
    print(content[:100])

    # 检查是否包含正常的中文
    if '项目' in content or '系统' in content:
        print("[OK] File content looks correct, no fix needed")
        sys.exit(0)
    else:
        print("[WARN] File is UTF-8 but content seems wrong")

except UnicodeDecodeError as e:
    print(f"\n[ERROR] File is not valid UTF-8: {e}")
    print("Will try to fix...")

# 如果UTF-8解码失败，可能是编码标签问题
# 直接替换有问题的字节序列

# 检查是否是UTF-8的BOM问题
if raw_bytes[:3] == b'\xef\xbb\xbf':
    print("[INFO] File has UTF-8 BOM, removing...")
    raw_bytes = raw_bytes[3:]

# 现在尝试用UTF-8解码
try:
    content = raw_bytes.decode('utf-8', errors='strict')
    print("[OK] Successfully decoded as UTF-8")

    # 保存回文件（无BOM）
    with open(file_path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)

    print(f"[OK] File saved: {file_path}")
    print("\nFirst 100 characters of fixed content:")
    print(content[:100])

except UnicodeDecodeError as e:
    print(f"[ERROR] Still cannot decode: {e}")
    print("File may be corrupted beyond repair")
    sys.exit(1)
