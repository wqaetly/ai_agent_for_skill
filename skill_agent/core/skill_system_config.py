"""
技能系统配置加载器

从 Unity 导出的 skill_system_config.json 加载配置，
用于适配不同项目的技能架构。
"""

import json
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from pathlib import Path


@dataclass
class SchemaFieldMapping:
    """字段映射配置"""
    unity: str
    python: str
    description: str = ""


@dataclass
class SkillSystemConfig:
    """技能系统配置"""
    # 项目信息
    project_name: str = "ai_agent_for_skill"
    assembly_name: str = "Assembly-CSharp"
    unity_version: str = ""
    
    # 类型配置
    base_action_type: str = "SkillSystem.Actions.ISkillAction"
    skill_data_type: str = "SkillSystem.Data.SkillData"
    skill_track_type: str = "SkillSystem.Data.SkillTrack"
    
    # 完整类型字符串（包含程序集）
    base_action_full: str = ""
    skill_data_full: str = ""
    skill_track_full: str = ""
    
    # 特性配置
    display_name_attribute: str = "ActionDisplayNameAttribute"
    category_attribute: str = "ActionCategoryAttribute"
    label_text_attribute: str = "LabelTextAttribute"
    box_group_attribute: str = "BoxGroupAttribute"
    info_box_attribute: str = "InfoBoxAttribute"
    min_value_attribute: str = "MinValueAttribute"
    
    # 字段映射
    schema_mappings: List[SchemaFieldMapping] = field(default_factory=list)
    
    def __post_init__(self):
        """初始化后处理"""
        # 如果完整类型字符串为空，自动生成
        if not self.base_action_full:
            self.base_action_full = f"{self.base_action_type}, {self.assembly_name}"
        if not self.skill_data_full:
            self.skill_data_full = f"{self.skill_data_type}, {self.assembly_name}"
        if not self.skill_track_full:
            self.skill_track_full = f"{self.skill_track_type}, {self.assembly_name}"
    
    def get_odin_type_string(self, type_name: str) -> str:
        """获取完整的 Odin 类型字符串"""
        return f"{type_name}, {self.assembly_name}"
    
    def get_list_type_string(self, element_type: str) -> str:
        """获取 List 类型的完整类型字符串"""
        return f"System.Collections.Generic.List`1[[{element_type}, {self.assembly_name}]], mscorlib"
    
    def get_field_mapping(self, unity_field: str) -> Optional[str]:
        """获取 Unity 字段对应的 Python 字段名"""
        for mapping in self.schema_mappings:
            if mapping.unity == unity_field:
                return mapping.python
        return None


# 全局配置实例
_global_config: Optional[SkillSystemConfig] = None


def load_skill_system_config(config_path: Optional[str] = None) -> SkillSystemConfig:
    """
    加载技能系统配置
    
    Args:
        config_path: 配置文件路径，默认为 Data/skill_system_config.json
        
    Returns:
        SkillSystemConfig 实例
    """
    global _global_config
    
    if config_path is None:
        # 默认路径
        base_dir = Path(__file__).parent.parent
        config_path = base_dir / "Data" / "skill_system_config.json"
    else:
        config_path = Path(config_path)
    
    if not config_path.exists():
        print(f"[SkillSystemConfig] 配置文件不存在: {config_path}，使用默认配置")
        _global_config = SkillSystemConfig()
        return _global_config
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 解析配置
        project = data.get("project", {})
        types = data.get("types", {})
        attributes = data.get("attributes", {})
        schema_mapping = data.get("schema_mapping", [])
        
        # 构建字段映射
        mappings = [
            SchemaFieldMapping(
                unity=m.get("unity", ""),
                python=m.get("python", ""),
                description=m.get("description", "")
            )
            for m in schema_mapping
        ]
        
        _global_config = SkillSystemConfig(
            project_name=project.get("name", ""),
            assembly_name=project.get("assembly", "Assembly-CSharp"),
            unity_version=project.get("unity_version", ""),
            base_action_type=types.get("base_action", "SkillSystem.Actions.ISkillAction"),
            skill_data_type=types.get("skill_data", "SkillSystem.Data.SkillData"),
            skill_track_type=types.get("skill_track", "SkillSystem.Data.SkillTrack"),
            base_action_full=types.get("base_action_full", ""),
            skill_data_full=types.get("skill_data_full", ""),
            skill_track_full=types.get("skill_track_full", ""),
            display_name_attribute=attributes.get("display_name", "ActionDisplayNameAttribute"),
            category_attribute=attributes.get("category", "ActionCategoryAttribute"),
            label_text_attribute=attributes.get("label_text", "LabelTextAttribute"),
            box_group_attribute=attributes.get("box_group", "BoxGroupAttribute"),
            info_box_attribute=attributes.get("info_box", "InfoBoxAttribute"),
            min_value_attribute=attributes.get("min_value", "MinValueAttribute"),
            schema_mappings=mappings
        )
        
        print(f"[SkillSystemConfig] 已加载配置: {config_path}")
        print(f"  - 项目: {_global_config.project_name}")
        print(f"  - 程序集: {_global_config.assembly_name}")
        print(f"  - 基类: {_global_config.base_action_type}")
        
        return _global_config
        
    except Exception as e:
        print(f"[SkillSystemConfig] 加载配置失败: {e}，使用默认配置")
        _global_config = SkillSystemConfig()
        return _global_config


def get_skill_system_config() -> SkillSystemConfig:
    """获取全局配置实例（懒加载）"""
    global _global_config
    if _global_config is None:
        _global_config = load_skill_system_config()
    return _global_config

