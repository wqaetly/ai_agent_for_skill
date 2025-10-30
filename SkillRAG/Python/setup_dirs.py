"""
创建必要的数据目录
"""
import os

# 项目根目录
project_root = r"E:\Study\wqaetly\ai_agent_for_skill\SkillRAG"

# 需要创建的目录列表
directories = [
    os.path.join(project_root, "Data"),
    os.path.join(project_root, "Data", "embeddings_cache"),
    os.path.join(project_root, "Data", "vector_db"),
]

for directory in directories:
    os.makedirs(directory, exist_ok=True)
    print(f"Created directory: {directory}")

print("\nAll directories are ready!")
