#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复 README.md 和 PROJECT_SUMMARY.md 的编码问题
"""
import os
import shutil
import sys

# 设置标准输出为 UTF-8 编码
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def fix_encoding(file_path):
    """修复文件编码为 UTF-8"""

    print(f"\n正在处理: {file_path}")

    # 备份原文件
    backup_path = file_path + '.backup'
    shutil.copy2(file_path, backup_path)
    print(f"[OK] 备份已创建: {backup_path}")

    # 读取原始字节
    with open(file_path, 'rb') as f:
        raw_content = f.read()

    # 尝试多种编码方式解码
    encodings_to_try = [
        ('utf-8', 'UTF-8'),
        ('utf-8-sig', 'UTF-8-BOM'),
        ('gbk', 'GBK'),
        ('gb2312', 'GB2312'),
        ('cp1252', 'Windows-1252'),
        ('latin1', 'Latin-1'),
    ]

    decoded_content = None
    successful_encoding = None

    for encoding, name in encodings_to_try:
        try:
            decoded = raw_content.decode(encoding)
            print(f"  尝试 {name}: 成功")

            # 检查是否是双重编码问题
            # PROJECT_SUMMARY.md 的典型特征：é¡¹ç®æ»ç»
            if 'é¡¹ç®' in decoded or 'ç³»ç»' in decoded or 'æè½' in decoded:
                print(f"  检测到双重编码问题，尝试修复...")
                try:
                    # 双重编码修复：先编码回 latin1，再用 utf-8 解码
                    fixed = decoded.encode('latin1').decode('utf-8')
                    decoded_content = fixed
                    successful_encoding = f"{name} -> Latin-1 -> UTF-8 (双重编码修复)"
                    print(f"  [OK] 双重编码修复成功")
                    break
                except Exception as e:
                    print(f"  [WARN] 双重编码修复失败: {e}")
                    # 修复失败，继续使用原解码结果
                    pass

            # 如果没有明显乱码，直接使用
            decoded_content = decoded
            successful_encoding = name
            break

        except (UnicodeDecodeError, LookupError) as e:
            print(f"  尝试 {name}: 失败")
            continue

    if decoded_content is None:
        print(f"[ERROR] 所有编码尝试均失败")
        return False

    print(f"[OK] 解码成功: {successful_encoding}")

    # 保存为 UTF-8（无 BOM）
    try:
        with open(file_path, 'w', encoding='utf-8', newline='\n') as f:
            f.write(decoded_content)
        print(f"[OK] 已保存为 UTF-8 编码")

        # 验证保存结果
        with open(file_path, 'r', encoding='utf-8') as f:
            verify_content = f.read()

        # 验证：检查常见中文字符
        chinese_chars = ['项目', '技能', '系统', '智能', '配置']
        found_chars = [char for char in chinese_chars if char in verify_content]

        if found_chars:
            print(f"[OK] 验证成功，找到中文字符: {', '.join(found_chars[:3])}")
            return True
        else:
            print(f"[WARN] 验证时未找到预期的中文字符，但文件已保存")
            return True

    except Exception as e:
        print(f"[ERROR] 保存文件失败: {e}")
        # 恢复备份
        shutil.copy2(backup_path, file_path)
        print(f"[OK] 已从备份恢复")
        return False

def main():
    base_dir = r"E:\Study\wqaetly\ai_agent_for_skill"

    files_to_fix = [
        os.path.join(base_dir, "README.md"),
        os.path.join(base_dir, "PROJECT_SUMMARY.md")
    ]

    print("=" * 70)
    print("文件编码修复工具")
    print("=" * 70)

    success_count = 0
    for file_path in files_to_fix:
        if os.path.exists(file_path):
            if fix_encoding(file_path):
                success_count += 1
        else:
            print(f"\n[ERROR] 文件不存在: {file_path}")

    print("\n" + "=" * 70)
    print(f"修复结果: {success_count}/{len(files_to_fix)} 个文件成功")
    print("=" * 70)

    if success_count == len(files_to_fix):
        print("\n[OK] 所有文件编码已修复为 UTF-8")
        print("[INFO] 原文件备份为 .backup 后缀")
        print("\n操作建议:")
        print("1. 用文本编辑器打开文件验证中文显示是否正常")
        print("2. 如果正常，可以删除 .backup 备份文件")
        print("3. 如果异常，可以从 .backup 恢复原文件")
    else:
        print("\n[ERROR] 部分文件修复失败，请检查错误信息")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n[FATAL ERROR] 程序异常: {e}")
        import traceback
        traceback.print_exc()
