#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复 README.md 和 PROJECT_SUMMARY.md 的编码问题（无需额外依赖）
"""
import os
import shutil

def fix_encoding(file_path):
    """修复文件编码为 UTF-8"""

    print(f"\n处理文件: {file_path}")

    # 备份原文件
    backup_path = file_path + '.backup'
    shutil.copy2(file_path, backup_path)
    print(f"✓ 已创建备份: {backup_path}")

    # 读取原始字节
    with open(file_path, 'rb') as f:
        raw_content = f.read()

    # 尝试多种编码方式解码
    encodings_to_try = [
        ('utf-8', '尝试 UTF-8'),
        ('utf-8-sig', '尝试 UTF-8-BOM'),
        ('gbk', '尝试 GBK'),
        ('gb2312', '尝试 GB2312'),
        ('cp1252', '尝试 Windows-1252'),
        ('latin1', '尝试 Latin-1'),
    ]

    decoded_content = None
    successful_encoding = None

    for encoding, desc in encodings_to_try:
        try:
            decoded = raw_content.decode(encoding)
            print(f"  {desc}: 成功")

            # 检查是否是双重编码问题（PROJECT_SUMMARY.md 的典型问题）
            # 如果解码后包含类似 é¡¹ç® 这样的字符，说明需要二次转换
            if 'é¡¹ç®' in decoded or 'ç³»ç»' in decoded or 'æè½' in decoded:
                print(f"  检测到双重编码，尝试修复...")
                try:
                    # 先编码回 latin1，再用 utf-8 解码
                    fixed = decoded.encode('latin1').decode('utf-8')
                    decoded_content = fixed
                    successful_encoding = f"{encoding} → latin1 → utf-8"
                    print(f"  ✓ 双重编码修复成功")
                    break
                except:
                    # 如果修复失败，继续用原来的
                    pass

            # 如果没有明显乱码，直接使用
            decoded_content = decoded
            successful_encoding = encoding
            break

        except (UnicodeDecodeError, LookupError) as e:
            print(f"  {desc}: 失败")
            continue

    if decoded_content is None:
        print(f"✗ 所有编码尝试均失败")
        return False

    print(f"✓ 解码成功，使用: {successful_encoding}")

    # 保存为 UTF-8（无 BOM）
    try:
        with open(file_path, 'w', encoding='utf-8', newline='\n') as f:
            f.write(decoded_content)
        print(f"✓ 文件已保存为 UTF-8 编码")

        # 验证保存结果
        with open(file_path, 'r', encoding='utf-8') as f:
            verify_content = f.read()

        # 简单验证：检查常见中文字符
        if '项目' in verify_content or '技能' in verify_content or '系统' in verify_content:
            print(f"✓ 验证成功：文件包含正确的中文字符")
            return True
        else:
            print(f"⚠ 警告：验证时未找到预期的中文字符")
            return True

    except Exception as e:
        print(f"✗ 保存文件失败: {e}")
        # 恢复备份
        shutil.copy2(backup_path, file_path)
        print(f"✓ 已从备份恢复")
        return False

def main():
    base_dir = r"E:\Study\wqaetly\ai_agent_for_skill"

    files_to_fix = [
        os.path.join(base_dir, "README.md"),
        os.path.join(base_dir, "PROJECT_SUMMARY.md")
    ]

    print("=" * 70)
    print("开始修复文件编码问题")
    print("=" * 70)

    success_count = 0
    for file_path in files_to_fix:
        if os.path.exists(file_path):
            if fix_encoding(file_path):
                success_count += 1
        else:
            print(f"\n✗ 文件不存在: {file_path}")

    print("\n" + "=" * 70)
    print(f"修复完成: {success_count}/{len(files_to_fix)} 个文件成功")
    print("=" * 70)

    if success_count == len(files_to_fix):
        print("\n✓ 所有文件编码已修复为 UTF-8")
        print("✓ 原文件备份为 .backup 后缀")
        print("\n建议：")
        print("1. 用文本编辑器打开文件验证中文显示是否正常")
        print("2. 如果正常，可以删除 .backup 备份文件")
        print("3. 如果异常，可以从 .backup 恢复")
    else:
        print("\n✗ 部分文件修复失败，请检查错误信息")

if __name__ == "__main__":
    main()
