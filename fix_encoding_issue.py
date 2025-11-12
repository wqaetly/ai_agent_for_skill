#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复 README.md 和 PROJECT_SUMMARY.md 的编码问题
"""
import os
import chardet

def detect_and_fix_encoding(file_path):
    """检测文件编码并修复为 UTF-8"""

    print(f"\n处理文件: {file_path}")

    # 备份原文件
    backup_path = file_path + '.backup'
    with open(file_path, 'rb') as f:
        original_content = f.read()

    with open(backup_path, 'wb') as f:
        f.write(original_content)
    print(f"✓ 已创建备份: {backup_path}")

    # 检测编码
    detected = chardet.detect(original_content)
    detected_encoding = detected['encoding']
    confidence = detected['confidence']
    print(f"检测到的编码: {detected_encoding} (置信度: {confidence:.2%})")

    # 尝试多种编码方式解码
    encodings_to_try = [
        detected_encoding,
        'utf-8',
        'gbk',
        'gb2312',
        'utf-8-sig',  # UTF-8 with BOM
        'cp1252',     # Windows-1252
        'latin1',
        'iso-8859-1'
    ]

    decoded_content = None
    successful_encoding = None

    for encoding in encodings_to_try:
        if not encoding:
            continue
        try:
            decoded_content = original_content.decode(encoding)
            successful_encoding = encoding
            print(f"✓ 成功使用 {encoding} 解码")
            break
        except (UnicodeDecodeError, LookupError) as e:
            print(f"✗ {encoding} 解码失败: {e}")
            continue

    if decoded_content is None:
        print(f"✗ 所有编码尝试均失败")
        return False

    # 检查是否有乱码（PROJECT_SUMMARY.md 的情况）
    # 如果检测到是 utf-8 但包含类似 é¡¹ç® 这样的字符，说明是双重编码问题
    if 'é¡¹ç®' in decoded_content or 'ç³»ç»' in decoded_content:
        print("检测到双重编码问题，尝试修复...")
        try:
            # 先编码为 latin1，再解码为 utf-8
            fixed_content = decoded_content.encode('latin1').decode('utf-8')
            decoded_content = fixed_content
            print("✓ 双重编码问题已修复")
        except Exception as e:
            print(f"✗ 双重编码修复失败: {e}")

    # 保存为 UTF-8 (without BOM)
    try:
        with open(file_path, 'w', encoding='utf-8', newline='\n') as f:
            f.write(decoded_content)
        print(f"✓ 文件已保存为 UTF-8 编码")
        return True
    except Exception as e:
        print(f"✗ 保存文件失败: {e}")
        # 恢复备份
        with open(backup_path, 'rb') as f:
            backup_content = f.read()
        with open(file_path, 'wb') as f:
            f.write(backup_content)
        print(f"✓ 已从备份恢复")
        return False

def main():
    base_dir = r"E:\Study\wqaetly\ai_agent_for_skill"

    files_to_fix = [
        os.path.join(base_dir, "README.md"),
        os.path.join(base_dir, "PROJECT_SUMMARY.md")
    ]

    print("=" * 60)
    print("开始修复文件编码问题")
    print("=" * 60)

    success_count = 0
    for file_path in files_to_fix:
        if os.path.exists(file_path):
            if detect_and_fix_encoding(file_path):
                success_count += 1
        else:
            print(f"\n✗ 文件不存在: {file_path}")

    print("\n" + "=" * 60)
    print(f"修复完成: {success_count}/{len(files_to_fix)} 个文件成功")
    print("=" * 60)

    if success_count == len(files_to_fix):
        print("\n✓ 所有文件编码已修复为 UTF-8")
        print("✓ 原文件备份为 .backup 后缀")
    else:
        print("\n✗ 部分文件修复失败，请检查错误信息")

if __name__ == "__main__":
    main()
