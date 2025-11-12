#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量修复 skill_agent 目录下的 MD 文件编码问题
"""
import os
import sys
import re
import shutil
from pathlib import Path

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def check_encoding_issue(content):
    """检查是否有编码问题"""
    # 检查双重编码特征
    has_double_encoding = any(pattern in content for pattern in [
        'é¡¹ç®',  # 项目
        'æè½',    # 技能
        'ç³»ç»',  # 系统
        'éç½®',  # 配置
    ])

    # 检查丢失字符
    has_missing_chars = '?' in content and any(pattern in content for pattern in [
        '系?', '配?', '程?', '器?', '介?', '值?', '构?', '索?',
    ])

    return has_double_encoding or has_missing_chars

def fix_double_encoding(content):
    """修复双重UTF-8编码"""
    try:
        # 将字符的 unicode 码点当作字节值
        fixed_bytes = bytes(ord(c) if ord(c) < 256 else ord('?') for c in content)
        # 用 UTF-8 解码
        fixed = fixed_bytes.decode('utf-8', errors='replace')
        return fixed
    except Exception as e:
        print(f"    [WARN] 双重编码修复失败: {e}")
        return content

def fix_missing_chars(content):
    """修复丢失的字符"""
    # 基于上下文的正则表达式替换
    fixes = [
        # 常见的丢失字符模式
        (r'系\?', '系统'),
        (r'配\?', '配置'),
        (r'程\?', '程序'),
        (r'器\?', '器'),
        (r'介\?', '介'),
        (r'值\?', '值'),
        (r'构\?', '构'),
        (r'索\?', '索'),
        (r'览\?', '览器'),
        (r'索引擎', '索引擎'),
        (r'基\?', '基于'),
        (r'简\?', '简介'),
        (r'架\?', '架构'),
        (r'服务\?', '服务器'),
        (r'模\?', '模块'),
        (r'流\?', '流程'),
        (r'节\?', '节点'),
        (r'工具\?', '工具'),
        (r'引擎\?', '引擎'),
        (r'生\?', '生成'),
        (r'参\?', '参考'),
        (r'最\?次', '最多3次'),
        (r'最\?', '最多'),
        (r'快速开\?', '快速开始'),
        (r'技术架\?', '技术架构'),
        (r'项目简\?', '项目简介'),
        (r'核心价\?', '核心价值'),
        (r'赋\?', '赋能'),
        (r'体\?', '体验'),
        (r'同\?', '同步'),
        (r'结\?', '结构'),
        (r'创\?', '创新'),
        (r'检\?', '检索'),
        # 修复替换字符
        (r'�\?', ''),  # 移除单独的替换字符
    ]

    for pattern, replacement in fixes:
        content = re.sub(pattern, replacement, content)

    return content

def fix_markdown_file(file_path):
    """修复单个 MD 文件"""
    print(f"\n处理: {file_path}")

    try:
        # 读取原始文件
        with open(file_path, 'rb') as f:
            raw_bytes = f.read()

        # UTF-8 解码
        content = raw_bytes.decode('utf-8', errors='replace')

        # 检查是否需要修复
        if not check_encoding_issue(content):
            print("  [SKIP] 无需修复")
            return False

        # 备份原文件
        backup_path = str(file_path) + '.backup'
        shutil.copy2(file_path, backup_path)

        original_content = content

        # 检查双重编码
        if 'é¡¹ç®' in content or 'æè½' in content or 'ç³»ç»' in content:
            print("  [INFO] 检测到双重编码，修复中...")
            content = fix_double_encoding(content)

        # 修复丢失的字符
        content = fix_missing_chars(content)

        # 如果没有变化，跳过
        if content == original_content:
            print("  [SKIP] 修复后无变化")
            os.remove(backup_path)
            return False

        # 保存修复后的文件
        with open(file_path, 'w', encoding='utf-8', newline='\n') as f:
            f.write(content)

        # 统计中文字符数
        chinese_count = sum(1 for char in content if '\u4e00' <= char <= '\u9fff')

        print(f"  [OK] 修复完成 (中文字符: {chinese_count})")
        print(f"  [INFO] 备份: {backup_path}")

        return True

    except Exception as e:
        print(f"  [ERROR] 修复失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    base_dir = Path(r"E:\Study\wqaetly\ai_agent_for_skill\skill_agent")

    # 查找所有 MD 文件（排除 venv 目录）
    md_files = []
    for pattern in ['*.md', 'Docs/*.md', 'Data/**/*.md']:
        md_files.extend(base_dir.glob(pattern))

    # 过滤掉 venv 目录
    md_files = [f for f in md_files if 'venv' not in str(f)]

    print("=" * 70)
    print("批量修复 skill_agent MD 文件编码")
    print("=" * 70)
    print(f"\n找到 {len(md_files)} 个 MD 文件")

    # 显示文件列表
    for i, f in enumerate(md_files, 1):
        rel_path = f.relative_to(base_dir)
        print(f"  {i:2d}. {rel_path}")

    # 批量修复
    success_count = 0
    for md_file in md_files:
        if fix_markdown_file(md_file):
            success_count += 1

    print("\n" + "=" * 70)
    print(f"修复完成: {success_count}/{len(md_files)} 个文件已修复")
    print("=" * 70)

    if success_count > 0:
        print("\n操作建议:")
        print("1. 用文本编辑器检查修复后的文件")
        print("2. 如果正常，删除 .backup 备份文件")
        print("3. 如果异常，从 .backup 恢复")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n[FATAL ERROR] {e}")
        import traceback
        traceback.print_exc()
