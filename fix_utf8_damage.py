#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复 skill_agent 目录中 UTF-8 字节序列破损的 MD 文件
"""
import os
import sys
import re
from pathlib import Path

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')


def repair_utf8_damage(raw_bytes):
    """修复破损的 UTF-8 字节序列"""

    # 常见的破损模式：三字节 UTF-8 序列的第三个字节被 ? (0x3F) 替换
    # 0xE5 0xA7 ? -> 始 (0xE5 0xA7 0x8B)
    # 0xE5 0xBC ? -> 开 (0xE5 0xBC 0x80)
    # 0xE7 0x89 ? -> 特 (0xE7 0x89 0xB9)
    # 0xE6 0x80 ? -> 性 (0xE6 0x80 0xA7)
    # 0xE6 0x9E ? -> 构 (0xE6 0x9E 0x84)
    # 0xE5 0xBA ? -> 库 (0xE5 0xBA 0x93)
    # 0xE5 0x8F ? -> 发 (0xE5 0x8F 0x91)
    # 0xE5 0xBC ? -> 式 (0xE5 0xBC 0x8F)
    # 0xE7 0xAE ? -> 简 (0xE7 0xAE 0x80), 介 (0xE7 0xAE 0x80/0xE4 0xBB 0x8B)
    # 0xE4 0xBA ? -> 于 (0xE4 0xBA 0x8E)
    # 0xE5 0x80 ? -> 值 (0xE5 0x80 0xBC)
    # 0xE6 0x96 ? -> 新 (0xE6 0x96 0xB0)
    # 0xE6 0x95 ? -> 整 (0xE6 0x95 0xB4)
    # 0xE7 0xBB ? -> 统 (0xE7 0xBB 0x9F), 构 (0xE7 0xBB 0x93)
    # 0xE8 0xAE ? -> 训 (0xE8 0xAE 0xAD), 访 (0xE8 0xAE 0xBF)
    # 0xE6 0x93 ? -> 擎 (0xE6 0x93 0x8E)
    # 0xE7 0x94 ? -> 用 (0xE7 0x94 0xA8), 生 (0xE7 0x94 0x9F)
    # 0xE8 0x80 ? -> 过 (0xE8 0x80 0x83)
    # 0xE6 0xB5 ? -> 流 (0xE6 0xB5 0x81), 测 (0xE6 0xB5 0x8B)
    # 0xE7 0x82 ? -> 点 (0xE7 0x82 0xB9)
    # 0xE5 0xB7 ? -> 工 (0xE5 0xB7 0xA5)
    # 0xE8 0xB5 ? -> 能 (0xE8 0xB5 0x84)
    # 0xE4 0xBB ? -> 介 (0xE4 0xBB 0x8B)
    # 0xE5 0x88 ? -> 到 (0xE5 0x88 0xB0), 别 (0xE5 0x88 0xAB)
    # 0xE6 0x9F ? -> 查 (0xE6 0x9F 0xA5)
    # 0xE8 0xAF ? -> 询 (0xE8 0xAF 0xA2), 话 (0xE8 0xAF 0x9D), 语 (0xE8 0xAF 0xAD)
    # 0xE9 0x85 ? -> 配 (0xE9 0x85 0x8D)
    # 0xE7 0xA8 ? -> 程 (0xE7 0xA8 0x8B)
    # 0xE9 0xA1 ? -> 项 (0xE9 0xA1 0xB9)
    # 0xE6 0x8C ? -> 指 (0xE6 0x8C 0x87)
    # 0xE6 0x93 ? -> 操 (0xE6 0x93 0x8D), 据 (0xE6 0x8D 0xAE)
    # 0xE8 0xBE ? -> 输 (0xE8 0xBE 0x93)
    # 0xE5 0x85 ? -> 入 (0xE5 0x85 0xA5)
    # 0xE5 0xAF ? -> 对 (0xE5 0xAF 0xB9)
    # 0xE5 0xBA ? -> 应 (0xE5 0xBA 0x94)
    # 0xE8 0xB0 ? -> 调 (0xE8 0xB0 0x83)
    # 0xE6 0xA8 ? -> 模 (0xE6 0xA8 0xA1)
    # 0xE7 0xB1 ? -> 类 (0xE7 0xB1 0xBB)
    # 0xE5 0xA4 ? -> 复 (0xE5 0xA4 0x8D), 处 (0xE5 0xA4 0x84)
    # 0xE4 0xBD ? -> 体 (0xE4 0xBD 0x93), 例 (0xE4 0xBE 0x8B)
    # 0xE9 0x80 ? -> 过 (0xE9 0x80 0x9A)
    # 0xE8 0xA1 ? -> 表 (0xE8 0xA1 0xA8)
    # 0xE7 0x8E ? -> 现 (0xE7 0x8E 0xB0)
    # 0xE6 0x8D ? -> 据 (0xE6 0x8D 0xAE)
    # 0xE5 0x90 ? -> 名 (0xE5 0x90 0x8D), 启 (0xE5 0x90 0xAF)

    # 标点符号的破损模式
    # 0xE2 0x80 0x9C = "
    # 0xE2 0x80 0x9D = "
    # 0xE2 0x80 0x94 = —
    # 0xE2 0x80 0x93 = –
    # 0xE2 0x80 0xA6 = …

    # 创建修复映射表（基于常见汉字）
    repair_map = {
        b'\xe5\xa7?': b'\xe5\xa7\x8b',  # 始
        b'\xe5\xbc?': b'\xe5\xbc\x80',  # 开
        b'\xe7\x89?': b'\xe7\x89\xb9',  # 特
        b'\xe6\x80?': b'\xe6\x80\xa7',  # 性
        b'\xe6\x9e?': b'\xe6\x9e\x84',  # 构
        b'\xe5\xba?': b'\xe5\xba\x93',  # 库
        b'\xe5\x8f?': b'\xe5\x8f\x91',  # 发
        b'\xe7\xae?': b'\xe7\xae\x80',  # 简
        b'\xe4\xbb?': b'\xe4\xbb\x8b',  # 介
        b'\xe4\xba?': b'\xe4\xba\x8e',  # 于
        b'\xe5\x80?': b'\xe5\x80\xbc',  # 值
        b'\xe6\x96?': b'\xe6\x96\xb0',  # 新
        b'\xe6\x95?': b'\xe6\x95\xb4',  # 整
        b'\xe7\xbb?': b'\xe7\xbb\x9f',  # 统
        b'\xe8\xae?': b'\xe8\xae\xad',  # 训
        b'\xe6\x93?': b'\xe6\x93\x8e',  # 擎
        b'\xe7\x94?': b'\xe7\x94\x9f',  # 生
        b'\xe8\x80?': b'\xe8\x80\x83',  # 考
        b'\xe6\xb5?': b'\xe6\xb5\x8b',  # 测
        b'\xe7\x82?': b'\xe7\x82\xb9',  # 点
        b'\xe5\xb7?': b'\xe5\xb7\xa5',  # 工
        b'\xe8\xb5?': b'\xe8\xb5\x84',  # 资
        b'\xe5\x88?': b'\xe5\x88\xb0',  # 到
        b'\xe6\x9f?': b'\xe6\x9f\xa5',  # 查
        b'\xe8\xaf?': b'\xe8\xaf\xa2',  # 询
        b'\xe9\x85?': b'\xe9\x85\x8d',  # 配
        b'\xe7\xa8?': b'\xe7\xa8\x8b',  # 程
        b'\xe9\xa1?': b'\xe9\xa1\xb9',  # 项
        b'\xe6\x8c?': b'\xe6\x8c\x87',  # 指
        b'\xe6\x8d?': b'\xe6\x8d\xae',  # 据
        b'\xe8\xbe?': b'\xe8\xbe\x93',  # 输
        b'\xe5\x85?': b'\xe5\x85\xa5',  # 入
        b'\xe5\xaf?': b'\xe5\xaf\xb9',  # 对
        b'\xe5\xba?': b'\xe5\xba\x94',  # 应
        b'\xe8\xb0?': b'\xe8\xb0\x83',  # 调
        b'\xe6\xa8?': b'\xe6\xa8\xa1',  # 模
        b'\xe7\xb1?': b'\xe7\xb1\xbb',  # 类
        b'\xe5\xa4?': b'\xe5\xa4\x8d',  # 复
        b'\xe4\xbd?': b'\xe4\xbd\x93',  # 体
        b'\xe9\x80?': b'\xe9\x80\x9a',  # 通
        b'\xe8\xa1?': b'\xe8\xa1\xa8',  # 表
        b'\xe7\x8e?': b'\xe7\x8e\xb0',  # 现
        b'\xe5\x90?': b'\xe5\x90\xaf',  # 启

        # 标点符号
        b'\xe2\x80?': b'\xe2\x80\x9c',  # " (默认用左引号)
    }

    # 执行修复
    result = raw_bytes
    for broken, fixed in repair_map.items():
        result = result.replace(broken, fixed)

    # 通用修复：对于任何 \xE? \x?? ? 模式，尝试智能推断
    # 这是一个更保守的方法，只修复明确的模式

    return result


def fix_file(file_path):
    """修复单个文件"""
    rel_path = file_path.relative_to(Path(r"E:\Study\wqaetly\ai_agent_for_skill\skill_agent"))
    print(f"\n处理: {rel_path}")

    try:
        # 读取原始字节
        with open(file_path, 'rb') as f:
            raw_bytes = f.read()

        # 检查是否有破损的 UTF-8 序列（三字节序列 + ?）
        damage_pattern = re.compile(rb'[\xe0-\xef][\x80-\xbf]\?')
        matches = damage_pattern.findall(raw_bytes)

        if not matches:
            print("  [SKIP] 无 UTF-8 破损")
            return False

        print(f"  [INFO] 发现 {len(matches)} 处 UTF-8 破损")

        # 创建备份（如果不存在）
        backup_path = str(file_path) + '.backup2'
        if not os.path.exists(backup_path):
            with open(backup_path, 'wb') as f:
                f.write(raw_bytes)
            print(f"  [OK] 备份创建: {backup_path}")

        # 修复
        repaired = repair_utf8_damage(raw_bytes)

        # 验证修复后的内容可以正确解码
        try:
            decoded = repaired.decode('utf-8')

            # 检查是否还有替换字符
            replacement_count = decoded.count('\ufffd')
            chinese_count = sum(1 for c in decoded if '\u4e00' <= c <= '\u9fff')

            # 保存
            with open(file_path, 'wb') as f:
                f.write(repaired)

            print(f"  [OK] 修复完成")
            print(f"    - 中文字符: {chinese_count}")
            print(f"    - 替换字符: {replacement_count}")

            return True

        except UnicodeDecodeError as e:
            print(f"  [ERROR] 修复后仍无法解码: {e}")
            return False

    except Exception as e:
        print(f"  [ERROR] 处理失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    base_dir = Path(r"E:\Study\wqaetly\ai_agent_for_skill\skill_agent")

    # 查找所有 MD 文件
    md_files = []
    for pattern in ['*.md', 'Docs/*.md']:
        md_files.extend(base_dir.glob(pattern))

    # 过滤掉 venv 和 Data 目录
    md_files = [f for f in md_files if 'venv' not in str(f) and 'Data' not in str(f)]

    print("=" * 70)
    print("修复 UTF-8 字节序列破损")
    print("=" * 70)
    print(f"\n找到 {len(md_files)} 个 MD 文件\n")

    success_count = 0
    for md_file in md_files:
        if fix_file(md_file):
            success_count += 1

    print("\n" + "=" * 70)
    print(f"修复结果: {success_count}/{len(md_files)} 个文件已修复")
    print("=" * 70)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n[FATAL ERROR] {e}")
        import traceback
        traceback.print_exc()