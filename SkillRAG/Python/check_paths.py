"""
路径配置验证脚本
检查config.yaml中的所有路径是否正确配置
"""

import os
import sys
import yaml


def check_path(name: str, path: str, should_exist: bool = True) -> bool:
    """
    检查单个路径

    Args:
        name: 路径名称
        path: 路径
        should_exist: 是否应该存在

    Returns:
        是否通过检查
    """
    abs_path = os.path.abspath(path)
    exists = os.path.exists(abs_path)

    status = "[OK]" if (exists == should_exist) else "[FAIL]"
    exist_str = "exists" if exists else "not exists"

    print(f"{status} {name}")
    print(f"   Config path: {path}")
    print(f"   Absolute path: {abs_path}")
    print(f"   Status: {exist_str}")

    if not exists and should_exist:
        print(f"   WARNING: Path does not exist! Please check config or create directory")

    print()

    return exists == should_exist


def main():
    """主函数"""
    print("=" * 70)
    print("SkillRAG Path Configuration Check")
    print("=" * 70)
    print()

    # 检查工作目录
    cwd = os.getcwd()
    print(f"Current directory: {cwd}")

    if not cwd.endswith("Python"):
        print("WARNING: Current directory is not SkillRAG/Python/")
        print("   Recommended: cd SkillRAG/Python")
        print()

    # 加载配置
    config_path = "config.yaml"
    if not os.path.exists(config_path):
        print(f"[FAIL] Config file not found: {config_path}")
        print("   Please make sure to run this script in SkillRAG/Python/ directory")
        sys.exit(1)

    print(f"[OK] Config file found: {config_path}")
    print()

    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    print("=" * 70)
    print("Checking Configuration Paths")
    print("=" * 70)
    print()

    all_passed = True

    # 1. 检查嵌入模型路径
    model_path = config['embedding']['model_name']
    all_passed &= check_path(
        "嵌入模型目录",
        model_path,
        should_exist=False  # 模型可能还未下载
    )

    # 2. 检查向量数据库目录
    vector_db_path = config['vector_store']['persist_directory']
    all_passed &= check_path(
        "向量数据库目录",
        vector_db_path,
        should_exist=False  # 首次运行时不存在
    )

    # 3. 检查技能目录
    skills_dir = config['skill_indexer']['skills_directory']
    all_passed &= check_path(
        "技能JSON目录",
        skills_dir,
        should_exist=True
    )

    # 4. 检查技能索引缓存
    skill_cache = config['skill_indexer']['index_cache']
    check_path(
        "技能索引缓存",
        skill_cache,
        should_exist=False  # 首次运行时不存在
    )

    # 5. 检查Action目录
    actions_dir = config['action_indexer']['actions_directory']
    all_passed &= check_path(
        "Action JSON目录",
        actions_dir,
        should_exist=True
    )

    # 6. 检查Action索引缓存
    action_cache = config['action_indexer']['action_index_cache']
    check_path(
        "Action索引缓存",
        action_cache,
        should_exist=False  # 首次运行时不存在
    )

    # 7. 检查日志文件路径
    log_file = config['logging']['file']
    log_dir = os.path.dirname(log_file)
    check_path(
        "日志文件目录",
        log_dir,
        should_exist=False  # 会自动创建
    )

    # 8. 检查Data目录
    data_dir = "../Data"
    all_passed &= check_path(
        "Data根目录",
        data_dir,
        should_exist=True
    )

    # 统计结果
    print("=" * 70)
    print("Check Results")
    print("=" * 70)
    print()

    if all_passed:
        print("[OK] All key paths are configured correctly!")
        print()
        print("You can start using:")
        print("  python server.py              # Start RAG server")
        print("  python build_action_index.py  # Build Action index")
    else:
        print("[FAIL] Some paths are not configured correctly, please check errors above")
        print()
        print("Common issues:")
        print("  1. Make sure to run in SkillRAG/Python/ directory")
        print("  2. Check project directory structure")
        print("  3. Export skills and actions in Unity")

    print()
    print("=" * 70)

    # 额外检查：统计文件数量
    print()
    print("File Statistics:")
    print("-" * 70)

    try:
        skills_dir_abs = os.path.abspath(skills_dir)
        if os.path.exists(skills_dir_abs):
            skill_files = [f for f in os.listdir(skills_dir_abs) if f.endswith('.json')]
            print(f"Skill files: {len(skill_files)}")
        else:
            print(f"Skill files: directory not exists")
    except Exception as e:
        print(f"Skill files: cannot read ({e})")

    try:
        actions_dir_abs = os.path.abspath(actions_dir)
        if os.path.exists(actions_dir_abs):
            action_files = [f for f in os.listdir(actions_dir_abs) if f.endswith('.json')]
            print(f"Action files: {len(action_files)}")
        else:
            print(f"Action files: directory not exists")
    except Exception as e:
        print(f"Action files: cannot read ({e})")

    print("=" * 70)


if __name__ == "__main__":
    main()
