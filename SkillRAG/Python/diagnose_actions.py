"""
诊断Action描述质量
检查所有Action JSON文件的description和searchText字段
"""

import os
import json
from pathlib import Path

def diagnose_actions(actions_dir: str = "../Data/Actions"):
    """诊断Action描述质量"""

    if not os.path.exists(actions_dir):
        print(f"❌ Actions目录不存在: {actions_dir}")
        return

    print("=" * 80)
    print("Action描述质量诊断报告")
    print("=" * 80)

    # 统计
    total_actions = 0
    empty_description = []
    short_description = []
    empty_searchtext = []
    short_searchtext = []
    good_actions = []

    # 扫描所有JSON文件
    for filename in sorted(os.listdir(actions_dir)):
        if not filename.endswith('.json') or filename.startswith('EXAMPLE'):
            continue

        filepath = os.path.join(actions_dir, filename)
        total_actions += 1

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            action = data.get('action', {})
            type_name = action.get('typeName', 'Unknown')
            description = action.get('description', '')
            search_text = action.get('searchText', '')

            # 检查description
            desc_status = "✅"
            desc_len = len(description)

            if not description or description.strip() == "":
                empty_description.append(type_name)
                desc_status = "❌ 空"
            elif desc_len < 20:
                short_description.append((type_name, desc_len))
                desc_status = f"⚠️ 太短({desc_len}字符)"
            else:
                desc_status = f"✅ ({desc_len}字符)"

            # 检查searchText
            search_status = "✅"
            search_len = len(search_text)

            if not search_text or search_text.strip() == "":
                empty_searchtext.append(type_name)
                search_status = "❌ 空"
            elif search_len < 50:
                short_searchtext.append((type_name, search_len))
                search_status = f"⚠️ 太短({search_len}字符)"
            else:
                search_status = f"✅ ({search_len}字符)"

            # 综合评分
            if desc_len >= 20 and search_len >= 50:
                good_actions.append(type_name)
                overall = "✅ 良好"
            else:
                overall = "❌ 需要改进"

            print(f"\n{total_actions}. {type_name}")
            print(f"   Description: {desc_status}")
            print(f"   SearchText:  {search_status}")
            print(f"   综合评分: {overall}")

            # 显示description预览
            if description:
                preview = description[:100] + "..." if len(description) > 100 else description
                print(f"   描述预览: {preview}")

        except Exception as e:
            print(f"\n❌ 错误: 无法读取 {filename}: {e}")

    # 汇总报告
    print("\n" + "=" * 80)
    print("汇总报告")
    print("=" * 80)
    print(f"\n总Action数: {total_actions}")
    print(f"✅ 良好: {len(good_actions)} ({len(good_actions)/total_actions*100:.1f}%)")
    print(f"❌ 需要改进: {total_actions - len(good_actions)} ({(total_actions - len(good_actions))/total_actions*100:.1f}%)")

    if empty_description:
        print(f"\n❌ Description为空的Action ({len(empty_description)}):")
        for name in empty_description:
            print(f"   - {name}")

    if short_description:
        print(f"\n⚠️ Description太短的Action ({len(short_description)}):")
        for name, length in short_description:
            print(f"   - {name}: {length}字符")

    if empty_searchtext:
        print(f"\n❌ SearchText为空的Action ({len(empty_searchtext)}):")
        for name in empty_searchtext:
            print(f"   - {name}")

    if short_searchtext:
        print(f"\n⚠️ SearchText太短的Action ({len(short_searchtext)}):")
        for name, length in short_searchtext:
            print(f"   - {name}: {length}字符")

    print("\n" + "=" * 80)
    print("问题诊断")
    print("=" * 80)
    print("""
🔍 RAG推荐"击飞"时推荐AudioAction的原因：

1. AudioAction的description为空，searchText只有3行简单文本
2. 向量嵌入时，短文本可能产生与查询意外匹配的向量
3. 即使语义不匹配，如果AudioAction在技能中使用频率高，usage_weight会提升其排名

💡 解决方案：

方案1（推荐）：批量修复所有Action的description
   - 为所有空description的Action填写详细功能描述
   - 确保searchText包含足够的语义信息
   - 包含关键词、使用场景、相关效果等

方案2：调整RAG算法参数
   - 提高semantic_weight（从0.6到0.8）
   - 降低usage_weight（从0.4到0.2）
   - 添加最低相似度阈值过滤（0.3以下直接过滤）

方案3：改进searchText构建逻辑
   - 如果description为空，自动从参数推断功能
   - 为每个Action添加关键词标签
   - 扩展searchText包含更多上下文信息
""")

if __name__ == "__main__":
    diagnose_actions()
