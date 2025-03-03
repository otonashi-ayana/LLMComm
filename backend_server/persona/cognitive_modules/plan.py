"""
描述智能体的规划（Plan）功能
"""

import math
import sys

sys.path.append("../../")

from persona.prompt_modules.run_prompt import *
from persona.cognitive_modules.converse import *
from converse import (
    register_convo,
    update_convo_status_from_map,
    get_convo_status_from_map,
    remove_convo_from_map,
)


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


def simple_generate_hourly_schedule(persona, wake_up_time):
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
    outing_time = persona.direct_mem.outing_time
    diversity_repeat_count = 3
    for i in range(diversity_repeat_count):
        print("diversity_repeat_count:", i + 1)
        hourly_activity = []
        for _ in range(wake_up_time):
            hourly_activity += ["睡觉"]
        hourly_activity_response = run_prompt_simple_generate_hourly_schedule(
            persona, hour_str, wake_up_time, outing_time
        ).split("\n")

        hourly_activity += [
            activity.split("正在")[-1].strip() for activity in hourly_activity_response
        ]
        hourly_activity_set = set(hourly_activity)
        if len(hourly_activity_set) > 4:
            break
    # print("hourly_activity", hourly_activity)

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
    # print("hourly_compressed_min", hourly_compressed_min)

    return hourly_compressed_min


def revise_identity(persona):
    p_name = persona.scratch.name

    focal_points = [
        f"{p_name}在{persona.scratch.get_str_curr_date_str()}当天的计划。",
        f"关于{p_name}生活的重要近期事件。",
    ]
    retrieved = new_retrieve(persona, focal_points)

    # 构建陈述记录
    statements = "[陈述记录]\n"
    for key, val in retrieved.items():
        for i in val:
            statements += (
                f"{i.created.strftime('%A %B %d -- %H:%M %p')}: {i.embedding_key}\n"
            )

    # 生成计划笔记
    plan_prompt = statements + "\n"
    plan_prompt += f"根据上述陈述，{p_name}在制定*{persona.scratch.curr_time.strftime('%A %B %d')}*计划时，有哪些需要特别注意的事项？"
    plan_prompt += f"如果包含日程安排信息，请尽可能具体（若陈述中提及，需包含日期、时间和地点）\n\n"
    plan_prompt += f"请以{p_name}的第一视角进行回答。"
    plan_note = ChatGPT_single_request(plan_prompt)

    # 生成情感总结
    thought_prompt = statements + "\n"
    thought_prompt += f"基于上述陈述，如何总结{p_name}迄今为止的日常情绪感受？\n\n"
    thought_prompt += f"请以{p_name}的第一视角进行回答。"
    thought_note = ChatGPT_single_request(thought_prompt)

    # 生成当前状态
    currently_prompt = f"{p_name}在{(persona.scratch.curr_time - datetime.timedelta(days=1)).strftime('%A %B %d')}的状态：\n"
    currently_prompt += f"{persona.scratch.currently}\n\n"
    currently_prompt += f"{p_name}在{(persona.scratch.curr_time - datetime.timedelta(days=1)).strftime('%A %B %d')}结束时的思考：\n"
    currently_prompt += (plan_note + thought_note).replace("\n", "") + "\n\n"
    currently_prompt += f"当前时间为{persona.scratch.curr_time.strftime('%A %B %d')}。根据以上信息，请用第三人称撰写{p_name}当天的状态描述，需反映其前一天的思考内容。"
    currently_prompt += f"若包含日程安排，请提供完整细节（日期、时间、地点）。\n\n"
    currently_prompt += "请严格遵循格式：\n状态：<新状态>"
    new_currently = ChatGPT_single_request(currently_prompt)

    persona.scratch.currently = new_currently

    # 生成每日计划
    daily_req_prompt = persona.scratch.get_str_iss() + "\n"
    daily_req_prompt += f"今天是{persona.scratch.curr_time.strftime('%A %B %d')}。请列出{p_name}当日的概略计划（需包含时间段，例如：中午12:00用餐，19:00-20:00观看电视）。\n\n"
    daily_req_prompt += f"格式要求（列表项4~6条）：\n"
    daily_req_prompt += f"1. 在<时间>起床并完成早晨例行活动，2. ..."

    new_daily_req = ChatGPT_single_request(daily_req_prompt)
    new_daily_req = new_daily_req.replace("\n", " ")
    print("生成结果：", new_daily_req)
    persona.scratch.daily_plan_req = new_daily_req


def _new_day_planning(persona, new_day):
    wake_up_time = generate_wake_up_time(persona)
    if new_day == "first":
        persona.direct_mem.daily_goals = generate_first_daily_goals(
            persona, wake_up_time
        )
    elif new_day == "new":
        # TODO
        pass
        # revise_identity(persona)

    persona.direct_mem.daily_schedule = simple_generate_hourly_schedule(
        persona, wake_up_time
    )
    persona.direct_mem.daily_schedule_hourly = persona.direct_mem.daily_schedule[:]

    thought = f"这是 {persona.direct_mem.name} 在 {persona.direct_mem.curr_time.strftime('%A %B %d')}的计划:"
    for i in persona.direct_mem.daily_goals:
        thought += f" {i}，"
    thought = thought[:-1] + "。"
    created = persona.direct_mem.curr_time
    expiration = persona.direct_mem.curr_time + datetime.timedelta(days=30)
    s, p, o = (
        persona.direct_mem.name,
        "计划",
        persona.direct_mem.curr_time.strftime("%A %B %d"),
    )
    keywords = set(["计划"])
    thought_poignancy = 5
    thought_embedding_pair = (thought, get_embedding(thought))
    persona.associate_mem.add_thought(
        created,
        expiration,
        s,
        p,
        o,
        thought,
        keywords,
        thought_poignancy,
        thought_embedding_pair,
        None,
    )


def generate_task_decomp(persona, task, duration):
    return run_prompt_task_decomp(persona, task, duration)


def generate_action_sector(act_desp, persona, maze):
    return run_prompt_action_sector(act_desp, persona, maze)


def generate_action_area(act_desp, persona, maze, act_world, act_sector):
    return run_prompt_action_area(act_desp, persona, maze, act_world, act_sector)


def generate_action_object(act_desp, act_address, persona, maze):
    if not persona.spatial_mem.get_str_accessible_area_objects(act_address):
        return "<random>"
    return run_prompt_action_object(act_desp, persona, maze, act_address)


def generate_action_event_triple(act_desp, persona):
    return run_prompt_event_triple(act_desp, persona)


def generate_act_obj_desc(act_object, act_desp, persona):
    return run_prompt_act_obj_desc(act_object, act_desp, persona)


def generate_act_obj_event_triple(act_object, act_obj_desc):
    output = (act_object, "正在", act_obj_desc)
    # print("generate_act_obj_event_triple output:", output)
    return output
    # return run_prompt_act_obj_event_triple(act_object, act_obj_desc, persona)


def generate_decide_to_talk(init_persona, target_persona, focused_event):
    return run_prompt_decide_to_talk(init_persona, target_persona, focused_event)


def generate_decide_to_react(init_persona, target_persona, focused_event):
    return run_prompt_decide_to_react(init_persona, target_persona, focused_event)


def generate_new_decomp_schedule(
    persona, inserted_act, inserted_act_dur, start_hour, end_hour
):
    # Step 1: Setting up the core variables for the function.
    # <p> is the persona whose schedule we are editing right now.
    p = persona
    # <today_min_pass> indicates the number of minutes that have passed today.
    today_min_pass = (
        int(p.direct_mem.curr_time.hour) * 60 + int(p.direct_mem.curr_time.minute) + 1
    )

    # Step 2: We need to create <main_act_dur> and <truncated_act_dur>.
    # These are basically a sub-component of <daily_schedule> of the persona,
    # but focusing on the current decomposition.
    # Here is an example for <main_act_dur>:
    # ['wakes up and completes her morning routine (wakes up at 6am)', 5]
    # ['wakes up and completes her morning routine (wakes up at 6am)', 5]
    # ['wakes up and completes her morning routine (uses the restroom)', 5]
    # ['wakes up and completes her morning routine (washes her ...)', 10]
    # ['wakes up and completes her morning routine (makes her bed)', 5]
    # ['wakes up and completes her morning routine (eats breakfast)', 15]
    # ['wakes up and completes her morning routine (gets dressed)', 10]
    # ['wakes up and completes her morning routine (leaves her ...)', 5]
    # ['wakes up and completes her morning routine (starts her ...)', 5]
    # ['preparing for her day (waking up at 6am)', 5]
    # ['preparing for her day (making her bed)', 5]
    # ['preparing for her day (taking a shower)', 15]
    # ['preparing for her day (getting dressed)', 5]
    # ['preparing for her day (eating breakfast)', 10]
    # ['preparing for her day (brushing her teeth)', 5]
    # ['preparing for her day (making coffee)', 5]
    # ['preparing for her day (checking her email)', 5]
    # ['preparing for her day (starting to work on her painting)', 5]
    #
    # And <truncated_act_dur> concerns only until where an event happens.
    # ['wakes up and completes her morning routine (wakes up at 6am)', 5]
    # ['wakes up and completes her morning routine (wakes up at 6am)', 2]
    main_act_dur = []
    truncated_act_dur = []
    dur_sum = 0  # duration sum
    count = 0  # enumerate count
    truncated_fin = False

    print("DEBUG::: ", persona.direct_mem.name)
    for act, dur in p.direct_mem.daily_schedule:
        if (dur_sum >= start_hour * 60) and (dur_sum < end_hour * 60):
            main_act_dur += [[act, dur]]
            if dur_sum <= today_min_pass:
                truncated_act_dur += [[act, dur]]
            elif dur_sum > today_min_pass and not truncated_fin:
                # We need to insert that last act, duration list like this one:
                # e.g., ['wakes up and completes her morning routine (wakes up...)', 2]
                truncated_act_dur += [
                    [p.direct_mem.daily_schedule[count][0], dur_sum - today_min_pass]
                ]
                truncated_act_dur[-1][-1] -= (
                    dur_sum - today_min_pass
                )  ######## DEC 7 DEBUG;.. is the +1 the right thing to do???
                # truncated_act_dur[-1][-1] -= (dur_sum - today_min_pass + 1) ######## DEC 7 DEBUG;.. is the +1 the right thing to do???
                print("DEBUG::: ", truncated_act_dur)

                # truncated_act_dur[-1][-1] -= (dur_sum - today_min_pass) ######## DEC 7 DEBUG;.. is the +1 the right thing to do???
                truncated_fin = True
        dur_sum += dur
        count += 1

    persona_name = persona.name
    main_act_dur = main_act_dur

    x = (
        truncated_act_dur[-1][0].split("（")[0].strip()
        + "（即将去 "  # on the way to
        + truncated_act_dur[-1][0].split("（")[-1][:-1]
        + "）"
    )
    truncated_act_dur[-1][0] = x

    if "（" in truncated_act_dur[-1][0]:
        inserted_act = (
            truncated_act_dur[-1][0].split("（")[0].strip() + "（" + inserted_act + "）"
        )

    # To do inserted_act_dur+1 below is an important decision but I'm not sure
    # if I understand the full extent of its implications. Might want to
    # revisit.
    truncated_act_dur += [[inserted_act, inserted_act_dur]]
    start_time_hour = datetime.datetime(2022, 10, 31, 0, 0) + datetime.timedelta(
        hours=start_hour
    )
    end_time_hour = datetime.datetime(2022, 10, 31, 0, 0) + datetime.timedelta(
        hours=end_hour
    )
    return run_prompt_new_decomp_schedule(
        persona,
        main_act_dur,
        truncated_act_dur,
        start_time_hour,
        end_time_hour,
        inserted_act,
        inserted_act_dur,
    )


def generate_convo(maze, init_persona, target_persona):
    # curr_loc = maze.access_cell(init_persona.direct_mem.curr_cell)

    # convo = run_gpt_prompt_create_conversation(init_persona, target_persona, curr_loc)[0]
    # convo = agent_chat_v1(maze, init_persona, target_persona)
    convo = agent_chat_v2(maze, init_persona, target_persona)
    all_utt = ""

    for row in convo:
        speaker = row[0]
        utt = row[1]
        all_utt += f"{speaker}: {utt}\n"

    convo_length = math.ceil(int(len(all_utt) / 8) / 30)
    return convo, convo_length


def generate_convo_summary(persona, convo):
    convo_summary = run_prompt_summarize_conversation(persona, convo)
    return convo_summary


def determine_action(persona, maze):
    def determine_decomp(act_desp, act_dura):
        if "睡觉" in act_desp:
            return False
        # if act_desp == "离开小区":
        #     return False

        # elif "sleep" in act_desp or "bed" in act_desp:
        #     if act_dura > 60:
        #         return False
        return True

    curr_index = persona.direct_mem.get_daily_schedule_index()
    # 返回当前时间下所属任务所在的index
    curr_index_60 = persona.direct_mem.get_daily_schedule_index(advance=60)
    # 返回当前时间+60分钟后所属任务所在的index（可能和当前任务相同）

    # 若为首次分解，分解当前时间任务
    if curr_index == 0:
        act_desp, act_dura = persona.direct_mem.daily_schedule[curr_index]
        if act_dura >= 60 and determine_decomp(act_desp, act_dura):
            persona.direct_mem.daily_schedule[curr_index : curr_index + 1] = (
                generate_task_decomp(persona, act_desp, act_dura)
            )
        if curr_index_60 + 1 < len(persona.direct_mem.daily_schedule):
            # 分解一小时后的任务 的 下一个任务
            act_desp, act_dura = persona.direct_mem.daily_schedule[curr_index_60 + 1]
            if act_dura >= 60 and determine_decomp(act_desp, act_dura):
                persona.direct_mem.daily_schedule[
                    curr_index_60 + 1 : curr_index_60 + 2
                ] = generate_task_decomp(persona, act_desp, act_dura)

    # 分解一小时后的任务
    if curr_index_60 < len(persona.direct_mem.daily_schedule):
        if persona.direct_mem.curr_time.hour < 23:  # 如果23:00之前
            act_desp, act_dura = persona.direct_mem.daily_schedule[curr_index_60]
            # 一小时后的任务
            if act_dura >= 60 and determine_decomp(act_desp, act_dura):
                # 如果一小时后的任务时长大于60分钟（应该一般都不低于一小时）
                persona.direct_mem.daily_schedule[
                    curr_index_60 : curr_index_60
                    + 1  # 替换的只有一小时后的任务（分解成分钟任务）
                ] = generate_task_decomp(persona, act_desp, act_dura)

    # print_c("<determine_action> output")
    # determine_action_output = ""
    # for i in persona.direct_mem.daily_schedule:
    #     determine_action_output += str(i) + "\n"
    # print_c(determine_action_output)
    # print_c("<determine_action> end")

    # 1440
    total_time = 0
    for i in persona.direct_mem.daily_schedule:
        total_time += i[1]
    # print ("total_time", total_time)

    if 1440 - total_time > 0:
        print("total_time", total_time)
        persona.direct_mem.daily_schedule += [["睡觉", 1440 - total_time]]

    act_desp, act_dura = persona.direct_mem.daily_schedule[curr_index]

    # Finding the target location of the action and creating action-related
    # variables.
    act_world = maze.access_cell(persona.direct_mem.curr_cell)["world"]
    # act_sector = maze.access_cell(persona.direct_mem.curr_cell)["sector"]
    if act_desp == "离开小区":
        new_address = f"{act_world}:小区大门:小区大门:<小区外部>"

        act_obj_desp = "<小区外部>"
        act_obj_event = (None, None, None)
    else:
        act_sector = generate_action_sector(act_desp, persona, maze)
        act_area = generate_action_area(act_desp, persona, maze, act_world, act_sector)
        act_address = f"{act_world}:{act_sector}:{act_area}"
        act_object = generate_action_object(act_desp, act_address, persona, maze)
        new_address = f"{act_world}:{act_sector}:{act_area}:{act_object}"

        act_obj_desp = generate_act_obj_desc(act_object, act_desp, persona)
        act_obj_event = generate_act_obj_event_triple(act_object, act_obj_desp)

    act_event = generate_action_event_triple(act_desp, persona)

    persona.direct_mem.add_new_action(
        new_address,
        int(act_dura),
        act_desp,
        act_event,
        None,
        None,
        None,
        None,
        act_obj_desp,
        act_obj_event,
    )


def _choose_retrieved(persona, retrieved):
    # 清除persona自身事件
    copy_retrieved = retrieved.copy()
    for event_desc, rel_ctx in copy_retrieved.items():
        curr_event = rel_ctx["curr_event"]
        if curr_event.subject == persona.name:
            del retrieved[event_desc]

    # 首选persona相关事件
    priority = []
    for event_desc, rel_ctx in retrieved.items():
        curr_event = rel_ctx["curr_event"]
        if ":" not in curr_event.subject and curr_event.subject != persona.name:
            priority += [rel_ctx]
    if priority:
        return random.choice(priority)

    # 过滤对象的空闲事件(object正在空闲)，选择剩余事件
    for event_desc, rel_ctx in retrieved.items():
        curr_event = rel_ctx["curr_event"]
        if "正在 空闲" not in event_desc:
            priority += [rel_ctx]
    if priority:
        return random.choice(priority)
    return None


def _should_react(persona, retrieved, personas):
    def lets_talk(init_persona, target_persona, retrieved):
        if (
            not target_persona.direct_mem.act_address
            or not target_persona.direct_mem.act_description
            or not init_persona.direct_mem.act_address
            or not init_persona.direct_mem.act_description
        ):
            return False

        if (
            "睡觉" in target_persona.direct_mem.act_description
            or "睡觉" in init_persona.direct_mem.act_description
        ):
            return False

        if init_persona.direct_mem.curr_time.hour == 23:
            return False

        if "<等待>" in target_persona.direct_mem.act_address:
            return False

        if (
            target_persona.direct_mem.chatting_with
            or init_persona.direct_mem.chatting_with
        ):
            return False

        if target_persona.name in init_persona.direct_mem.chatting_with_buffer:
            if init_persona.direct_mem.chatting_with_buffer[target_persona.name] > 0:
                return False

        if generate_decide_to_talk(init_persona, target_persona, retrieved):
            return True

        return False

    def lets_react(init_persona, target_persona, retrieved):
        if (
            not target_persona.direct_mem.act_address
            or not target_persona.direct_mem.act_description
            or not init_persona.direct_mem.act_address
            or not init_persona.direct_mem.act_description
        ):
            return False

        if (
            "睡觉" in target_persona.direct_mem.act_description
            or "睡觉" in init_persona.direct_mem.act_description
        ):
            return False

        if init_persona.direct_mem.curr_time.hour == 23:
            return False

        if "等待" in target_persona.direct_mem.act_description:
            return False
        if init_persona.direct_mem.planned_path == []:
            return False

        if init_persona.direct_mem.act_address != target_persona.direct_mem.act_address:
            return False

        react_mode = generate_decide_to_react(init_persona, target_persona, retrieved)

        if react_mode == "1":
            wait_until = (
                target_persona.direct_mem.act_start_time
                + datetime.timedelta(minutes=target_persona.direct_mem.act_duration - 1)
            ).strftime("%B %d, %Y, %H:%M:%S")
            return ("wait", wait_until)
        elif react_mode == "2":
            return False

    if persona.direct_mem.chatting_with:  # 若对方正在聊天，则不react
        return False
    if "<等待>" in persona.direct_mem.act_address:  # 若对方正在等待，则不react
        return False

    curr_event = retrieved["curr_event"]

    if ":" not in curr_event.subject:  # 只处理persona事件
        target_persona = personas[curr_event.subject]
        if lets_talk(persona, target_persona, retrieved):  # 决定是否talk
            react_mode = ("chat", curr_event.subject)
            return react_mode  # ("chat", persona name)
        react_mode = lets_react(persona, target_persona, retrieved)
        # 如果不决定talk，才判断是否等待对方的行为（主要是避免使用对象冲突）
        return react_mode  # ("wait", wait_until)
    return False


def _create_react(
    persona,
    inserted_act,
    inserted_act_dur,
    act_address,
    act_event,
    chatting_with,
    chat,
    chatting_with_buffer,
    chatting_end_time,
    # act_pronunciatio,
    act_obj_description,
    # act_obj_pronunciatio,
    act_obj_event,
    act_start_time=None,
):
    p = persona

    min_sum = 0
    for i in range(p.direct_mem.get_daily_schedule_index()):
        min_sum += p.direct_mem.daily_schedule_hourly[i][1]
    start_hour = int(min_sum / 60)

    if (
        p.direct_mem.daily_schedule_hourly[p.direct_mem.get_daily_schedule_index()][1]
        >= 120
    ):
        end_hour = (
            start_hour
            + p.direct_mem.daily_schedule_hourly[
                p.direct_mem.get_daily_schedule_index()
            ][1]
            / 60
        )

    elif (
        p.direct_mem.daily_schedule_hourly[p.direct_mem.get_daily_schedule_index()][1]
        + p.direct_mem.daily_schedule_hourly[
            p.direct_mem.get_daily_schedule_index() + 1
        ][1]
    ):
        end_hour = start_hour + (
            (
                p.direct_mem.daily_schedule_hourly[
                    p.direct_mem.get_daily_schedule_index()
                ][1]
                + p.direct_mem.daily_schedule_hourly[
                    p.direct_mem.get_daily_schedule_index() + 1
                ][1]
            )
            / 60
        )

    else:
        end_hour = start_hour + 2
    end_hour = int(end_hour)

    dur_sum = 0
    count = 0
    start_index = None
    end_index = None
    for act, dur in p.direct_mem.daily_schedule:
        if dur_sum >= start_hour * 60 and start_index == None:
            start_index = count
        if dur_sum >= end_hour * 60 and end_index == None:
            end_index = count
        dur_sum += dur
        count += 1

    ret = generate_new_decomp_schedule(
        p, inserted_act, inserted_act_dur, start_hour, end_hour
    )
    p.direct_mem.daily_schedule[start_index:end_index] = ret
    p.direct_mem.add_new_action(
        act_address,
        inserted_act_dur,
        inserted_act,
        # act_pronunciatio,
        act_event,
        chatting_with,
        chat,
        chatting_with_buffer,
        chatting_end_time,
        act_obj_description,
        # act_obj_pronunciatio,
        act_obj_event,
        act_start_time,
    )


def _chat_react(maze, persona, target_persona, personas):
    # There are two personas -- the persona who is initiating the conversation
    # and the persona who is the target. We get the persona instances here.
    init_persona = persona
    target_persona = personas[target_persona]

    # Actually creating the conversation here.
    convo, duration_min = generate_convo(maze, init_persona, target_persona)
    convo_summary = generate_convo_summary(init_persona, convo)
    inserted_act = convo_summary
    inserted_act_dur = duration_min

    act_start_time = target_persona.direct_mem.act_start_time

    curr_time = target_persona.direct_mem.curr_time
    if curr_time.second != 0:
        temp_curr_time = curr_time + datetime.timedelta(seconds=60 - curr_time.second)
        chatting_end_time = temp_curr_time + datetime.timedelta(
            minutes=inserted_act_dur
        )  # ?为什么要加到 整分钟 再加 对话min数？
    else:
        chatting_end_time = curr_time + datetime.timedelta(minutes=inserted_act_dur)

    for role, p in [("init", init_persona), ("target", target_persona)]:
        if role == "init":
            act_address = f"<persona> {target_persona.name}"
            act_event = (p.name, "聊天", target_persona.name)  # chat with
            chatting_with = target_persona.name
            chatting_with_buffer = {}
            chatting_with_buffer[target_persona.name] = 800
        elif role == "target":
            act_address = f"<persona> {init_persona.name}"
            act_event = (p.name, "聊天", init_persona.name)
            chatting_with = init_persona.name
            chatting_with_buffer = {}
            chatting_with_buffer[init_persona.name] = 800

        # act_pronunciatio = "💬"
        act_obj_description = None
        # act_obj_pronunciatio = None
        act_obj_event = (None, None, None)

        _create_react(
            p,
            inserted_act,
            inserted_act_dur,
            act_address,
            act_event,
            chatting_with,
            convo,
            chatting_with_buffer,
            chatting_end_time,
            # act_pronunciatio,
            act_obj_description,
            # act_obj_pronunciatio,
            act_obj_event,
            act_start_time,
        )


def _wait_react(persona, wait_time):
    p = persona

    inserted_act = f'等待开始 {p.direct_mem.act_description.split("（")[-1][:-1]}'
    end_time = datetime.datetime.strptime(wait_time, "%B %d, %Y, %H:%M:%S")
    inserted_act_dur = (
        (end_time.minute + end_time.hour * 60)
        - (p.direct_mem.curr_time.minute + p.direct_mem.curr_time.hour * 60)
        + 1
    )

    act_address = f"<等待> {p.direct_mem.curr_cell[0]} {p.direct_mem.curr_cell[1]}"
    act_event = (
        p.name,
        "等待开始",
        p.direct_mem.act_description.split("（")[-1][:-1],
    )
    chatting_with = None
    chat = None
    chatting_with_buffer = None
    chatting_end_time = None

    # act_pronunciatio = "⌛"
    act_obj_description = None
    # act_obj_pronunciatio = None
    act_obj_event = (None, None, None)

    _create_react(
        p,
        inserted_act,
        inserted_act_dur,
        act_address,
        act_event,
        chatting_with,
        chat,
        chatting_with_buffer,
        chatting_end_time,
        # act_pronunciatio,
        act_obj_description,
        # act_obj_pronunciatio,
        act_obj_event,
    )


def plan(persona, maze, personas, new_day, retrieved):
    # plan小时计划（min单位）
    if new_day:  # 如果是同一天内，new_day=False
        # print_c("_new_day_planning start", COLOR="blue")
        _new_day_planning(persona, new_day)
        # print_c("_new_day_planning done", COLOR="blue")

    # 如果当前时间下的action已到期，新建一个action
    if persona.direct_mem.act_check_finished():
        # print_c("determine_action start", COLOR="blue")
        determine_action(persona, maze)
        # print_c("determine_action done", COLOR="blue")

    # 决定要关注哪个事件（有且有多个events被检索到）
    # print_c("_choose_retrieved start", COLOR="blue")
    focused_event = False
    if retrieved.keys():
        focused_event = _choose_retrieved(persona, retrieved)
    # print_c("_choose_retrieved done", COLOR="blue")

    # 决定对事件作什么反应
    if focused_event:
        # print_c("_should_react start", COLOR="blue")
        reaction_mode = _should_react(persona, focused_event, personas)
        print("reaction_mode:", reaction_mode)
        # print_c("_should_react done", COLOR="blue")
        if reaction_mode:
            if reaction_mode[0] == "chat":  # ("chat", persona name)
                _chat_react(maze, persona, reaction_mode[1], personas)
            elif reaction_mode[0] == "wait":  # ("wait", wait_until)
                _wait_react(persona, reaction_mode[1])

    if persona.direct_mem.act_event[1] != "聊天":
        persona.direct_mem.chatting_with = None
        persona.direct_mem.chat = None
        persona.direct_mem.chatting_end_time = None
    # We want to make sure that the persona does not keep conversing with each
    # other in an infinite loop. So, chatting_with_buffer maintains a form of
    # buffer that makes the persona wait from talking to the same target
    # immediately after chatting once. We keep track of the buffer value here.
    curr_persona_chat_buffer = persona.direct_mem.chatting_with_buffer
    for persona_name, buffer_count in curr_persona_chat_buffer.items():
        if persona_name != persona.direct_mem.chatting_with:
            persona.direct_mem.chatting_with_buffer[persona_name] -= 1

    return persona.direct_mem.act_address
