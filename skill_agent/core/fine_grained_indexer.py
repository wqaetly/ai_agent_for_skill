"""
细粒度索引器 - 构建行级/路径级索�?扩展现有skill_indexer，支持Action级别的精确定�?"""

import json
import hashlib
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime
import re


class FineGrainedIndexer:
    """细粒度索引器 - 记录每个Action的路径、行号和参数"""

    def __init__(self, skills_dir: str = "../../ai_agent_for_skill/Assets/Skills"):
        """
        Args:
            skills_dir: 技能文件目�?        """
        self.skills_dir = Path(skills_dir)
        self.index_file = Path("../Data/fine_grained_index.json")
        self.index_data = self._load_index()

    def index_all_skills(self, force_rebuild: bool = False) -> Dict[str, Any]:
        """
        为所有技能构建细粒度索引

        Args:
            force_rebuild: 强制重建所有索�?
        Returns:
            索引统计信息
        """
        if not self.skills_dir.exists():
            raise FileNotFoundError(f"技能目录不存在: {self.skills_dir}")

        stats = {
            "total_files": 0,
            "indexed_files": 0,
            "total_actions": 0,
            "skipped_files": 0,
            "errors": []
        }

        skill_files = list(self.skills_dir.glob("*.json"))
        stats["total_files"] = len(skill_files)

        for skill_file in skill_files:
            try:
                # 检查是否需要更�?                if not force_rebuild and self._is_file_indexed(skill_file):
                    stats["skipped_files"] += 1
                    continue

                # 构建细粒度索�?                file_index = self._index_single_file(skill_file)

                if file_index:
                    self.index_data["files"][str(skill_file)] = file_index
                    stats["indexed_files"] += 1
                    stats["total_actions"] += file_index["total_actions"]

            except Exception as e:
                stats["errors"].append({
                    "file": str(skill_file),
                    "error": str(e)
                })

        # 更新全局元数�?        self.index_data["metadata"]["last_updated"] = datetime.now().isoformat()
        self.index_data["metadata"]["total_files"] = stats["indexed_files"]
        self.index_data["metadata"]["total_actions"] = stats["total_actions"]

        # 保存索引
        self._save_index()

        return stats

    def _index_single_file(self, file_path: Path) -> Dict[str, Any]:
        """
        为单个技能文件构建细粒度索引

        Returns:
            {
                "file_hash": "md5...",
                "skill_name": "...",
                "total_actions": 12,
                "tracks": [
                    {
                        "track_name": "Damage Track",
                        "track_index": 2,
                        "track_path": "tracks.$rcontent[2]",
                        "actions": [
                            {
                                "action_type": "DamageAction",
                                "action_index": 0,
                                "json_path": "tracks.$rcontent[2].actions.$rcontent[0]",
                                "line_number": 145,
                                "frame": 10,
                                "duration": 20,
                                "parameters": {...},
                                "summary": "..."
                            }
                        ]
                    }
                ]
            }
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 计算文件哈希
        file_hash = hashlib.md5(content.encode('utf-8')).hexdigest()

        # 修复Unity JSON格式
        content_fixed = self._fix_unity_json(content)

        # 解析JSON
        data = json.loads(content_fixed)

        # 提取基础信息
        skill_name = data.get("skillName", "Unknown")

        # 索引所有轨道和Action
        tracks_index = []
        total_actions = 0

        tracks_data = data.get("tracks", {})
        if isinstance(tracks_data, dict) and "$rcontent" in tracks_data:
            tracks_list = tracks_data["$rcontent"]

            for track_idx, track in enumerate(tracks_list):
                track_name = track.get("trackName", f"Track {track_idx}")
                track_path = f"tracks.$rcontent[{track_idx}]"

                actions_index = []

                # 索引轨道中的Action
                actions_data = track.get("actions", {})
                if isinstance(actions_data, dict) and "$rcontent" in actions_data:
                    actions_list = actions_data["$rcontent"]

                    for action_idx, action in enumerate(actions_list):
                        action_info = self._index_action(
                            action,
                            track_idx,
                            action_idx,
                            track_name,
                            content
                        )

                        if action_info:
                            actions_index.append(action_info)
                            total_actions += 1

                if actions_index:
                    tracks_index.append({
                        "track_name": track_name,
                        "track_index": track_idx,
                        "track_path": track_path,
                        "actions": actions_index
                    })

        return {
            "file_hash": file_hash,
            "skill_name": skill_name,
            "total_actions": total_actions,
            "last_modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
            "tracks": tracks_index
        }

    def _index_action(
        self,
        action_data: Dict[str, Any],
        track_idx: int,
        action_idx: int,
        track_name: str,
        file_content: str
    ) -> Optional[Dict[str, Any]]:
        """索引单个Action"""
        # 提取Action类型
        action_type = self._extract_action_type(action_data.get("$type", ""))
        if not action_type:
            return None

        # 构建JSON路径
        json_path = f"tracks.$rcontent[{track_idx}].actions.$rcontent[{action_idx}]"

        # 估算行号（通过搜索JSON片段�?        line_number = self._estimate_line_number(action_data, file_content)

        # 提取参数（排除元数据字段�?        parameters = {
            k: v for k, v in action_data.items()
            if not k.startswith("$") and k not in ["frame", "duration"]
        }

        # 生成摘要
        summary = self._generate_action_summary(
            action_type,
            action_data,
            track_name
        )

        return {
            "action_type": action_type,
            "action_index": action_idx,
            "json_path": json_path,
            "line_number": line_number,
            "frame": action_data.get("frame", 0),
            "duration": action_data.get("duration", 0),
            "parameters": parameters,
            "summary": summary
        }

    def _extract_action_type(self, type_str: str) -> Optional[str]:
        """
        从Odin类型字符串提取Action类型名称

        Args:
            type_str: "4|SkillSystem.Actions.DamageAction, Assembly-CSharp"

        Returns:
            "DamageAction"
        """
        if "|" in type_str:
            type_name = type_str.split("|")[1].split(",")[0]
            return type_name.split(".")[-1]
        return None

    def _estimate_line_number(
        self,
        action_data: Dict[str, Any],
        file_content: str
    ) -> int:
        """
        估算Action在文件中的行�?
        通过搜索Action的特征字段（�?id或特殊参数值）来定�?        """
        # 使用$id作为锚点
        action_id = action_data.get("$id")
        if action_id is not None:
            pattern = f'"\\$id":\\s*{action_id}'
            match = re.search(pattern, file_content)
            if match:
                # 计算匹配位置之前的行�?                line_number = file_content[:match.start()].count('\n') + 1
                return line_number

        # 回退：使用frame值作为锚�?        frame = action_data.get("frame")
        if frame is not None:
            pattern = f'"frame":\\s*{frame}'
            # 搜索所有匹配，取第一个（简化处理）
            match = re.search(pattern, file_content)
            if match:
                line_number = file_content[:match.start()].count('\n') + 1
                return line_number

        return -1  # 无法确定

    def _generate_action_summary(
        self,
        action_type: str,
        action_data: Dict[str, Any],
        track_name: str
    ) -> str:
        """生成Action的可读摘�?""
        parts = [f"[{track_name}]"]

        frame = action_data.get("frame", 0)
        duration = action_data.get("duration", 0)
        parts.append(f"第{frame}�?)

        if duration > 0:
            parts.append(f"持续{duration}�?)

        # 根据类型提取关键参数
        if action_type == "DamageAction":
            damage = action_data.get("baseDamage", action_data.get("damage", "?"))
            damage_type = action_data.get("damageType", "")
            parts.append(f"造成{damage}点{damage_type}伤害")

            radius = action_data.get("damageRadius", 0)
            if radius > 0:
                parts.append(f"范围{radius}�?)

        elif action_type == "MovementAction":
            speed = action_data.get("moveSpeed", action_data.get("speed", "?"))
            parts.append(f"移动速度{speed}")

            distance = action_data.get("moveDistance", 0)
            if distance > 0:
                parts.append(f"移动{distance}�?)

        elif action_type == "AnimationAction":
            clip = action_data.get("animationClipName", "")
            if clip:
                parts.append(f"播放: {clip}")

        elif action_type == "HealAction":
            heal = action_data.get("healAmount", "?")
            parts.append(f"治疗{heal}点生�?)

        elif action_type == "ShieldAction":
            shield = action_data.get("shieldAmount", "?")
            parts.append(f"护盾{shield}�?)

        elif action_type == "ControlAction":
            control_type = action_data.get("controlType", "")
            control_duration = action_data.get("controlDuration", 0)
            parts.append(f"{control_type} {control_duration}�?)

        return " - ".join(parts)

    def _is_file_indexed(self, file_path: Path) -> bool:
        """检查文件是否已索引且未修改"""
        file_key = str(file_path)

        if file_key not in self.index_data["files"]:
            return False

        # 检查文件哈�?        with open(file_path, 'r', encoding='utf-8') as f:
            current_hash = hashlib.md5(f.read().encode('utf-8')).hexdigest()

        indexed_hash = self.index_data["files"][file_key].get("file_hash")

        return current_hash == indexed_hash

    def _load_index(self) -> Dict[str, Any]:
        """加载索引文件"""
        if self.index_file.exists():
            with open(self.index_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            return {
                "metadata": {
                    "version": "1.0",
                    "created": datetime.now().isoformat(),
                    "last_updated": None,
                    "total_files": 0,
                    "total_actions": 0
                },
                "files": {}
            }

    def _save_index(self):
        """保存索引到文�?""
        self.index_file.parent.mkdir(parents=True, exist_ok=True)

        with open(self.index_file, 'w', encoding='utf-8') as f:
            json.dump(self.index_data, f, ensure_ascii=False, indent=2)

    def get_index(self) -> Dict[str, Any]:
        """获取完整索引数据"""
        return self.index_data

    def get_file_index(self, file_path: str) -> Optional[Dict[str, Any]]:
        """获取指定文件的索�?""
        return self.index_data["files"].get(file_path)

    def _fix_unity_json(self, json_str: str) -> str:
        """
        修复Unity生成的非标准JSON格式
        主要处理Vector3、Color等类型的简写格�?        """
        # 处理 Color (4个�? r, g, b, a)
        pattern_color = r'("\$type":\s*"[^"]*UnityEngine\.Color([^"]*)")\s*,\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)'

        def replace_color(match):
            type_str = match.group(1)
            r = match.group(3)
            g = match.group(4)
            b = match.group(5)
            a = match.group(6)
            return f'{type_str}, "r": {r}, "g": {g}, "b": {b}, "a": {a}'

        json_str = re.sub(pattern_color, replace_color, json_str)

        # 处理 Vector3 (3个�? x, y, z)
        pattern_vector3 = r'("\$type":\s*"[^"]*UnityEngine\.Vector3([^"]*)")\s*,\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)'

        def replace_vector3(match):
            type_str = match.group(1)
            x = match.group(3)
            y = match.group(4)
            z = match.group(5)
            return f'{type_str}, "x": {x}, "y": {y}, "z": {z}'

        json_str = re.sub(pattern_vector3, replace_vector3, json_str)

        # 处理 Vector2 (2个�? x, y)
        pattern_vector2 = r'("\$type":\s*"[^"]*UnityEngine\.Vector2([^"]*)")\s*,\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)'

        def replace_vector2(match):
            type_str = match.group(1)
            x = match.group(3)
            y = match.group(4)
            return f'{type_str}, "x": {x}, "y": {y}'

        json_str = re.sub(pattern_vector2, replace_vector2, json_str)

        return json_str


# ==================== 便捷函数 ====================

def build_fine_grained_index(skills_dir: str = None, force_rebuild: bool = False) -> Dict[str, Any]:
    """
    构建细粒度索引（便捷函数�?
    Args:
        skills_dir: 技能目录（可选）
        force_rebuild: 强制重建

    Returns:
        索引统计信息
    """
    if skills_dir:
        indexer = FineGrainedIndexer(skills_dir)
    else:
        indexer = FineGrainedIndexer()

    return indexer.index_all_skills(force_rebuild=force_rebuild)
