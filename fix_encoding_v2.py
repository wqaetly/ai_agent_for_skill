#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复编码问题 - V2
专门处理UTF-8被误读为其他编码的情况
"""

def fix_utf8_misread_as_latin1(file_path):
    """
    修复UTF-8文件被误读为Latin1的情况
    例如：'项目' 被错误显示为 'é¡¹ç®'
    """
    print(f"[INFO] Processing: {file_path}")

    try:
        # 1. 先读取为Latin1（这样读取的字符串实际包含了原始UTF-8字节的Latin1表示）
        with open(file_path, 'r', encoding='latin1') as f:
            misread_content = f.read()

        # 2. 将字符串转回字节（使用Latin1编码）
        utf8_bytes = misread_content.encode('latin1')

        # 3. 用UTF-8解码这些字节
        correct_content = utf8_bytes.decode('utf-8')

        # 4. 检查解码是否成功（是否包含合理的中文字符）
        if '项目' in correct_content or '系统' in correct_content or '技能' in correct_content:
            print(f"[OK] Successfully decoded as UTF-8")

            # 5. 保存为UTF-8（无BOM）
            with open(file_path, 'w', encoding='utf-8', newline='\n') as f:
                f.write(correct_content)

            print(f"[OK] File saved as UTF-8")
            return True
        else:
            print(f"[WARN] Decoded content doesn't contain expected Chinese characters")
            return False

    except UnicodeDecodeError as e:
        print(f"[ERROR] UTF-8 decode failed: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        return False

def fix_damaged_utf8(file_path):
    """
    尝试修复已损坏的UTF-8文件
    通过替换损坏的字符或从备份恢复
    """
    print(f"[INFO] Processing damaged file: {file_path}")

    try:
        # 尝试读取，忽略错误
        with open(file_path, 'rb') as f:
            raw_bytes = f.read()

        # 尝试多种解码方式
        attempts = [
            ('utf-8', 'strict'),
            ('utf-8', 'ignore'),
            ('gbk', 'strict'),
            ('gb18030', 'strict'),
            ('utf-8-sig', 'strict'),
        ]

        for encoding, errors in attempts:
            try:
                content = raw_bytes.decode(encoding, errors=errors)
                if '项目' in content or 'AI Agent' in content:
                    print(f"[OK] Successfully decoded with {encoding} (errors={errors})")

                    # 保存为UTF-8
                    with open(file_path, 'w', encoding='utf-8', newline='\n') as f:
                        f.write(content)

                    print(f"[OK] File saved as UTF-8")
                    return True
            except:
                continue

        print(f"[ERROR] Could not decode file with any encoding")
        return False

    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        return False

if __name__ == '__main__':
    import os

    base_dir = r'E:\Study\wqaetly\ai_agent_for_skill'

    print("=" * 60)
    print("Starting encoding fix - V2")
    print("=" * 60)
    print()

    # 修复 PROJECT_SUMMARY.md（UTF-8被误读为Latin1）
    project_summary_path = os.path.join(base_dir, 'PROJECT_SUMMARY.md')
    print(f"[1/2] Fixing PROJECT_SUMMARY.md")
    print("-" * 60)
    if fix_utf8_misread_as_latin1(project_summary_path):
        print("[SUCCESS] PROJECT_SUMMARY.md fixed\n")
    else:
        print("[FAILED] PROJECT_SUMMARY.md fix failed\n")

    # 修复 README.md（UTF-8损坏）
    readme_path = os.path.join(base_dir, 'README.md')
    print(f"[2/2] Fixing README.md")
    print("-" * 60)
    if fix_damaged_utf8(readme_path):
        print("[SUCCESS] README.md fixed\n")
    else:
        print("[FAILED] README.md fix failed\n")

    print("=" * 60)
    print("Encoding fix completed")
    print("=" * 60)
