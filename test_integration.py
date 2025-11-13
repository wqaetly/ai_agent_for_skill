#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整集成测试脚本
测试Unity RAG功能迁移到WebUI后的完整系统
"""

import sys
import os
import time
import json
from pathlib import Path

# 设置UTF-8输出
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# 颜色代码
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
BOLD = '\033[1m'
RESET = '\033[0m'


def print_header(text):
    """打印章节标题"""
    print("\n" + "=" * 70)
    print(f"{BOLD}{BLUE}{text}{RESET}")
    print("=" * 70)


def print_success(text):
    """打印成功消息"""
    print(f"{GREEN}✓{RESET} {text}")


def print_error(text):
    """打印错误消息"""
    print(f"{RED}✗{RESET} {text}")


def print_warning(text):
    """打印警告消息"""
    print(f"{YELLOW}⚠{RESET} {text}")


def print_info(text):
    """打印信息消息"""
    print(f"{BLUE}ℹ{RESET} {text}")


def check_file_exists(file_path, description):
    """检查文件是否存在"""
    if os.path.exists(file_path):
        print_success(f"{description}: {file_path}")
        return True
    else:
        print_error(f"{description}不存在: {file_path}")
        return False


def check_file_deleted(file_path, description):
    """检查文件是否已删除"""
    if not os.path.exists(file_path):
        print_success(f"{description}已删除: {file_path}")
        return True
    else:
        print_error(f"{description}仍然存在: {file_path}")
        return False


def check_backend_files():
    """检查后端文件"""
    print_header("1. 检查后端文件")

    results = []

    # 检查langgraph_server.py
    server_file = "skill_agent/langgraph_server.py"
    if check_file_exists(server_file, "LangGraph服务器"):
        # 检查是否包含新增的API端点
        with open(server_file, 'r', encoding='utf-8') as f:
            content = f.read()
            endpoints = [
                "/rag/search",
                "/rag/recommend-actions",
                "/rag/recommend-parameters",
                "/rag/index/rebuild",
                "/rag/index/stats",
                "/rag/cache",
                "/rag/health"
            ]

            for endpoint in endpoints:
                if endpoint in content:
                    print_success(f"  端点已实现: {endpoint}")
                    results.append(True)
                else:
                    print_error(f"  端点缺失: {endpoint}")
                    results.append(False)
    else:
        results.append(False)

    # 检查测试脚本
    test_file = "skill_agent/test_rag_api.py"
    results.append(check_file_exists(test_file, "API测试脚本"))

    # 检查迁移文档
    migration_file = "MIGRATION_GUIDE.md"
    results.append(check_file_exists(migration_file, "迁移指南"))

    return all(results)


def check_unity_files():
    """检查Unity文件"""
    print_header("2. 检查Unity文件")

    results = []
    base_path = "ai_agent_for_skill/Assets/Scripts/RAGSystem/Editor"

    # 检查已删除的文件
    deleted_files = [
        f"{base_path}/SkillAgentWindow.cs",
        f"{base_path}/EditorRAGClient.cs",
        f"{base_path}/SmartActionInspector.cs",
    ]

    for file_path in deleted_files:
        results.append(check_file_deleted(file_path, os.path.basename(file_path)))

    # 检查已修改的文件
    modified_files = [
        f"{base_path}/RAGEditorIntegration.cs",
        f"{base_path}/DescriptionManagerWindow.cs",
    ]

    for file_path in modified_files:
        if check_file_exists(file_path, os.path.basename(file_path)):
            # 检查文件内容
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

                if file_path.endswith("RAGEditorIntegration.cs"):
                    # 应该包含WebUI相关内容
                    if "WebUIUrl" in content and "打开WebUI" in content:
                        print_success(f"  已重构为WebUI集成")
                        results.append(True)
                    else:
                        print_error(f"  未正确重构")
                        results.append(False)

                elif file_path.endswith("DescriptionManagerWindow.cs"):
                    # 不应该包含RAG服务器启动相关代码
                    if "StartServer" not in content and "StopServer" not in content:
                        print_success(f"  已移除RAG服务器管理功能")
                        results.append(True)
                    else:
                        print_error(f"  仍包含RAG服务器管理代码")
                        results.append(False)
        else:
            results.append(False)

    return all(results)


def check_webui_files():
    """检查WebUI文件"""
    print_header("3. 检查WebUI文件")

    results = []
    base_path = "webui"

    # 检查配置文件
    config_files = [
        f"{base_path}/package.json",
        f"{base_path}/tsconfig.json",
        f"{base_path}/next.config.js",
        f"{base_path}/tailwind.config.ts",
        f"{base_path}/postcss.config.js",
    ]

    for file_path in config_files:
        results.append(check_file_exists(file_path, os.path.basename(file_path)))

    # 检查源代码文件
    src_files = [
        f"{base_path}/src/app/layout.tsx",
        f"{base_path}/src/app/page.tsx",
        f"{base_path}/src/app/globals.css",
        f"{base_path}/src/app/rag/page.tsx",
    ]

    for file_path in src_files:
        results.append(check_file_exists(file_path, os.path.basename(file_path)))

    # 检查RAG页面内容
    rag_page = f"{base_path}/src/app/rag/page.tsx"
    if os.path.exists(rag_page):
        with open(rag_page, 'r', encoding='utf-8') as f:
            content = f.read()

            # 检查是否包含4个Tab
            tabs = ["技能搜索", "Action推荐", "参数推荐", "索引管理"]
            for tab in tabs:
                if tab in content:
                    print_success(f"  Tab已实现: {tab}")
                    results.append(True)
                else:
                    print_error(f"  Tab缺失: {tab}")
                    results.append(False)

            # 检查API调用
            apis = [
                "/rag/search",
                "/rag/recommend-actions",
                "/rag/recommend-parameters",
                "/rag/health"
            ]
            for api in apis:
                if api in content:
                    print_success(f"  API调用已实现: {api}")
                    results.append(True)
                else:
                    print_error(f"  API调用缺失: {api}")
                    results.append(False)

    return all(results)


def test_backend_api():
    """测试后端API（可选，需要服务运行）"""
    print_header("4. 测试后端API（可选）")

    try:
        import requests
    except ImportError:
        print_warning("requests库未安装，跳过API测试")
        print_info("可以手动运行: python skill_agent/test_rag_api.py")
        return None

    base_url = "http://localhost:2024"

    # 检查服务是否运行
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print_success("后端服务运行正常")

            # 测试RAG健康检查
            response = requests.get(f"{base_url}/rag/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                status = data.get('status', 'unknown')
                if status == 'healthy':
                    print_success(f"RAG服务健康: 技能数={data.get('indexed_skills', 0)}")
                    return True
                else:
                    print_warning(f"RAG服务状态: {status}")
                    return False
            else:
                print_error("RAG健康检查失败")
                return False
        else:
            print_warning("后端服务返回异常状态码")
            return False

    except requests.exceptions.ConnectionError:
        print_warning("后端服务未运行")
        print_info("启动方式: python skill_agent/langgraph_server.py")
        return None
    except Exception as e:
        print_error(f"API测试失败: {e}")
        return False


def check_code_quality():
    """检查代码质量"""
    print_header("5. 代码质量检查")

    results = []

    # 检查Python代码
    print_info("检查Python代码...")
    python_file = "skill_agent/langgraph_server.py"
    try:
        with open(python_file, 'r', encoding='utf-8') as f:
            content = f.read()
            # 简单的语法检查
            compile(content, python_file, 'exec')
            print_success("Python代码语法正确")
            results.append(True)
    except SyntaxError as e:
        print_error(f"Python语法错误: {e}")
        results.append(False)

    # 检查TypeScript代码（简单检查）
    print_info("检查TypeScript代码...")
    ts_files = [
        "webui/src/app/layout.tsx",
        "webui/src/app/page.tsx",
        "webui/src/app/rag/page.tsx",
    ]

    ts_ok = True
    for ts_file in ts_files:
        if os.path.exists(ts_file):
            with open(ts_file, 'r', encoding='utf-8') as f:
                content = f.read()
                # 检查基本的语法元素
                if "export default" in content and ("function" in content or "const" in content):
                    print_success(f"  {os.path.basename(ts_file)} 结构正确")
                else:
                    print_warning(f"  {os.path.basename(ts_file)} 可能有问题")
                    ts_ok = False
        else:
            print_error(f"  {ts_file} 不存在")
            ts_ok = False

    results.append(ts_ok)

    # 检查Unity C#代码（简单检查）
    print_info("检查Unity C#代码...")
    cs_files = [
        "ai_agent_for_skill/Assets/Scripts/RAGSystem/Editor/RAGEditorIntegration.cs",
        "ai_agent_for_skill/Assets/Scripts/RAGSystem/Editor/DescriptionManagerWindow.cs",
    ]

    cs_ok = True
    for cs_file in cs_files:
        if os.path.exists(cs_file):
            with open(cs_file, 'r', encoding='utf-8') as f:
                content = f.read()
                # 检查命名空间
                if "namespace SkillSystem" in content:
                    print_success(f"  {os.path.basename(cs_file)} 命名空间正确")
                else:
                    print_warning(f"  {os.path.basename(cs_file)} 命名空间可能有问题")
                    cs_ok = False
        else:
            print_error(f"  {cs_file} 不存在")
            cs_ok = False

    results.append(cs_ok)

    return all(results)


def generate_report(results):
    """生成测试报告"""
    print_header("测试报告")

    total = len(results)
    passed = sum(1 for r in results.values() if r is True)
    failed = sum(1 for r in results.values() if r is False)
    skipped = sum(1 for r in results.values() if r is None)

    print(f"\n{BOLD}测试结果统计:{RESET}")
    print(f"  总计: {total} 项")
    print(f"  {GREEN}通过: {passed} 项{RESET}")
    print(f"  {RED}失败: {failed} 项{RESET}")
    print(f"  {YELLOW}跳过: {skipped} 项{RESET}")
    print(f"  成功率: {passed/(total-skipped)*100 if total > skipped else 0:.1f}%")

    print(f"\n{BOLD}详细结果:{RESET}")
    for test_name, result in results.items():
        if result is True:
            print(f"  {GREEN}✓{RESET} {test_name}")
        elif result is False:
            print(f"  {RED}✗{RESET} {test_name}")
        else:
            print(f"  {YELLOW}○{RESET} {test_name} (跳过)")

    print("\n" + "=" * 70)

    if failed == 0:
        print(f"{GREEN}{BOLD}🎉 所有测试通过！迁移成功完成。{RESET}")
        return 0
    elif passed > 0:
        print(f"{YELLOW}{BOLD}⚠️  部分测试失败，请检查上述错误信息。{RESET}")
        return 1
    else:
        print(f"{RED}{BOLD}❌ 所有测试失败，请检查项目结构。{RESET}")
        return 2


def print_next_steps():
    """打印下一步操作"""
    print_header("下一步操作")

    print(f"\n{BOLD}1. 启动后端服务:{RESET}")
    print("   cd skill_agent")
    print("   python langgraph_server.py")

    print(f"\n{BOLD}2. 测试后端API:{RESET}")
    print("   python skill_agent/test_rag_api.py")

    print(f"\n{BOLD}3. 启动WebUI:{RESET}")
    print("   cd webui")
    print("   npm install  # 首次运行")
    print("   npm run dev")

    print(f"\n{BOLD}4. 访问WebUI:{RESET}")
    print("   浏览器打开: http://localhost:3000/rag")

    print(f"\n{BOLD}5. Unity中测试:{RESET}")
    print("   - 打开Unity Editor")
    print("   - 检查编译错误")
    print("   - 测试: Tools → SkillAgent → 启动服务器")
    print("   - 测试: 技能系统 → RAG功能 → 打开WebUI")
    print("   - 测试: 描述管理器")

    print(f"\n{BOLD}6. 阅读文档:{RESET}")
    print("   - MIGRATION_GUIDE.md - 迁移指南")
    print("   - webui/src/app/rag/README.md - WebUI使用说明")

    print()


def main():
    """主函数"""
    print("\n" + "=" * 70)
    print(f"{BOLD}{BLUE}Unity RAG功能迁移 - 集成测试{RESET}")
    print("=" * 70)
    print(f"测试时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"工作目录: {os.getcwd()}")

    results = {}

    # 执行各项检查
    results["后端文件检查"] = check_backend_files()
    results["Unity文件检查"] = check_unity_files()
    results["WebUI文件检查"] = check_webui_files()
    results["后端API测试"] = test_backend_api()
    results["代码质量检查"] = check_code_quality()

    # 生成报告
    exit_code = generate_report(results)

    # 打印下一步操作
    print_next_steps()

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
