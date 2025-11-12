#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量修复 skill_agent 目录下的 MD 文件编码问题 (改进版)
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
    # 检查 Unicode 替换字符 (U+FFFD)
    has_replacement_char = '\ufffd' in content

    # 检查双重编码特征
    has_double_encoding = any(pattern in content for pattern in [
        'é¡¹ç®',  # 项目
        'æè½',    # 技能
        'ç³»ç»',  # 系统
        'éç½®',  # 配置
    ])

    # 检查丢失字符（问号后面跟着中文）
    has_missing_chars = bool(re.search(r'\?[\u4e00-\u9fff]', content))

    return has_replacement_char or has_double_encoding or has_missing_chars

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

def fix_replacement_chars(content):
    """修复 Unicode 替换字符 (U+FFFD)"""
    # 常见的替换字符模式及其对应的正确字符
    replacements = [
        # 单个替换字符
        ('简�?', '简介'),
        ('系�?', '系统'),
        ('配�?', '配置'),
        ('程�?', '程序'),
        ('浏览�?', '浏览器'),
        ('服务�?', '服务器'),
        ('快速开�?', '快速开始'),
        ('功能特�?', '功能特性'),
        ('核心价�?', '核心价值'),
        ('知识�?', '知识库'),
        ('保持最�?', '保持最新'),
        ('超�?', '超过'),
        ('调�?', '调整'),
        ('培�?', '培训'),
        ('模�?', '模式'),
        ('一键启�?', '一键启动'),
        ('访�?', '访问'),
        ('�?', '✓'),  # 勾选符号
        ('引擎�?', '引擎'),
        ('流�?', '流程'),
        ('节�?', '节点'),
        ('工�?', '工具'),
        ('架�?', '架构'),
        ('生�?', '生成'),
        ('参�?', '参考'),
        ('赋�?', '赋能'),
        ('体�?', '体验'),
        ('同�?', '同步'),
        ('结�?', '结构'),
        ('创�?', '创新'),
        ('检�?', '检索'),
        ('索�?', '索引'),
        ('最�?', '最新'),
        ('修�?', '修复'),
        ('构�?', '构建'),
        ('通�?', '通过'),
        ('理�?', '理解'),
        ('式�?', '式'),

        # 多个连续替换字符
        ('�?�?', '和'),
        ('�?�?�?', ''),

        # 句首的替换字符通常是列表符号或标题符号
        (r'^�?', '•', re.MULTILINE),
        (r'\n�?', '\n•'),

        # Emoji 相关
        ('🔥�?', '🔥 '),
        ('📚�?', '📚 '),
        ('💡�?', '💡 '),
        ('🎯�?', '🎯 '),
        ('🌟�?', '🌟 '),
        ('🚀�?', '🚀 '),
    ]

    for pattern, replacement, *flags in replacements:
        if flags:
            content = re.sub(pattern, replacement, content, flags=flags[0])
        else:
            content = content.replace(pattern, replacement)

    # 移除孤立的替换字符（前后都是空格或标点）
    content = re.sub(r'(?<=\s)�(?=\s)', '', content)
    content = re.sub(r'(?<=\s)�(?=[。，、；：！？])', '', content)

    return content

def fix_markdown_file(file_path):
    """修复单个 MD 文件"""
    rel_path = file_path.relative_to(Path(r"E:\Study\wqaetly\ai_agent_for_skill\skill_agent"))
    print(f"\n处理: {rel_path}")

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

        # 显示问题统计
        replacement_count = content.count('\ufffd')
        double_encoding = 'é¡¹ç®' in content or 'æè½' in content

        print(f"  [INFO] 替换字符数: {replacement_count}")
        if double_encoding:
            print(f"  [INFO] 检测到双重编码")

        # 备份原文件
        backup_path = str(file_path) + '.backup'
        shutil.copy2(file_path, backup_path)

        original_content = content

        # 检查双重编码
        if double_encoding:
            print("  [INFO] 修复双重编码...")
            content = fix_double_encoding(content)

        # 修复替换字符
        print("  [INFO] 修复替换字符...")
        content = fix_replacement_chars(content)

        # 如果没有变化，跳过
        if content == original_content:
            print("  [SKIP] 修复后无变化")
            os.remove(backup_path)
            return False

        # 保存修复后的文件
        with open(file_path, 'w', encoding='utf-8', newline='\n') as f:
            f.write(content)

        # 统计修复效果
        remaining_replacement = content.count('\ufffd')
        chinese_count = sum(1 for char in content if '\u4e00' <= char <= '\u9fff')

        print(f"  [OK] 修复完成")
        print(f"    - 中文字符: {chinese_count}")
        print(f"    - 剩余替换字符: {remaining_replacement}")
        print(f"    - 备份: {backup_path.split('\\')[-1]}")

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
    print("批量修复 skill_agent MD 文件编码 (改进版)")
    print("=" * 70)
    print(f"\n找到 {len(md_files)} 个 MD 文件\n")

    # 批量修复
    success_count = 0
    for md_file in md_files:
        if fix_markdown_file(md_file):
            success_count += 1

    print("\n" + "=" * 70)
    print(f"修复结果: {success_count}/{len(md_files)} 个文件已修复")
    print("=" * 70)

    if success_count > 0:
        print("\n操作建议:")
        print("1. 用文本编辑器检查修复后的文件")
        print("2. 如果正常，删除 .backup 备份文件")
        print("3. 如果异常，从 .backup 恢复")
    else:
        print("\n所有文件均无编码问题！")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n[FATAL ERROR] {e}")
        import traceback
        traceback.print_exc()
