import sys
import json
import os
import datetime
import argparse

sys.path.append("../../")
sys.path.append("./")

from persona.prompt_modules.llm_structure import LLM_request
from global_methods import *
from utils import *

DEFAULT_PERSONA_PATH = "../../environment/storage/create_test/personas"


def generate_persona_details(
    name,
    gender,
    age,
    occupation,
    education_level,
    background_and_personality,
    living_area="幸福苑小区:1号楼",
):
    """使用LLM生成详细的人物描述，包括化名"""

    # 构建提示词
    prompt = f"""请基于以下信息，为模拟社区环境中的一个虚拟角色创建详细的人物描述：
称呼：{name}
性别：{gender}
年龄：{age}
职业：{occupation}
文化层次：{education_level}
背景及性格特征：{background_and_personality}

请提供以下几个方面的内容，输出格式必须严格按照JSON格式（不要添加多余的引号或符号）：
{{
  "alias": "请根据称呼为该角色起一个合适的全名，保留原有姓氏，例如李某可以变为李明、李华等。对于保安、社区人员等称呼，为其重新起一个新名字，而非职业代称",
  "personality": "请用简短的词语描述此人性格特点，要求客观、准确、突出其特点",
  "background": "请描述此人的背景故事和生活情况，包括家庭、工作、社交等方面，100字以内",
  "living_area": "{living_area}",
  "life_style": "请描述此人的日常作息习惯（包括时间），100字以内",
  "daily_plan_desc": "请描述此人的日程，内容为各个时间段内的事项'，100字以内"
}}
一个示例如下：
"personality": "勤劳、能干、认真",
"background": "小区内 李四饭店 的老板。小区街坊邻居是他的顾客。",
"currently": "",
"living_area": "幸福苑小区:6号楼李四业主家",
"life_style": "李四每天早晨8:00醒来，晚上23:00睡觉。",
"daily_plan_desc": "李四早晨10:00到 李四饭店 开始营业，下午14:00打烊，在自己饭店做午饭吃；傍晚从17:00营业到21:00，随后打烊回到家中。"

只输出JSON内容，不要添加任何其他解释或引言。
"""

    # 调用LLM
    parameter = {
        "model": specify_CoT_model,
        "max_tokens": 2048,
        "temperature": 0.4,
        "top_p": 1,
        "stream": False,
        "stop": None,
    }

    response, _ = LLM_request(prompt, parameter)

    # 解析JSON响应
    try:
        # 找出JSON部分（可能有额外文本）
        json_start = response.find("{")
        json_end = response.rfind("}") + 1
        if json_start >= 0 and json_end > json_start:
            json_str = response[json_start:json_end]
            persona_details = json.loads(json_str)
            return persona_details
        else:
            print("无法解析LLM的JSON响应")
            return None
    except json.JSONDecodeError as e:
        print(f"JSON解析错误: {e}")
        print(f"原始响应: {response}")
        return None


def create_direct_memory_json(
    persona_details, output_path, name, gender, age, alias=None
):
    """创建直接记忆JSON文件"""

    # 使用化名替换原名（如果有化名）
    actual_name = alias if alias else name

    if "岁" in age:
        age = age.split("岁")[0]

    # 创建基本模板
    direct_memory = {
        "vision_r": 8,
        "att_bandwidth": 8,
        "retention": 8,
        "curr_time": None,
        "curr_cell": None,
        "name": actual_name,
        "age": int(age),
        "gender": gender,
        "personality": persona_details.get("personality", ""),
        "background": persona_details.get("background", ""),
        "currently": "",
        "living_area": persona_details.get("living_area", ""),
        "life_style": persona_details.get("life_style", ""),
        "daily_plan_desc": persona_details.get("daily_plan_desc", "").replace(
            name, actual_name
        ),
        "outing_time": None,
        "daily_goals": [],
        "daily_schedule": [],
        "daily_schedule_hourly": [],
        "ordered_minds": [],
        "specify_action": [],
        "act_address": None,
        "act_start_time": None,
        "act_duration": None,
        "act_description": None,
        "act_event": [actual_name, None, None],
        "act_obj_description": None,
        "act_obj_event": [None, None, None],
        "chatting_with": None,
        "chat_history": None,
        "chatting_with_buffer": {},
        "chatting_end_time": None,
        "act_path_set": False,
        "planned_path": [],
        "recency_w": 1,
        "relevance_w": 1,
        "importance_w": 1,
        "recency_decay": 0.99,
        "importance_trigger_max": 150,
        "importance_trigger_curr": 150,
        "importance_ele_n": 0,
    }

    # 确保目录存在
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # 写入JSON文件
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(direct_memory, f, ensure_ascii=False, indent=2)

    print(f"已成功创建角色记忆文件: {output_path}")
    return output_path


def main():
    parser = argparse.ArgumentParser(description="生成角色记忆文件")
    parser.add_argument("--name", type=str, help="角色姓名")
    parser.add_argument("--gender", type=str, help="角色性别")
    parser.add_argument("--age", type=int, help="角色年龄")
    parser.add_argument("--occupation", type=str, help="角色职业")
    parser.add_argument("--education", type=str, help="角色文化层次")
    parser.add_argument("--background", type=str, help="角色背景及性格特征")
    parser.add_argument(
        "--output", type=str, help="输出目录路径", default=DEFAULT_PERSONA_PATH
    )

    args = parser.parse_args()

    # 如果没有提供命令行参数，则交互式获取信息
    if not (
        args.name
        and args.gender
        and args.age
        and args.occupation
        and args.education
        and args.background
    ):
        print("请输入角色信息:")
        name = input("姓名: ")
        gender = input("性别: ")
        age = input("年龄: ")
        occupation = input("职业: ")
        education_level = input("文化层次: ")
        background_and_personality = input("背景及性格特征: ")
    else:
        name = args.name
        gender = args.gender
        age = args.age
        occupation = args.occupation
        education_level = args.education
        background_and_personality = args.background

    # 生成角色详情
    persona_details = generate_persona_details(
        name, gender, age, occupation, education_level, background_and_personality
    )

    if persona_details:
        # 获取化名（如果有）
        alias = persona_details.get("alias", "")
        actual_name = alias if alias and alias.strip() else name

        # 创建输出目录
        persona_dir = os.path.join(args.output, actual_name)
        os.makedirs(persona_dir, exist_ok=True)

        # 创建直接记忆文件
        output_path = os.path.join(persona_dir, "direct_memory.json")
        create_direct_memory_json(
            persona_details, output_path, name, gender, age, actual_name
        )
    else:
        print("生成角色信息失败")


if __name__ == "__main__":
    main()
