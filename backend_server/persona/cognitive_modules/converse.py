import sys

sys.path.append("../")
from global_methods import *

from persona.memory_modules.spatial_memory import *
from persona.memory_modules.associate_memory import *
from persona.memory_modules.direct_memory import *
from persona.cognitive_modules.retrieve import *
from persona.prompt_modules.run_prompt import *
import threading

convo_lock = threading.Lock()

# convo_map: 记录多个对话提案
# key: frozenset({A_name, B_name})
# value: {
#   'status': 'WAITING' | 'IN_PROGRESS' | 'DONE' | 'CANCELLED',
#   'participants': set([A_name, B_name]),
#   'convo_info': {...}  # 存储具体对话数据, 例如对话内容、时间、摘要等
# }
convo_map = {}


def register_convo(persona_name, target_name):
    """在对话管理器中注册一个新的对话提案"""
    pair = frozenset({persona_name, target_name})
    with convo_lock:
        if pair not in convo_map:
            convo_map[pair] = {
                "status": "IN_PROGRESS",
                "participants": set([persona_name, target_name]),
                "convo_info": {},
            }
        return convo_map[pair]


def update_convo_status_from_map(pair, new_status):
    """修改对话状态 (WAITING → IN_PROGRESS / DONE / CANCELLED)"""
    with convo_lock:
        if pair in convo_map:
            convo_map[pair]["status"] = new_status
            convo_map[pair]["cond"].notify_all()  # 唤醒所有等待线程


def get_convo_status_from_map(pair):
    """获取对话状态"""
    with convo_lock:
        return convo_map.get(pair, {}).get("status", None)


def remove_convo_from_map(pair):
    """对话完成后，从管理器中移除"""
    with convo_lock:
        if pair in convo_map:
            del convo_map[pair]


def generate_summarize_agent_relationship(init_persona, target_persona, retrieved):
    description = list()
    for key, val in retrieved.items():
        for i in val:
            if i.predicate == "正在":
                description += [i.description.replace("正在 ", "")]
            else:
                description += [i.description]
    description_str = ""
    for i in description:
        description_str += f"{i}\n"

    summarized_relationship = run_prompt_agent_chat_summarize_relationship(
        init_persona, target_persona, description_str
    )
    return summarized_relationship


def generate_one_utterance(maze, init_persona, target_persona, retrieved, curr_chat):
    # Chat version optimized for speed via batch generation
    curr_context = (
        f"{init_persona.direct_mem.name} "
        + f"正在 {init_persona.direct_mem.act_description} "
        + f"当 {init_persona.direct_mem.name} "
        + f"看到 {target_persona.direct_mem.name} "
        + f"正在 {target_persona.direct_mem.act_description}.\n"
    )
    curr_context += (
        f"{init_persona.direct_mem.name} "
        + f"开始了一段和"
        + f"{target_persona.direct_mem.name}的对话"
    )

    x = run_generate_iterative_chat_utt(
        maze, init_persona, target_persona, retrieved, curr_context, curr_chat
    )

    return x["utterance"], x["end"]


def agent_chat_v2(maze, init_persona, target_persona):
    curr_chat = []

    for i in range(4):
        focal_points = [f"{target_persona.direct_mem.name}"]
        retrieved = new_retrieve(init_persona, focal_points, 20)
        relationship = generate_summarize_agent_relationship(
            init_persona, target_persona, retrieved
        )
        last_chat = ""
        for i in curr_chat[-4:]:
            last_chat += "： ".join(i) + "\n"
        if last_chat:
            focal_points = [
                f"{relationship}",
                f"{target_persona.direct_mem.name} 正在 {target_persona.direct_mem.act_description}",
                last_chat,
            ]
        else:
            focal_points = [
                f"{relationship}",
                f"{target_persona.direct_mem.name} 正在 {target_persona.direct_mem.act_description}",
            ]
        retrieved = new_retrieve(init_persona, focal_points, 10)
        utt, end = generate_one_utterance(
            maze, init_persona, target_persona, retrieved, curr_chat
        )

        curr_chat += [[init_persona.direct_mem.name, utt]]
        if end:
            break

        focal_points = [f"{init_persona.direct_mem.name}"]
        retrieved = new_retrieve(target_persona, focal_points, 20)
        relationship = generate_summarize_agent_relationship(
            target_persona, init_persona, retrieved
        )
        last_chat = ""
        for i in curr_chat[-4:]:
            last_chat += "： ".join(i) + "\n"
        if last_chat:
            focal_points = [
                f"{relationship}",
                f"{init_persona.direct_mem.name} 正在 {init_persona.direct_mem.act_description}",
                last_chat,
            ]
        else:
            focal_points = [
                f"{relationship}",
                f"{init_persona.direct_mem.name} 正在 {init_persona.direct_mem.act_description}",
            ]
        retrieved = new_retrieve(target_persona, focal_points, 10)
        utt, end = generate_one_utterance(
            maze, target_persona, init_persona, retrieved, curr_chat
        )

        curr_chat += [[target_persona.direct_mem.name, utt]]
        if end:
            break

    print("agent_chat_v2 curr_chat：")
    for row in curr_chat:
        print(row)

    return curr_chat
