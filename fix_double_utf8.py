#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复双重UTF-8编码问题
问题：文件的 UTF-8 字节被当作 latin1 字符保存
解决：latin1读取 -> 转换为字节 -> UTF-8解码
"""
import sys
from pathlib import Path
import shutil

# 强制 UTF-8 输出
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def fix_double_utf8_encoding(file_path):
    """修复双重UTF-8编码的文件"""
    rel_path = file_path.relative_to(Path(r"E:\Study\wqaetly\ai_agent_for_skill\skill_agent"))
    print(f"\n处理: {rel_path}")

    try:
        # 读取文件
        with open(file_path, 'rb') as f:
            raw_bytes = f.read()

        # 先用 latin1 解码（这样每个字节都能读出来）
        try:
            content_latin1 = raw_bytes.decode('latin1')
        except:
            print("  [ERROR] 无法用 latin1 解码")
            return False

        # 检查是否是双重编码（特征：latin1解码后有类似 æºè½ 的字符）
        double_encoding_markers = ['æ', 'è', 'ä', 'ã', 'é', 'ï']
        has_double_encoding = any(marker in content_latin1[:500] for marker in double_encoding_markers)

        if not has_double_encoding:
            print("  [SKIP] 没有双重编码特征")
            return False

        # 将 latin1 字符串的每个字符的码点当作字节
        try:
            # 这一步的关键：latin1 字符的码点值就是原始的 UTF-8 字节值
            utf8_bytes = bytes(ord(c) for c in content_latin1)
            # 用 UTF-8 解码
            content_utf8 = utf8_bytes.decode('utf-8', errors='replace')
        except Exception as e:
            print(f"  [ERROR] UTF-8 解码失败: {e}")
            return False

        # 检查修复效果
        chinese_count = sum(1 for c in content_utf8 if '\u4e00' <= c <= '\u9fff')
        replacement_count = content_utf8.count('\ufffd')

        print(f"  [INFO] 中文字符: {chinese_count}")
        print(f"  [INFO] 替换字符: {replacement_count}")

        if chinese_count == 0:
            print("  [SKIP] 修复后没有中文字符，可能不需要修复")
            return False

        # 创建备份
        backup_path = str(file_path) + '.before_fix'
        if not Path(backup_path).exists():
            shutil.copy2(file_path, backup_path)
            print("  [INFO] 已创建备份")

        # 保存修复后的文件
        with open(file_path, 'w', encoding='utf-8', newline='\n') as f:
            f.write(content_utf8)

        print("  [OK] 修复成功")
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
    print("修复 skill_agent MD 文件的双重UTF-8编码问题")
    print("=" * 70)
    print(f"\n找到 {len(md_files)} 个 MD 文件\n")

    # 批量修复
    success_count = 0
    for md_file in md_files:
        if fix_double_utf8_encoding(md_file):
            success_count += 1

    print("\n" + "=" * 70)
    print(f"修复结果: {success_count}/{len(md_files)} 个文件已修复")
    print("=" * 70)

    if success_count > 0:
        print("\n成功修复双重UTF-8编码问题！")
        print("\n操作建议:")
        print("1. 检查修复后的文件内容")
        print("2. 如果正常，删除 .before_fix 备份文件")
        print("3. 删除其他旧备份文件（.backup, .bak, .original）")
    else:
        print("\n所有文件都正常，无需修复！")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n[FATAL ERROR] {e}")
        import traceback
        traceback.print_exc()
