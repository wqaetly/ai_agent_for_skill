#!/usr/bin/env python3
"""
Claude 开发规范应用脚本
用于自动应用和管理 Claude 开发规范配置
"""

import json
import os
import sys
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional

class StandardsManager:
    """Claude 开发规范管理器"""

    def __init__(self, plugin_root: str):
        self.plugin_root = Path(plugin_root)
        self.config_dir = self.plugin_root / "config"
        self.prompts_dir = self.plugin_root / "prompts"
        self.default_config_file = self.config_dir / "default-config.json"

    def load_default_config(self) -> Dict[str, Any]:
        """加载默认配置"""
        try:
            with open(self.default_config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"❌ 默认配置文件未找到: {self.default_config_file}")
            return {}
        except json.JSONDecodeError as e:
            print(f"❌ 配置文件格式错误: {e}")
            return {}

    def load_prompt_module(self, module_name: str) -> Optional[str]:
        """加载提示词模块"""
        prompt_file = self.prompts_dir / f"{module_name}.md"
        if prompt_file.exists():
            with open(prompt_file, 'r', encoding='utf-8') as f:
                return f.read()
        return None

    def get_available_modules(self) -> List[str]:
        """获取可用的提示词模块"""
        modules = []
        for file in self.prompts_dir.glob("*.md"):
            modules.append(file.stem)
        return modules

    def apply_standards(self,
                       modules: List[str] = None,
                       scenario: str = "default",
                       interactive: bool = False,
                       dry_run: bool = False) -> bool:
        """应用开发规范"""

        config = self.load_default_config()
        if not config:
            return False

        available_modules = self.get_available_modules()

        if interactive:
            selected_modules = self._interactive_module_selection(available_modules)
        elif modules:
            selected_modules = [m for m in modules if m in available_modules]
        else:
            selected_modules = available_modules

        if dry_run:
            print("🔍 预览将要加载的规范模块:")
            for module in selected_modules:
                print(f"  - {module}")
            return True

        # 加载并应用选定的模块
        applied_prompts = []
        for module in selected_modules:
            prompt_content = self.load_prompt_module(module)
            if prompt_content:
                applied_prompts.append({
                    "name": module,
                    "content": prompt_content
                })

        # 生成组合提示词
        combined_prompt = self._generate_combined_prompt(applied_prompts, config, scenario)

        # 应用到当前会话
        if self._apply_to_session(combined_prompt):
            self._print_success_message(selected_modules, config, scenario)
            return True

        return False

    def _interactive_module_selection(self, available_modules: List[str]) -> List[str]:
        """交互式模块选择"""
        print("\n🎯 请选择要加载的规范模块:")
        print("0. 加载全部模块")

        for i, module in enumerate(available_modules, 1):
            description = self._get_module_description(module)
            print(f"{i}. {module} - {description}")

        while True:
            try:
                choice = input("\n请输入数字选择 (多选用逗号分隔): ").strip()

                if choice == "0":
                    return available_modules

                selected_indices = [int(x.strip()) - 1 for x in choice.split(",")]
                selected_modules = []

                for idx in selected_indices:
                    if 0 <= idx < len(available_modules):
                        selected_modules.append(available_modules[idx])
                    else:
                        print(f"⚠️ 无效选择: {idx + 1}")
                        break
                else:
                    return selected_modules

            except (ValueError, KeyboardInterrupt):
                print("❌ 输入无效，请重新选择")

    def _get_module_description(self, module_name: str) -> str:
        """获取模块描述"""
        descriptions = {
            "language-standards": "中文交流，直接犀利风格",
            "work-principles": "质量导向，架构感知",
            "socratic-dialogue": "深度质疑，智能激活",
            "technical-analysis": "系统性分析框架"
        }
        return descriptions.get(module_name, "开发规范模块")

    def _generate_combined_prompt(self,
                                 applied_prompts: List[Dict],
                                 config: Dict[str, Any],
                                 scenario: str) -> str:
        """生成组合提示词"""

        prompt_parts = []

        # 添加角色定义
        prompt_parts.append("# Claude 开发规范助手")
        prompt_parts.append("你是一个遵循严格中文开发规范的 Claude Code 助手。")
        prompt_parts.append("")

        # 添加场景特定配置
        if scenario != "default":
            scenario_config = self._get_scenario_config(scenario)
            if scenario_config:
                prompt_parts.append(f"## 当前场景: {scenario_config['name']}")
                prompt_parts.append(scenario_config['description'])
                prompt_parts.append("")

        # 添加各模块内容
        for prompt in applied_prompts:
            prompt_parts.append(f"## {prompt['name'].replace('-', ' ').title()}")
            prompt_parts.append(prompt['content'])
            prompt_parts.append("")

        # 添加配置总结
        prompt_parts.append("## 当前配置总结")
        prompt_parts.append(f"- 主要语言: {config['language']['primary']}")
        prompt_parts.append(f"- 表达风格: 直接犀利，零废话")
        prompt_parts.append(f"- 质量要求: 严格模式")
        prompt_parts.append(f"- 对话模式: 智能激活苏格拉底式对话")
        prompt_parts.append("")

        return "\n".join(prompt_parts)

    def _get_scenario_config(self, scenario: str) -> Optional[Dict[str, str]]:
        """获取场景特定配置"""
        scenarios = {
            "code-review": {
                "name": "代码审查",
                "description": "专注于代码质量检查、架构合理性分析和最佳实践建议。应用严格的质量底线检查，重点关注可维护性和性能影响。"
            },
            "architecture": {
                "name": "架构设计",
                "description": "专注于架构决策权衡、设计方案评估和技术选型分析。系统性分析架构优劣，提供决策支持。"
            },
            "planning": {
                "name": "技术规划",
                "description": "专注于技术方案规划、实施路径设计和风险评估。平衡开发效率与代码质量，制定合理的技术债务管理策略。"
            },
            "debugging": {
                "name": "问题调试",
                "description": "专注于问题根因分析、调试策略制定和解决方案验证。系统性分析问题，提供可执行的解决步骤。"
            }
        }
        return scenarios.get(scenario)

    def _apply_to_session(self, combined_prompt: str) -> bool:
        """应用提示词到当前会话"""
        # 这里应该与 Claude Code 的会话系统集成
        # 目前只是模拟应用过程
        print("🔄 正在应用开发规范到当前会话...")
        # 实际实现需要调用 Claude Code 的 API
        return True

    def _print_success_message(self, modules: List[str], config: Dict[str, Any], scenario: str):
        """打印成功消息"""
        print("✅ Claude 开发规范加载成功\n")

        print("📋 已加载的规范模块:")
        for module in modules:
            description = self._get_module_description(module)
            print(f"├── {module} - {description}")

        print("\n⚙️ 配置详情:")
        print(f"- 主要语言: {config['language']['primary']}")
        print(f"- 表达风格: 直接、零废话")
        print(f"- 质量检查: 严格模式")
        print(f"- 对话模式: 智能激活")

        if scenario != "default":
            scenario_config = self._get_scenario_config(scenario)
            if scenario_config:
                print(f"- 应用场景: {scenario_config['name']}")

        print("\n💡 使用提示:")
        print("- 使用'为什么'等关键词触发深度讨论")
        print("- 代码审查将自动应用质量底线检查")
        print("- 技术分析将使用系统性框架")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="Claude 开发规范应用工具")

    parser.add_argument("--modules", "-m", nargs="+",
                       help="要加载的模块列表")
    parser.add_argument("--scenario", "-s",
                       choices=["default", "code-review", "architecture", "planning", "debugging"],
                       default="default",
                       help="应用场景")
    parser.add_argument("--interactive", "-i", action="store_true",
                       help="交互式选择模块")
    parser.add_argument("--dry-run", "-d", action="store_true",
                       help="预览模式，不实际应用")
    parser.add_argument("--plugin-root",
                       default=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       help="插件根目录路径")

    args = parser.parse_args()

    manager = StandardsManager(args.plugin_root)

    success = manager.apply_standards(
        modules=args.modules,
        scenario=args.scenario,
        interactive=args.interactive,
        dry_run=args.dry_run
    )

    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()