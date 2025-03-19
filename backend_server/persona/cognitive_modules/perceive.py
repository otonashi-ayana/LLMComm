import sys

sys.path.append("../../")
import math
from operator import itemgetter
from persona.memory_modules.associate_memory import *
from persona.prompt_modules.llm_structure import *
from persona.prompt_modules.run_prompt import *


def generate_poig_score(persona, event_type, description):
    if "正在 空闲" in description:
        return 1
    if event_type == "event" or event_type == "thought":
        return run_prompt_event_poignancy(persona, description)
    elif event_type == "chat":
        return run_prompt_chat_poignancy(persona, persona.direct_mem.act_description)


def perceive(persona, maze):
    nearby_cells = maze.get_nearby_cells(
        persona.direct_mem.curr_cell, persona.direct_mem.vision_r
    )

    # 构建空间记忆树 tree={}
    for i in nearby_cells:
        i = maze.access_cell(i)
        if i["world"]:
            if i["world"] not in persona.spatial_mem.tree:
                persona.spatial_mem.tree[i["world"]] = {}
        if i["sector"]:
            if i["sector"] not in persona.spatial_mem.tree[i["world"]]:
                persona.spatial_mem.tree[i["world"]][i["sector"]] = {}
        if i["area"]:
            if i["area"] not in persona.spatial_mem.tree[i["world"]][i["sector"]]:
                persona.spatial_mem.tree[i["world"]][i["sector"]][i["area"]] = []
        if i["object"]:
            if (
                i["object"]
                not in persona.spatial_mem.tree[i["world"]][i["sector"]][i["area"]]
            ):
                persona.spatial_mem.tree[i["world"]][i["sector"]][i["area"]] += [
                    i["object"]
                ]
    curr_area_path = maze.get_cell_path(persona.direct_mem.curr_cell, "area")
    # print("curr_area_path:", curr_area_path)
    percept_events_set = set()
    percept_events_list = []
    for cell in nearby_cells:
        cell_info = maze.access_cell(cell)
        if cell_info["events"]:  # 只筛选有event发生的cell
            if maze.get_cell_path(cell, "area") == curr_area_path:
                # print("cell_info with events and current area:", cell_info["object"])
                # 计算area内所有cell的距离
                distance = math.dist(
                    [cell[0], cell[1]],
                    [persona.direct_mem.curr_cell[0], persona.direct_mem.curr_cell[1]],
                )
                # print(distance)
                # 将所有cell的所有event及dist存入
                for event in cell_info["events"]:
                    # print(event)
                    if event not in percept_events_set:
                        percept_events_list += [[distance, event]]
                        percept_events_set.add(event)
    # 按dist排序,perceived_events存入较近event
    percept_events_list = sorted(percept_events_list, key=itemgetter(0))
    perceived_events = []
    for dist, event in percept_events_list[: persona.direct_mem.att_bandwidth]:
        # print(event)
        perceived_events += [
            event
        ]  # perceived_events（list）是按照距离排序的前att_bandwidth个event

    ret_events = []
    for p_event in perceived_events:
        s, p, o, desc = p_event
        # print_c("<perceive> p_event:", s, p, o, desc)
        if not p:  # event没有事件发生
            p = "正在"
            o = "空闲"
            desc = "空闲"
        desc = f"{s.split(':')[-1]} 正在 {desc}"
        # print_c("<perceive> edited desc:", desc)
        # cell_info的event主语都是object?
        p_event = (s, p, o)

        latest_events = persona.associate_mem.get_summarized_latest_events(
            persona.direct_mem.retention
        )  # 长记忆中前retention个事件。如果当前事件超过该冷却窗口，则作为新事件
        if p_event not in latest_events:
            # step 1：关键词
            keywords = set()
            sub = p_event[0]
            obj = p_event[2]
            if ":" in p_event[0]:
                sub = p_event[0].split(":")[-1]
            if ":" in p_event[2]:
                obj = p_event[2].split(":")[-1]
            keywords.update([sub, obj])  # 提取主语和宾语"keywords":["bed","used"]

            # step 2：使用desc编码事件
            desc_embedding_in = desc
            if "（" in desc:
                desc_embedding_in = (
                    desc_embedding_in.split("（")[1].split("）")[0].strip()
                )  # 取出（子任务内容）
            if desc_embedding_in in persona.associate_mem.embeddings:
                # 检查当前desc是否在缓存的{desc:[embedding]中}
                event_embedding = persona.associate_mem.embeddings[desc_embedding_in]
            else:
                event_embedding = get_embedding(desc_embedding_in)
            event_embedding_pair = (desc_embedding_in, event_embedding)

            # step 3: 获得重要性打分
            event_poignancy = generate_poig_score(persona, "event", desc_embedding_in)

            # 如果perceive到人物自己相关的聊天，加入到chat记忆
            chat_node_ids = []
            if p_event[0] == f"{persona.name}" and p_event[1] == "聊天":
                curr_event = persona.direct_mem.act_event  # (李华,正在,吃饭)
                if (
                    persona.direct_mem.act_description
                    in persona.associate_mem.embeddings
                ):
                    chat_embedding = persona.associate_mem.embeddings[
                        persona.direct_mem.act_description
                    ]
                else:
                    chat_embedding = get_embedding(persona.direct_mem.act_description)
                chat_embedding_pair = (
                    persona.direct_mem.act_description,
                    chat_embedding,
                )
                chat_poignancy = generate_poig_score(
                    persona, "chat", persona.direct_mem.act_description
                )
                chat_node = persona.associate_mem.add_chat(
                    persona.direct_mem.curr_time,
                    None,
                    curr_event[0],
                    curr_event[1],
                    curr_event[2],
                    persona.direct_mem.act_description,
                    keywords,
                    chat_poignancy,
                    chat_embedding_pair,
                    persona.direct_mem.chat_history,
                )
                chat_node_ids = [chat_node.node_id]

            # Finally, we add the current event to the agent's memory.
            ret_events += [
                persona.associate_mem.add_event(
                    persona.direct_mem.curr_time,
                    None,
                    s,
                    p,
                    o,
                    desc,
                    keywords,
                    event_poignancy,
                    event_embedding_pair,
                    chat_node_ids,
                )
            ]
            persona.direct_mem.importance_trigger_curr -= event_poignancy
            persona.direct_mem.importance_ele_n += 1

    return ret_events
