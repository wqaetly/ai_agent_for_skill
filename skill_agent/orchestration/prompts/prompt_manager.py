"""
Prompt 管理器
加载和管理所有 Prompt 模板，支持变量替换
"""

import yaml
from pathlib import Path
from typing import Dict, Any, List
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate


class PromptManager:
    """Prompt 模板管理器"""

    def __init__(self, prompts_file: str = None):
        """
        初始化 Prompt 管理器

        Args:
            prompts_file: prompts.yaml 文件路径，默认使用当前目录下的
        """
        if prompts_file is None:
            prompts_dir = Path(__file__).parent
            prompts_file = prompts_dir / "prompts.yaml"

        self.prompts_file = Path(prompts_file)

        if not self.prompts_file.exists():
            raise FileNotFoundError(f"Prompts 文件不存在: {self.prompts_file}")

        # 加载所有 prompts
        with open(self.prompts_file, 'r', encoding='utf-8') as f:
            self.prompts = yaml.safe_load(f)

    def get_prompt(self, prompt_key: str, **kwargs) -> ChatPromptTemplate:
        """
        获取 LangChain ChatPromptTemplate

        Args:
            prompt_key: Prompt 键名（如 'skill_generation'）
            **kwargs: 变量值（用于预填充）

        Returns:
            ChatPromptTemplate 实例
        """
        if prompt_key not in self.prompts:
            raise KeyError(f"Prompt '{prompt_key}' 不存在")

        prompt_config = self.prompts[prompt_key]
        system_template = prompt_config.get('system', '')
        user_template = prompt_config.get('user', '')

        # 创建 ChatPromptTemplate
        messages = []

        if system_template:
            messages.append(SystemMessagePromptTemplate.from_template(system_template))

        if user_template:
            messages.append(HumanMessagePromptTemplate.from_template(user_template))

        prompt_template = ChatPromptTemplate.from_messages(messages)

        # 如果提供了变量值，进行部分填充
        if kwargs:
            prompt_template = prompt_template.partial(**kwargs)

        return prompt_template

    def get_raw_template(self, prompt_key: str) -> Dict[str, str]:
        """
        获取原始模板字符串

        Args:
            prompt_key: Prompt 键名

        Returns:
            包含 'system' 和 'user' 的字典
        """
        if prompt_key not in self.prompts:
            raise KeyError(f"Prompt '{prompt_key}' 不存在")

        return self.prompts[prompt_key].copy()

    def list_prompts(self) -> List[str]:
        """列出所有可用的 Prompt 键名"""
        return list(self.prompts.keys())

    def reload(self):
        """重新加载 prompts.yaml（用于热更新）"""
        with open(self.prompts_file, 'r', encoding='utf-8') as f:
            self.prompts = yaml.safe_load(f)


# 全局 Prompt 管理器实例
_global_prompt_manager = None


def get_prompt_manager(prompts_file: str = None) -> PromptManager:
    """
    获取全局 Prompt 管理器实例

    Args:
        prompts_file: prompts.yaml 文件路径（仅首次调用有效）

    Returns:
        PromptManager 实例
    """
    global _global_prompt_manager

    if _global_prompt_manager is None:
        _global_prompt_manager = PromptManager(prompts_file)

    return _global_prompt_manager
