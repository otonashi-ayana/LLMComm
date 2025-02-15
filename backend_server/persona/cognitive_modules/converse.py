import sys

sys.path.append("../")
from global_methods import *

from persona.memory_modules.spatial_memory import *
from persona.memory_modules.associate_memory import *
from persona.memory_modules.direct_memory import *
from persona.cognitive_modules.retrieve import *
from persona.prompt_modules.run_prompt import *


def generate_summarize_agent_relationship(init_persona, target_persona, retrieved):
    all_embedding_keys = list()
    for key, val in retrieved.items():
        for i in val:
            all_embedding_keys += [i.embedding_key]
    all_embedding_key_str = ""
    for i in all_embedding_keys:
        all_embedding_key_str += f"{i}\n"

    summarized_relationship = run_prompt_agent_chat_summarize_relationship(
        init_persona, target_persona, all_embedding_key_str
    )[0]
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
    )[0]

    return x["utterance"], x["end"]


def agent_chat_v2(maze, init_persona, target_persona):
    curr_chat = []

    for i in range(1):
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
