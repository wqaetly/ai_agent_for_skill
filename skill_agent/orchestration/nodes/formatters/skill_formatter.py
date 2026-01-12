"""
技能格式化模块
"""

from typing import Any, Dict, List


def format_similar_skills(skills: List[Dict[str, Any]]) -> str:
    """格式化相似技能用于 prompt"""
    if not skills:
        return "No reference skills"

    formatted = []
    for i, skill in enumerate(skills[:3]):
        skill_name = skill.get("skill_name", "Unknown")
        skill_data = skill.get("skill_data", {})

        tracks = skill_data.get("tracks", [])
        track_info = []
        for track in tracks[:5]:
            track_name = track.get("trackName", "?")
            actions_count = len(track.get("actions", []))
            track_info.append(f"{track_name} ({actions_count} actions)")

        formatted.append(
            f"Reference Skill {i+1}: {skill_name}\n"
            f"  - Tracks: {', '.join(track_info) if track_info else 'None'}\n"
            f"  - Total Duration: {skill_data.get('totalDuration', '?')} frames"
        )

    return "\n\n".join(formatted)


def format_action_schemas_for_prompt(action_schemas: List[Dict[str, Any]]) -> str:
    """格式化 Action Schema 用于 prompt"""
    if not action_schemas:
        return ""

    formatted_actions = []
    for action in action_schemas[:5]:
        action_name = action.get('action_name', 'Unknown')
        action_type = action.get('action_type', 'N/A')
        category = action.get('category', 'N/A')
        description = action.get('description', '')[:200]
        parameters = action.get('parameters', [])

        params_info = []
        for param in parameters:
            param_name = param.get('name', 'unknown')
            param_type = param.get('type', 'unknown')
            default_val = param.get('defaultValue', '')
            constraints = param.get('constraints', {})
            is_enum = param.get('isEnum', False)
            enum_values = param.get('enumValues', [])

            constraint_desc = []
            if constraints.get('min'):
                constraint_desc.append(f"min={constraints['min']}")
            if constraints.get('max'):
                constraint_desc.append(f"max={constraints['max']}")
            if constraints.get('minValue'):
                constraint_desc.append(f"minValue={constraints['minValue']}")
            if constraints.get('maxValue'):
                constraint_desc.append(f"maxValue={constraints['maxValue']}")

            param_info = f"  - {param_name}: {param_type}"
            if default_val:
                param_info += f" = {default_val}"
            if is_enum and enum_values:
                param_info += f" (enum: {', '.join(enum_values)})"
            elif constraint_desc:
                param_info += f" ({', '.join(constraint_desc)})"

            params_info.append(param_info)

        params_text = "\n".join(params_info) if params_info else "  No parameters"

        formatted_action = f"""Action: {action_name} ({action_type})
Category: {category}
Description: {description}
Parameters:
{params_text}"""
        formatted_actions.append(formatted_action)

    return "\n\n".join(formatted_actions)
