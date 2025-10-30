"""
技能索引模块
负责读取技能JSON文件，提取信息并建立索引
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime
import hashlib

logger = logging.getLogger(__name__)


class SkillIndexer:
    """技能索引器，处理技能数据的读取和索引"""

    def __init__(self, config: dict):
        """
        初始化技能索引器

        Args:
            config: 索引配置字典
        """
        self.config = config
        self.skills_directory = config.get("skills_directory", "../../ai_agent_for_skill/Assets/Skills")
        self.index_cache_path = config.get("index_cache", "../Data/skill_index.json")
        self.index_fields = config.get("index_fields", ["skillName", "skillDescription", "skillId", "actions"])
        self.index_action_details = config.get("index_action_details", True)

        # 确保技能目录存在
        if not os.path.exists(self.skills_directory):
            logger.warning(f"Skills directory not found: {self.skills_directory}")

        # 加载缓存索引
        self.cached_index = self._load_index_cache()

    def _load_index_cache(self) -> Dict[str, Any]:
        """加载缓存的索引信息"""
        if os.path.exists(self.index_cache_path):
            try:
                with open(self.index_cache_path, 'r', encoding='utf-8') as f:
                    cache = json.load(f)
                logger.info(f"Loaded index cache with {len(cache.get('skills', {}))} skills")
                return cache
            except Exception as e:
                logger.error(f"Error loading index cache: {e}")

        return {"skills": {}, "last_updated": None}

    def _save_index_cache(self, index: Dict[str, Any]):
        """保存索引缓存"""
        try:
            cache_dir = os.path.dirname(self.index_cache_path)
            if cache_dir and not os.path.exists(cache_dir):
                os.makedirs(cache_dir, exist_ok=True)

            with open(self.index_cache_path, 'w', encoding='utf-8') as f:
                json.dump(index, f, ensure_ascii=False, indent=2)
            logger.info(f"Saved index cache to {self.index_cache_path}")
        except Exception as e:
            logger.error(f"Error saving index cache: {e}")

    def _compute_file_hash(self, file_path: str) -> str:
        """计算文件内容的哈希值"""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception as e:
            logger.error(f"Error computing hash for {file_path}: {e}")
            return ""

    def _parse_odin_json(self, json_data: dict) -> Dict[str, Any]:
        """
        解析Odin序列化的JSON数据

        Args:
            json_data: 原始JSON数据

        Returns:
            解析后的技能数据
        """
        skill_data = {}

        # 提取基本字段
        skill_data['skillName'] = json_data.get('skillName', '')
        skill_data['skillDescription'] = json_data.get('skillDescription', '')
        skill_data['skillId'] = json_data.get('skillId', '')
        skill_data['totalDuration'] = json_data.get('totalDuration', 0)
        skill_data['frameRate'] = json_data.get('frameRate', 30)

        # 解析tracks和actions
        skill_data['tracks'] = []
        tracks_data = json_data.get('tracks', {})

        if isinstance(tracks_data, dict) and '$rcontent' in tracks_data:
            # Odin序列化格式
            tracks_content = tracks_data.get('$rcontent', [])

            for track in tracks_content:
                if isinstance(track, dict):
                    track_info = {
                        'trackName': track.get('trackName', ''),
                        'enabled': track.get('enabled', True),
                        'actions': []
                    }

                    # 解析actions
                    actions_data = track.get('actions', {})
                    if isinstance(actions_data, dict) and '$rcontent' in actions_data:
                        actions_content = actions_data.get('$rcontent', [])

                        for action in actions_content:
                            if isinstance(action, dict):
                                action_info = self._parse_action(action)
                                track_info['actions'].append(action_info)

                    skill_data['tracks'].append(track_info)

        return skill_data

    def _parse_action(self, action_data: dict) -> Dict[str, Any]:
        """
        解析单个Action数据

        Args:
            action_data: Action的JSON数据

        Returns:
            解析后的Action信息
        """
        action_info = {
            'type': self._extract_action_type(action_data.get('$type', '')),
            'frame': action_data.get('frame', 0),
            'duration': action_data.get('duration', 0),
            'enabled': action_data.get('enabled', True)
        }

        # 如果需要索引详细参数
        if self.index_action_details:
            # 提取关键参数（排除内部字段）
            params = {}
            for key, value in action_data.items():
                if not key.startswith('$') and key not in ['frame', 'duration', 'enabled']:
                    # 简化复杂对象
                    if isinstance(value, (str, int, float, bool)):
                        params[key] = value
                    elif isinstance(value, dict):
                        # 提取类型信息
                        if '$type' in value:
                            params[key] = self._extract_type_name(value['$type'])
                        else:
                            params[key] = str(value)
                    elif isinstance(value, list):
                        params[key] = f"List[{len(value)}]"

            action_info['parameters'] = params

        return action_info

    def _extract_action_type(self, type_string: str) -> str:
        """从Odin类型字符串中提取Action类型名"""
        # 格式: "2|SkillSystem.Actions.DamageAction, Assembly-CSharp"
        if '|' in type_string:
            type_string = type_string.split('|')[1]
        if ',' in type_string:
            type_string = type_string.split(',')[0]
        if '.' in type_string:
            type_string = type_string.split('.')[-1]
        return type_string

    def _extract_type_name(self, type_string: str) -> str:
        """提取类型名称"""
        return self._extract_action_type(type_string)

    def scan_skills(self) -> List[str]:
        """
        扫描技能目录，返回所有技能JSON文件路径

        Returns:
            技能文件路径列表
        """
        skill_files = []

        if not os.path.exists(self.skills_directory):
            logger.warning(f"Skills directory not found: {self.skills_directory}")
            return skill_files

        try:
            for file_name in os.listdir(self.skills_directory):
                if file_name.endswith('.json'):
                    file_path = os.path.join(self.skills_directory, file_name)
                    skill_files.append(file_path)

            logger.info(f"Found {len(skill_files)} skill files")
        except Exception as e:
            logger.error(f"Error scanning skills directory: {e}")

        return skill_files

    def _fix_unity_json(self, json_str: str) -> str:
        """
        修复Unity生成的非标准JSON格式
        主要处理Vector3、Color等类型的简写格式
        """
        import re

        # 处理 Color (4个值: r, g, b, a)
        pattern_color = r'("\$type":\s*"[^"]*UnityEngine\.Color([^"]*)")\s*,\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)'

        def replace_color(match):
            type_str = match.group(1)
            r = match.group(3)
            g = match.group(4)
            b = match.group(5)
            a = match.group(6)
            return f'{type_str}, "r": {r}, "g": {g}, "b": {b}, "a": {a}'

        json_str = re.sub(pattern_color, replace_color, json_str)

        # 处理 Vector3 (3个值: x, y, z)
        pattern_vector3 = r'("\$type":\s*"[^"]*UnityEngine\.Vector3([^"]*)")\s*,\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)'

        def replace_vector3(match):
            type_str = match.group(1)
            x = match.group(3)
            y = match.group(4)
            z = match.group(5)
            return f'{type_str}, "x": {x}, "y": {y}, "z": {z}'

        json_str = re.sub(pattern_vector3, replace_vector3, json_str)

        # 处理 Vector2 (2个值: x, y)
        pattern_vector2 = r'("\$type":\s*"[^"]*UnityEngine\.Vector2([^"]*)")\s*,\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)'

        def replace_vector2(match):
            type_str = match.group(1)
            x = match.group(3)
            y = match.group(4)
            return f'{type_str}, "x": {x}, "y": {y}'

        json_str = re.sub(pattern_vector2, replace_vector2, json_str)

        return json_str

    def parse_skill_file(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        解析单个技能文件

        Args:
            file_path: 技能文件路径

        Returns:
            解析后的技能数据，失败返回None
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                json_str = f.read()

            # 修复Unity的非标准JSON格式
            json_str = self._fix_unity_json(json_str)

            # 解析JSON
            json_data = json.loads(json_str)

            skill_data = self._parse_odin_json(json_data)

            # 添加文件信息
            skill_data['file_path'] = file_path
            skill_data['file_name'] = os.path.basename(file_path)
            skill_data['file_hash'] = self._compute_file_hash(file_path)
            skill_data['last_modified'] = datetime.fromtimestamp(
                os.path.getmtime(file_path)
            ).isoformat()

            return skill_data

        except Exception as e:
            logger.error(f"Error parsing skill file {file_path}: {e}")
            return None

    def build_search_text(self, skill_data: Dict[str, Any]) -> str:
        """
        构建用于向量检索的搜索文本

        Args:
            skill_data: 技能数据

        Returns:
            搜索文本
        """
        text_parts = []

        # 技能名称
        if skill_data.get('skillName'):
            text_parts.append(f"技能名称：{skill_data['skillName']}")

        # 技能描述
        if skill_data.get('skillDescription'):
            text_parts.append(f"技能描述：{skill_data['skillDescription']}")

        # 技能ID
        if skill_data.get('skillId'):
            text_parts.append(f"技能ID：{skill_data['skillId']}")

        # Action信息
        if skill_data.get('tracks'):
            action_types = []
            action_summaries = []

            for track in skill_data['tracks']:
                if not track.get('enabled', True):
                    continue

                for action in track.get('actions', []):
                    action_type = action.get('type', '')
                    if action_type:
                        action_types.append(action_type)

                        # 添加关键参数信息
                        if self.index_action_details and 'parameters' in action:
                            params = action['parameters']
                            # 构建简短描述
                            param_strs = [f"{k}={v}" for k, v in list(params.items())[:3]]
                            action_summaries.append(f"{action_type}({', '.join(param_strs)})")

            if action_types:
                text_parts.append(f"包含动作：{', '.join(set(action_types))}")

            if action_summaries:
                text_parts.append(f"动作详情：{'; '.join(action_summaries[:5])}")

        return "\n".join(text_parts)

    def index_all_skills(self, force_rebuild: bool = False) -> List[Dict[str, Any]]:
        """
        索引所有技能

        Args:
            force_rebuild: 是否强制重建索引（忽略缓存）

        Returns:
            技能数据列表
        """
        skill_files = self.scan_skills()
        indexed_skills = []

        for file_path in skill_files:
            # 检查缓存
            file_hash = self._compute_file_hash(file_path)
            cached_skill = self.cached_index.get('skills', {}).get(file_path)

            if not force_rebuild and cached_skill:
                if cached_skill.get('file_hash') == file_hash:
                    logger.debug(f"Using cached data for {file_path}")
                    indexed_skills.append(cached_skill)
                    continue

            # 解析技能文件
            skill_data = self.parse_skill_file(file_path)
            if skill_data:
                # 构建搜索文本
                skill_data['search_text'] = self.build_search_text(skill_data)
                indexed_skills.append(skill_data)

        # 更新缓存
        new_cache = {
            'skills': {skill['file_path']: skill for skill in indexed_skills},
            'last_updated': datetime.now().isoformat()
        }
        self._save_index_cache(new_cache)
        self.cached_index = new_cache

        logger.info(f"Indexed {len(indexed_skills)} skills")
        return indexed_skills

    def check_for_changes(self) -> List[str]:
        """
        检查技能文件是否有变化

        Returns:
            变化的文件路径列表
        """
        changed_files = []
        skill_files = self.scan_skills()

        for file_path in skill_files:
            current_hash = self._compute_file_hash(file_path)
            cached_skill = self.cached_index.get('skills', {}).get(file_path)

            if not cached_skill or cached_skill.get('file_hash') != current_hash:
                changed_files.append(file_path)

        return changed_files


if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(level=logging.INFO)

    config = {
        "skills_directory": "../../ai_agent_for_skill/Assets/Skills",
        "index_cache": "../Data/skill_index.json",
        "index_fields": ["skillName", "skillDescription", "skillId", "actions"],
        "index_action_details": True
    }

    indexer = SkillIndexer(config)

    # 索引所有技能
    skills = indexer.index_all_skills(force_rebuild=True)

    # 打印结果
    for skill in skills[:2]:  # 只打印前2个
        print(f"\n{'='*60}")
        print(f"Skill: {skill.get('skillName', 'N/A')}")
        print(f"ID: {skill.get('skillId', 'N/A')}")
        print(f"Description: {skill.get('skillDescription', 'N/A')}")
        print(f"Tracks: {len(skill.get('tracks', []))}")
        print(f"Search Text:\n{skill.get('search_text', 'N/A')[:200]}...")
