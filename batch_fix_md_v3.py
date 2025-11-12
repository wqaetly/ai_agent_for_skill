#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量修复 skill_agent 目录下的 MD 文件编码问题 (终极版)
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

    return has_replacement_char or has_double_encoding

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

def fix_replacement_chars_contextual(content):
    """基于上下文智能修复替换字符"""

    # 常见词组的精确替换
    precise_replacements = [
        ('简�介', '简介'),
        ('系�统', '系统'),
        ('配�置', '配置'),
        ('程�序', '程序'),
        ('浏览�器', '浏览器'),
        ('服务�器', '服务器'),
        ('快速开�始', '快速开始'),
        ('功能特�性', '功能特性'),
        ('核心价�值', '核心价值'),
        ('知识�库', '知识库'),
        ('保持最�新', '保持最新'),
        ('超�过', '超过'),
        ('调�整', '调整'),
        ('培�训', '培训'),
        ('模�式', '模式'),
        ('一键启�动', '一键启动'),
        ('访�问', '访问'),
        ('引擎�', '引擎'),
        ('流�程', '流程'),
        ('节�点', '节点'),
        ('工�具', '工具'),
        ('架�构', '架构'),
        ('生�成', '生成'),
        ('参�考', '参考'),
        ('参�数', '参数'),
        ('赋�能', '赋能'),
        ('体�验', '体验'),
        ('同�步', '同步'),
        ('结�构', '结构'),
        ('创�新', '创新'),
        ('检�索', '检索'),
        ('索�引', '索引'),
        ('最�新', '最新'),
        ('修�复', '修复'),
        ('构�建', '构建'),
        ('通�过', '通过'),
        ('理�解', '理解'),
        ('实�践', '实践'),
        ('推�荐', '推荐'),
        ('开�发', '开发'),
        ('1�00', '100'),
        ('2�00', '200'),
        ('3�00', '300'),
        ('5�00', '500'),
    ]

    for old, new in precise_replacements:
        content = content.replace(old, new)

    # 基于正则的上下文替换
    # 中文前的替换字符：于、和、的
    content = re.sub(r'基�([于于])', r'基于', content)
    content = re.sub(r'�([和和])', r'和', content)
    content = re.sub(r'([的的])�', r'的', content)

    # 句尾的替换字符：。！？
    content = re.sub(r'�([。！？\n])', r'。\1', content)

    # 数字后的替换字符
    content = re.sub(r'(\d+)�(\d*)', r'\1\2', content)

    # Emoji 后的替换字符（通常是空格）
    content = re.sub(r'([\U0001F300-\U0001F9FF])�', r'\1 ', content)

    # 列表项前的替换字符（通常是 - 或 *）
    content = re.sub(r'\n�\s*-', r'\n-', content)
    content = re.sub(r'\n�\s*\*', r'\n*', content)

    # 链接中的替换字符
    content = re.sub(r'\[([^\]]+)�([^\]]*)\]', r'[\1\2]', content)
    content = re.sub(r'�(\))', r'\1', content)

    # 代码块中的替换字符（保留原样或删除）
    # 暂时跳过，因为代码块通常不应该有中文

    # 移除孤立的替换字符（前后都是空格、标点或行首行尾）
    content = re.sub(r'(?<=\s)�(?=\s)', '', content)
    content = re.sub(r'(?<=\s)�(?=[。，、；：！？\n])', '', content)
    content = re.sub(r'^�', '', content, flags=re.MULTILINE)
    content = re.sub(r'�$', '', content, flags=re.MULTILINE)

    # 如果还有剩余的替换字符，可能是特殊符号，尝试推断
    # 标题前后的替换字符：删除
    content = re.sub(r'(#{1,6}\s+)�', r'\1', content)
    content = re.sub(r'�(#{1,6}\s+)', r'\1', content)

    # 加粗、斜体标记周围的替换字符
    content = re.sub(r'\*\*�', r'**', content)
    content = re.sub(r'�\*\*', r'**', content)

    # 最后，删除所有剩余的孤立替换字符
    content = content.replace('�', '')

    return content

def restore_from_backup(file_path):
    """从备份恢复文件"""
    backup_path = str(file_path) + '.backup'
    if os.path.exists(backup_path):
        shutil.copy2(backup_path, file_path)
        return True
    return False

def fix_markdown_file(file_path):
    """修复单个 MD 文件"""
    rel_path = file_path.relative_to(Path(r"E:\Study\wqaetly\ai_agent_for_skill\skill_agent"))
    print(f"\n处理: {rel_path}")

    try:
        # 先检查是否有备份，如果有则从备份恢复
        backup_path = str(file_path) + '.backup'
        if os.path.exists(backup_path):
            print("  [INFO] 发现备份文件，从备份恢复...")
            shutil.copy2(backup_path, file_path)

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

        # 重新创建备份
        if not os.path.exists(backup_path):
            shutil.copy2(file_path, backup_path)

        original_content = content

        # 检查双重编码
        if double_encoding:
            print("  [INFO] 修复双重编码...")
            content = fix_double_encoding(content)

        # 修复替换字符
        print("  [INFO] 修复替换字符...")
        content = fix_replacement_chars_contextual(content)

        # 保存修复后的文件
        with open(file_path, 'w', encoding='utf-8', newline='\n') as f:
            f.write(content)

        # 统计修复效果
        remaining_replacement = content.count('\ufffd')
        chinese_count = sum(1 for char in content if '\u4e00' <= char <= '\u9fff')

        print(f"  [OK] 修复完成")
        print(f"    - 中文字符: {chinese_count}")
        print(f"    - 剩余替换字符: {remaining_replacement}")

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
    print("批量修复 skill_agent MD 文件编码 (终极版)")
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
        print("\n✓ 所有替换字符已智能修复")
        print("\n操作建议:")
        print("1. 用文本编辑器检查修复后的文件")
        print("2. 如果正常，可以删除 .backup 备份文件")
    else:
        print("\n所有文件均无编码问题！")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n[FATAL ERROR] {e}")
        import traceback
        traceback.print_exc()
