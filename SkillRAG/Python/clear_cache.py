"""
清理损坏的缓存目录
"""
import os
import shutil

cache_dir = r"E:\Study\wqaetly\ai_agent_for_skill\SkillRAG\Data\embeddings_cache"

if os.path.exists(cache_dir):
    print(f"Removing corrupted cache: {cache_dir}")
    shutil.rmtree(cache_dir)
    print("Cache removed successfully")

    # 重建空目录
    os.makedirs(cache_dir, exist_ok=True)
    print("Empty cache directory created")
else:
    print("Cache directory does not exist")
