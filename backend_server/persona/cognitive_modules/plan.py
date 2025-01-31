"""
描述智能体的规划（Plan）功能
"""

import sys

sys.path.append("../../")

from persona.prompt_modules.run_prompt import *


def generate_wake_up_time(persona):
    """
    生成角色的起床时间，日常规划的基础
    """
    return int(run_prompt_wake_up_time(persona))


def generate_first_daily_goals(persona, wake_up_time):
    """
    生成角色的第一日日常目标，基础规划
    """
    return run_prompt_daily_goals(persona, wake_up_time)


def generate_hourly_schedule(persona, wake_up_time):
    hour_str = [
        "00:00",
        "01:00",
        "02:00",
        "03:00",
        "04:00",
        "05:00",
        "06:00",
        "07:00",
        "08:00",
        "09:00",
        "10:00",
        "11:00",
        "12:00",
        "13:00",
        "14:00",
        "15:00",
        "16:00",
        "17:00",
        "18:00",
        "19:00",
        "20:00",
        "21:00",
        "22:00",
        "23:00",
    ]
    hourly_activity = []
    diversity_repeat_count = 3
    for i in range(diversity_repeat_count):
        print("diversity_repeat_count:", i)
        hourly_activity_set = set(hourly_activity)
        if len(hourly_activity_set) < 5:
            hourly_activity = []
            wake_up_time_tmp = wake_up_time
            for count, curr_hour_str in enumerate(hour_str):
                if wake_up_time_tmp > 0:
                    hourly_activity += ["睡觉"]
                    wake_up_time_tmp -= 1
                else:
                    hourly_activity += [
                        run_prompt_generate_hourly_schedule(
                            persona, curr_hour_str, hourly_activity, hour_str
                        )
                    ]
    hourly_compressed = []
    prev = None
    prev_count = 0
    for i in hourly_activity:
        if i != prev:
            prev_count = 1
            hourly_compressed += [[i, prev_count]]
            prev = i
        else:
            if hourly_compressed:
                hourly_compressed[-1][1] += 1

    hourly_compressed_min = []
    for task, duration in hourly_compressed:
        hourly_compressed_min += [[task, duration * 60]]

    return hourly_compressed_min


def new_day_planning(persona, new_day):
    wake_up_time = generate_wake_up_time(persona)
    if new_day == "first":
        persona.direct_mem.daily_goals = generate_first_daily_goals(
            persona, wake_up_time
        )
    elif new_day == "new":
        # TODO
        pass
    persona.direct_mem.daily_schedule = generate_hourly_schedule(persona, wake_up_time)
    persona.direct_mem.daily_schedule_hourly = persona.direct_mem.daily_schedule[:]


def generate_task_decomp(persona, task, duration):
    return run_gpt_prompt_task_decomp(persona, task, duration)


def generate_action_sector(act_desp, persona, maze):
    return run_gpt_prompt_action_sector(act_desp, persona, maze)


def generate_action_area(act_desp, persona, maze, act_world, act_sector):
    return run_gpt_prompt_action_area(act_desp, persona, maze, act_world, act_sector)


def generate_action_object(act_desp, act_address, persona, maze):
    if not persona.spatial_mem.get_str_accessible_arena_objects(act_address):
        return "<random>"
    return run_gpt_prompt_action_object(act_desp, persona, maze, act_address)


def determine_action(persona, maze):
    def determine_decomp(act_desp, act_dura):
        if "睡觉" in act_desp:
            return False
        if act_desp == "外出":
            return False
        # elif "sleep" in act_desp or "bed" in act_desp:
        #     if act_dura > 60:
        #         return False
        return True

    curr_index = persona.direct_mem.get_daily_schedule_index()
    curr_index_60 = persona.direct_mem.get_daily_schedule_index(advance=60)

    if curr_index == 0:
        act_desp, act_dura = persona.direct_mem.daily_schedule[curr_index]
        if act_dura >= 60:
            if determine_decomp(act_desp, act_dura):
                persona.direct_mem.daily_schedule[curr_index : curr_index + 1] = (
                    generate_task_decomp(persona, act_desp, act_dura)
                )
        if curr_index_60 + 1 < len(persona.direct_mem.daily_schedule):
            act_desp, act_dura = persona.direct_mem.daily_schedule[curr_index_60 + 1]
            if act_dura >= 60:
                if determine_decomp(act_desp, act_dura):
                    persona.direct_mem.daily_schedule[
                        curr_index_60 + 1 : curr_index_60 + 2
                    ] = generate_task_decomp(persona, act_desp, act_dura)

    if curr_index_60 < len(persona.direct_mem.daily_schedule):
        if persona.direct_mem.curr_time.hour < 23:
            act_desp, act_dura = persona.direct_mem.daily_schedule[curr_index_60]
            if act_dura >= 60:
                if determine_decomp(act_desp, act_dura):
                    persona.direct_mem.daily_schedule[
                        curr_index_60 : curr_index_60 + 1
                    ] = generate_task_decomp(persona, act_desp, act_dura)

    if debug:
        print_c("<determine_action> output")
        for i in persona.direct_mem.daily_schedule:
            print(i)
        # print(curr_index)
        # print(len(persona.direct_mem.daily_schedule))
        # print(persona.direct_mem.name)
        print_c("<determine_action> end")

    # 1440
    x_emergency = 0
    for i in persona.direct_mem.daily_schedule:
        x_emergency += i[1]
    # print ("x_emergency", x_emergency)

    if 1440 - x_emergency > 0:
        print("x_emergency__AAA", x_emergency)
    persona.direct_mem.daily_schedule += [["sleeping", 1440 - x_emergency]]

    act_desp, act_dura = persona.direct_mem.daily_schedule[curr_index]

    # Finding the target location of the action and creating action-related
    # variables.
    act_world = maze.access_cell(persona.direct_mem.curr_cell)["world"]
    # act_sector = maze.access_cell(persona.direct_mem.curr_cell)["sector"]
    act_sector = generate_action_sector(act_desp, persona, maze)
    act_area = generate_action_area(act_desp, persona, maze, act_world, act_sector)
    act_address = f"{act_world}:{act_sector}:{act_area}"
    act_object = generate_action_game_object(act_desp, act_address, persona, maze)
    new_address = f"{act_world}:{act_sector}:{act_area}:{act_object}"
    act_pron = generate_action_pronunciatio(act_desp, persona)
    act_event = generate_action_event_triple(act_desp, persona)
    # Persona's actions also influence the object states. We set those up here.
    act_obj_desp = generate_act_obj_desc(act_object, act_desp, persona)
    act_obj_pron = generate_action_pronunciatio(act_obj_desp, persona)
    act_obj_event = generate_act_obj_event_triple(act_object, act_obj_desp, persona)

    # Adding the action to persona's queue.
    persona.direct_mem.add_new_action(
        new_address,
        int(act_dura),
        act_desp,
        act_pron,
        act_event,
        None,
        None,
        None,
        None,
        act_obj_desp,
        act_obj_pron,
        act_obj_event,
    )


def plan(persona, maze, personas, new_day, retrieved):
    # plan小时计划（min单位）
    if new_day:  # 如果是同一天内，new_day=False
        new_day_planning(persona, new_day)

    # 如果当前时间下的action已到期，新建一个action
    if persona.direct_mem.act_check_finished():
        determine_action(persona, maze)
