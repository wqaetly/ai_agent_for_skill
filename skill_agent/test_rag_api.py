#!/usr/bin/env python3
"""
RAG API端点测试脚本
测试所有新增的RAG API端点是否正常工作
"""

import requests
import json
import sys
from typing import Dict, Any

# 配置
BASE_URL = "http://localhost:2024"
TIMEOUT = 30


def print_section(title: str):
    """打印章节标题"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_result(test_name: str, success: bool, details: str = ""):
    """打印测试结果"""
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status} | {test_name}")
    if details:
        print(f"       {details}")


def test_server_health() -> bool:
    """测试服务器健康检查"""
    print_section("1. 服务器健康检查")

    try:
        # 测试根端点
        response = requests.get(f"{BASE_URL}/", timeout=TIMEOUT)
        if response.status_code == 200:
            data = response.json()
            print_result("根端点", True, f"版本: {data.get('version', 'N/A')}")
        else:
            print_result("根端点", False, f"状态码: {response.status_code}")
            return False

        # 测试通用健康检查
        response = requests.get(f"{BASE_URL}/health", timeout=TIMEOUT)
        if response.status_code == 200:
            print_result("通用健康检查", True)
        else:
            print_result("通用健康检查", False, f"状态码: {response.status_code}")
            return False

        # 测试RAG健康检查
        response = requests.get(f"{BASE_URL}/rag/health", timeout=TIMEOUT)
        if response.status_code == 200:
            data = response.json()
            status = data.get('status', 'unknown')
            skills = data.get('indexed_skills', 0)
            actions = data.get('indexed_actions', 0)
            print_result(
                "RAG健康检查",
                status == "healthy",
                f"状态: {status}, 技能: {skills}, Actions: {actions}"
            )
        else:
            print_result("RAG健康检查", False, f"状态码: {response.status_code}")
            return False

        return True

    except requests.exceptions.ConnectionError:
        print_result("服务器连接", False, "无法连接到服务器，请确保langgraph_server.py正在运行")
        return False
    except Exception as e:
        print_result("服务器健康检查", False, f"异常: {str(e)}")
        return False


def test_rag_search() -> bool:
    """测试技能语义搜索"""
    print_section("2. 技能语义搜索 (/rag/search)")

    test_queries = [
        ("治疗技能", 3),
        ("AOE伤害", 5),
        ("", 1),  # 空查询
    ]

    success_count = 0

    for query, top_k in test_queries:
        try:
            payload = {"query": query, "top_k": top_k}
            response = requests.post(
                f"{BASE_URL}/rag/search",
                json=payload,
                timeout=TIMEOUT
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    result_count = data.get("count", 0)
                    print_result(
                        f"搜索'{query}'",
                        True,
                        f"找到 {result_count} 个结果"
                    )
                    success_count += 1
                else:
                    print_result(f"搜索'{query}'", False, "success=false")
            else:
                print_result(f"搜索'{query}'", False, f"状态码: {response.status_code}")

        except Exception as e:
            print_result(f"搜索'{query}'", False, f"异常: {str(e)}")

    return success_count == len(test_queries)


def test_action_recommendation() -> bool:
    """测试Action类型推荐"""
    print_section("3. Action类型推荐 (/rag/recommend-actions)")

    test_contexts = [
        ("造成伤害", 3),
        ("移动角色", 3),
        ("恢复生命值", 2),
    ]

    success_count = 0

    for context, top_k in test_contexts:
        try:
            payload = {"context": context, "top_k": top_k}
            response = requests.post(
                f"{BASE_URL}/rag/recommend-actions",
                json=payload,
                timeout=TIMEOUT
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    rec_count = data.get("count", 0)
                    recommendations = data.get("recommendations", [])
                    action_types = [r.get("action_type", "Unknown") for r in recommendations[:3]]
                    print_result(
                        f"推荐'{context}'",
                        True,
                        f"{rec_count}个推荐: {', '.join(action_types)}"
                    )
                    success_count += 1
                else:
                    print_result(f"推荐'{context}'", False, "success=false")
            else:
                print_result(f"推荐'{context}'", False, f"状态码: {response.status_code}")

        except Exception as e:
            print_result(f"推荐'{context}'", False, f"异常: {str(e)}")

    return success_count == len(test_contexts)


def test_parameter_recommendation() -> bool:
    """测试参数智能推荐"""
    print_section("4. 参数智能推荐 (/rag/recommend-parameters)")

    test_action_types = [
        "DamageAction",
        "HealAction",
        "MoveAction",
    ]

    success_count = 0

    for action_type in test_action_types:
        try:
            payload = {"action_type": action_type}
            response = requests.post(
                f"{BASE_URL}/rag/recommend-parameters",
                json=payload,
                timeout=TIMEOUT
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    param_count = data.get("count", 0)
                    print_result(
                        f"参数推荐'{action_type}'",
                        True,
                        f"找到 {param_count} 个参数示例"
                    )
                    success_count += 1
                else:
                    print_result(f"参数推荐'{action_type}'", False, "success=false")
            else:
                print_result(
                    f"参数推荐'{action_type}'",
                    False,
                    f"状态码: {response.status_code}"
                )

        except Exception as e:
            print_result(f"参数推荐'{action_type}'", False, f"异常: {str(e)}")

    return success_count == len(test_action_types)


def test_index_stats() -> bool:
    """测试索引统计信息"""
    print_section("5. 索引统计信息 (/rag/index/stats)")

    try:
        response = requests.get(f"{BASE_URL}/rag/index/stats", timeout=TIMEOUT)

        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                stats = data.get("statistics", {})
                total_skills = stats.get("total_skills", 0)
                total_actions = stats.get("total_actions", 0)
                cache_hits = stats.get("cache_hits", 0)
                print_result(
                    "获取索引统计",
                    True,
                    f"技能: {total_skills}, Actions: {total_actions}, 缓存命中: {cache_hits}"
                )
                return True
            else:
                print_result("获取索引统计", False, "success=false")
                return False
        else:
            print_result("获取索引统计", False, f"状态码: {response.status_code}")
            return False

    except Exception as e:
        print_result("获取索引统计", False, f"异常: {str(e)}")
        return False


def test_cache_clear() -> bool:
    """测试清空缓存"""
    print_section("6. 清空缓存 (/rag/cache)")

    try:
        response = requests.delete(f"{BASE_URL}/rag/cache", timeout=TIMEOUT)

        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                cleared = data.get("cleared_entries", 0)
                print_result(
                    "清空缓存",
                    True,
                    f"清空了 {cleared} 个缓存条目"
                )
                return True
            else:
                print_result("清空缓存", False, "success=false")
                return False
        else:
            print_result("清空缓存", False, f"状态码: {response.status_code}")
            return False

    except Exception as e:
        print_result("清空缓存", False, f"异常: {str(e)}")
        return False


def test_index_rebuild() -> bool:
    """测试重建索引（可选，耗时较长）"""
    print_section("7. 重建索引 (/rag/index/rebuild) [可选]")

    print("⚠️  重建索引可能需要几分钟时间，是否执行？(y/N): ", end="")
    choice = input().strip().lower()

    if choice != 'y':
        print_result("重建索引", True, "跳过（用户选择）")
        return True

    try:
        print("正在重建索引，请稍候...")
        response = requests.post(f"{BASE_URL}/rag/index/rebuild", timeout=300)

        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                skill_result = data.get("skill_index", {})
                action_result = data.get("action_index", {})
                skill_count = skill_result.get("count", 0)
                action_count = action_result.get("count", 0)
                elapsed = skill_result.get("elapsed_time", 0)
                print_result(
                    "重建索引",
                    True,
                    f"技能: {skill_count}, Actions: {action_count}, 耗时: {elapsed:.2f}s"
                )
                return True
            else:
                print_result("重建索引", False, "success=false")
                return False
        else:
            print_result("重建索引", False, f"状态码: {response.status_code}")
            return False

    except requests.exceptions.Timeout:
        print_result("重建索引", False, "请求超时（可能仍在后台执行）")
        return False
    except Exception as e:
        print_result("重建索引", False, f"异常: {str(e)}")
        return False


def main():
    """主测试流程"""
    print("\n" + "=" * 60)
    print("  RAG API端点测试")
    print("  测试目标: http://localhost:2024")
    print("=" * 60)

    results = {
        "服务器健康检查": test_server_health(),
        "技能语义搜索": False,
        "Action类型推荐": False,
        "参数智能推荐": False,
        "索引统计信息": False,
        "清空缓存": False,
        "重建索引": False,
    }

    # 只有服务器健康才继续后续测试
    if results["服务器健康检查"]:
        results["技能语义搜索"] = test_rag_search()
        results["Action类型推荐"] = test_action_recommendation()
        results["参数智能推荐"] = test_parameter_recommendation()
        results["索引统计信息"] = test_index_stats()
        results["清空缓存"] = test_cache_clear()
        results["重建索引"] = test_index_rebuild()

    # 汇总结果
    print_section("测试汇总")
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    failed = total - passed

    for test_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} | {test_name}")

    print("\n" + "-" * 60)
    print(f"总计: {total} 个测试")
    print(f"通过: {passed} 个 ({passed/total*100:.1f}%)")
    print(f"失败: {failed} 个")
    print("-" * 60)

    if failed == 0:
        print("\n🎉 所有测试通过！RAG API端点工作正常。")
        return 0
    elif passed > 0:
        print(f"\n⚠️  部分测试失败，请检查错误信息。")
        return 1
    else:
        print("\n❌ 所有测试失败，请确保服务器正在运行。")
        print("\n启动服务器:")
        print("  cd skill_agent")
        print("  python langgraph_server.py")
        return 2


if __name__ == "__main__":
    sys.exit(main())
