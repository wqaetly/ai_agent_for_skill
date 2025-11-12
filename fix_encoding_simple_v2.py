#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单修复 skill_agent 目录下的 MD 文件编码问题
不依赖任何外部库，仅使用 Python 内置功能
"""
import os
from pathlib import Path
import shutil

def try_decode_file(file_path):
    """尝试多种编码读取文件"""
    with open(file_path, 'rb') as f:
        raw_bytes = f.read()

    # 尝试的编码顺序
    encodings = ['utf-8', 'gbk', 'gb18030', 'cp936', 'gb2312', 'latin1']

    for encoding in encodings:
        try:
            content = raw_bytes.decode(encoding)
            # 检查是否有替换字符
            replacement_count = content.count('\ufffd')

            # 检查中文字符数量（判断解码是否正确）
            chinese_count = sum(1 for char in content if '\u4e00' <= char <= '\u9fff')

            # 如果没有替换字符且有中文，认为解码成功
            if replacement_count == 0 and chinese_count > 0:
                return content, encoding, chinese_count

        except (UnicodeDecodeError, LookupError):
            continue

    # 如果所有编码都失败，返回 None
    return None, None, 0

def fix_markdown_file(file_path):
    """修复单个 MD 文件的编码"""
    rel_path = file_path.relative_to(Path(r"E:\Study\wqaetly\ai_agent_for_skill\skill_agent"))
    print(f"\n处理: {rel_path}")

    try:
        # 尝试解码
        content, detected_encoding, chinese_count = try_decode_file(file_path)

        if content is None:
            print(f"  [ERROR] 无法解码文件")
            return False

        print(f"  [INFO] 检测到编码: {detected_encoding}")
        print(f"  [INFO] 中文字符数: {chinese_count}")

        # 如果已经是 UTF-8，跳过
        if detected_encoding == 'utf-8':
            print(f"  [SKIP] 已经是 UTF-8 编码")
            return False

        # 创建备份
        backup_path = str(file_path) + '.original'
        if not os.path.exists(backup_path):
            shutil.copy2(file_path, backup_path)
            print(f"  [INFO] 已创建备份")

        # 保存为 UTF-8
        with open(file_path, 'w', encoding='utf-8', newline='\n') as f:
            f.write(content)

        print(f"  [OK] 已转换: {detected_encoding} -> UTF-8")
        return True

    except Exception as e:
        print(f"  [ERROR] 修复失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    base_dir = Path(r"E:\Study\wqaetly\ai_agent_for_skill\skill_agent")

    # 查找所有 MD 文件
    md_files = []
    for pattern in ['*.md', 'Docs/*.md']:
        md_files.extend(base_dir.glob(pattern))

    # 过滤掉不需要处理的目录
    md_files = [f for f in md_files
                if 'venv' not in str(f)
                and 'Data\\models' not in str(f)
                and 'Data/models' not in str(f)]

    print("=" * 70)
    print("修复 skill_agent MD 文件编码")
    print("=" * 70)
    print(f"\n找到 {len(md_files)} 个 MD 文件\n")

    # 批量修复
    success_count = 0
    for md_file in md_files:
        if fix_markdown_file(md_file):
            success_count += 1

    print("\n" + "=" * 70)
    print(f"修复结果: {success_count}/{len(md_files)} 个文件已转换为 UTF-8")
    print("=" * 70)

    if success_count > 0:
        print("\n✓ 文件编码已修复")
        print("\n操作建议:")
        print("1. 检查修复后的文件内容")
        print("2. 如果正常，删除 .original 备份文件")
        print("3. 删除旧的 .backup 和 .bak 备份文件")
    else:
        print("\n所有文件编码正常！")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n[FATAL ERROR] {e}")
        import traceback
        traceback.print_exc()
