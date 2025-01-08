"""
描述智能体的规划（Plan）功能
"""


def generate_wake_up_time(persona):
    """
    生成角色的起床时间，日常规划的基础
    """
    if debug:
        print("<generate_wake_up_time>")
    return int(run_prompt_wake_up_time(persona))
