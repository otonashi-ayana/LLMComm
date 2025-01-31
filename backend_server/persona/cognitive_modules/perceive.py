import sys

sys.path.append("../../")
import math
from operator import itemgetter
from persona.memory_modules.associate_memory import *


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
    # print("spatial_mem_tree:", persona.spatial_mem.tree)
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
        perceived_events += [event]

    ret_events = []
    for p_event in perceived_events:
        s, p, o, desc = p_event
        if not p:  # event没有事件发生
            p = "is"
            o = "idle"
            desc = "idle"
        desc = f"{s.split(':')[-1]} is {desc}"
        p_event = (s, p, o, desc)

        latest_events = persona.direct_mem.latest_events
        if p_event not in latest_events:
            if latest_events:
                latest_events.pop(0)
            latest_events.append(p_event)
            ret_events += [ConceptNode(s, p, o, desc)]

    persona.direct_mem.latest_events = latest_events
    # ret_events: a list of <ConceptNode> that are perceived and new.
    return ret_events
