#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复 README.md 和 PROJECT_SUMMARY.md 的编码问题
"""

def fix_file_encoding(file_path):
    """修复文件编码问题"""
    print(f"正在修复: {file_path}")

    # 尝试不同的编码读取
    encodings_to_try = [
        'utf-8', 'utf-8-sig', 'gbk', 'gb2312', 'gb18030',
        'latin1', 'cp1252', 'iso-8859-1'
    ]

    content = None
    successful_encoding = None

    for encoding in encodings_to_try:
        try:
            with open(file_path, 'r', encoding=encoding, errors='strict') as f:
                content = f.read()
            successful_encoding = encoding
            print(f"  [OK] 成功使用 {encoding} 读取")
            break
        except (UnicodeDecodeError, LookupError) as e:
            continue

    if content is None:
        # 如果所有编码都失败，使用 utf-8 并忽略错误
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        successful_encoding = 'utf-8 (with errors ignored)'
        print(f"  [WARN] 使用 utf-8 读取（忽略错误）")

    # 检查是否需要修复乱码
    # 常见的乱码模式: �
    if '�' in content:
        print(f"  [WARN] 检测到乱码字符")
        # 尝试重新解码
        # 读取原始字节
        with open(file_path, 'rb') as f:
            raw_bytes = f.read()

        # 尝试用 GBK 解码（Windows 中文系统常见）
        try:
            content = raw_bytes.decode('gbk')
            print(f"  [OK] 使用 GBK 解码成功")
        except:
            try:
                content = raw_bytes.decode('gb18030')
                print(f"  [OK] 使用 GB18030 解码成功")
            except:
                print(f"  [ERROR] 无法修复乱码")
                return False

    # 保存为 UTF-8（无 BOM）
    with open(file_path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)

    print(f"  [OK] 已保存为 UTF-8 编码")
    return True

if __name__ == '__main__':
    import os

    base_dir = r'E:\Study\wqaetly\ai_agent_for_skill'

    files_to_fix = [
        os.path.join(base_dir, 'README.md'),
        os.path.join(base_dir, 'PROJECT_SUMMARY.md')
    ]

    print("=" * 60)
    print("开始修复文件编码...")
    print("=" * 60)

    for file_path in files_to_fix:
        if os.path.exists(file_path):
            success = fix_file_encoding(file_path)
            if success:
                print(f"[OK] {os.path.basename(file_path)} 修复成功\n")
            else:
                print(f"[ERROR] {os.path.basename(file_path)} 修复失败\n")
        else:
            print(f"[ERROR] 文件不存在: {file_path}\n")

    print("=" * 60)
    print("修复完成！")
    print("=" * 60)
