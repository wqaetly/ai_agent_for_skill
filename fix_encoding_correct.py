#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
正确修复 skill_agent 目录下的 MD 文件编码问题
问题：文件是 GBK/GB18030 编码，但需要转换为 UTF-8
"""
import os
import sys
from pathlib import Path
import shutil
import chardet

def detect_encoding(file_path):
    """检测文件编码"""
    with open(file_path, 'rb') as f:
        raw_data = f.read()
        result = chardet.detect(raw_data)
        return result['encoding'], result['confidence']

def fix_markdown_file(file_path):
    """修复单个 MD 文件的编码"""
    rel_path = file_path.relative_to(Path(r"E:\Study\wqaetly\ai_agent_for_skill\skill_agent"))
    print(f"\n处理: {rel_path}")

    try:
        # 检测当前编码
        encoding, confidence = detect_encoding(file_path)
        print(f"  [INFO] 检测到编码: {encoding} (置信度: {confidence:.2f})")

        # 读取原始文件
        with open(file_path, 'rb') as f:
            raw_bytes = f.read()

        # 尝试用检测到的编码解码
        content = None
        tried_encodings = [encoding, 'gbk', 'gb18030', 'utf-8', 'cp936']

        for enc in tried_encodings:
            if enc is None:
                continue
            try:
                content = raw_bytes.decode(enc)
                # 检查是否有替换字符
                if '\ufffd' not in content:
                    print(f"  [OK] 成功使用 {enc} 解码")
                    actual_encoding = enc
                    break
            except:
                continue

        if content is None or '\ufffd' in content:
            print(f"  [SKIP] 无法找到正确的编码")
            return False

        # 检查是否已经是 UTF-8
        if actual_encoding.lower() in ['utf-8', 'utf8', 'ascii']:
            print(f"  [SKIP] 已经是 UTF-8 编码")
            return False

        # 创建备份
        backup_path = str(file_path) + '.bak'
        if not os.path.exists(backup_path):
            shutil.copy2(file_path, backup_path)
            print(f"  [INFO] 已创建备份: {backup_path}")

        # 保存为 UTF-8
        with open(file_path, 'w', encoding='utf-8', newline='\n') as f:
            f.write(content)

        # 统计中文字符
        chinese_count = sum(1 for char in content if '\u4e00' <= char <= '\u9fff')
        print(f"  [OK] 已转换为 UTF-8")
        print(f"    - 中文字符数: {chinese_count}")
        print(f"    - 文件大小: {len(content)} 字符")

        return True

    except Exception as e:
        print(f"  [ERROR] 修复失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    base_dir = Path(r"E:\Study\wqaetly\ai_agent_for_skill\skill_agent")

    # 查找所有 MD 文件（排除 venv 和 Data/models 目录）
    md_files = []
    for pattern in ['*.md', 'Docs/*.md']:
        md_files.extend(base_dir.glob(pattern))

    # 过滤掉不需要处理的目录
    md_files = [f for f in md_files
                if 'venv' not in str(f)
                and 'Data\\models' not in str(f)
                and 'Data/models' not in str(f)]

    print("=" * 70)
    print("修复 skill_agent MD 文件编码 (GBK -> UTF-8)")
    print("=" * 70)
    print(f"\n找到 {len(md_files)} 个 MD 文件\n")

    # 批量修复
    success_count = 0
    for md_file in md_files:
        if fix_markdown_file(md_file):
            success_count += 1

    print("\n" + "=" * 70)
    print(f"修复结果: {success_count}/{len(md_files)} 个文件已转换")
    print("=" * 70)

    if success_count > 0:
        print("\n✓ 所有文件已转换为 UTF-8 编码")
        print("\n操作建议:")
        print("1. 用文本编辑器检查修复后的文件")
        print("2. 如果正常，可以删除 .bak 备份文件")
        print("3. 可以删除旧的 .backup 备份文件")
    else:
        print("\n所有文件编码正常或无需转换！")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n[FATAL ERROR] {e}")
        import traceback
        traceback.print_exc()
