#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析文件编码问题
"""
import sys

# 强制 UTF-8 输出
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def analyze_file(file_path):
    print(f"\n分析文件: {file_path}")
    print("=" * 70)

    # 读取原始字节
    with open(file_path, 'rb') as f:
        raw_bytes = f.read(1000)  # 读取前1000字节

    print(f"\n文件大小（前1000字节）: {len(raw_bytes)} bytes")
    print(f"前50字节(hex): {raw_bytes[:50].hex(' ')}")

    # 尝试不同编码
    encodings = ['utf-8', 'gbk', 'gb18030', 'cp936', 'gb2312', 'utf-16', 'latin1']

    print("\n尝试不同编码:")
    print("-" * 70)

    for enc in encodings:
        try:
            content = raw_bytes.decode(enc)
            chinese_count = sum(1 for c in content if '\u4e00' <= c <= '\u9fff')
            replacement_count = content.count('\ufffd')

            print(f"\n{enc:12s}:")
            print(f"  中文字符: {chinese_count}")
            print(f"  替换字符: {replacement_count}")
            print(f"  前100字符: {content[:100]}")

            if replacement_count == 0 and chinese_count > 10:
                print(f"  >>> 这可能是正确的编码！")

        except (UnicodeDecodeError, LookupError) as e:
            print(f"\n{enc:12s}: 解码失败 - {e}")

if __name__ == "__main__":
    # 分析 backup 文件和当前文件
    files = [
        "skill_agent/README.md",
        "skill_agent/README.md.backup",
    ]

    for file_path in files:
        try:
            analyze_file(file_path)
        except FileNotFoundError:
            print(f"\n文件不存在: {file_path}")
        except Exception as e:
            print(f"\n错误: {e}")

    print("\n" + "=" * 70)
