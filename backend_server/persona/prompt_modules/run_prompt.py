"""
定义运行prompt的所有函数
"""

import datetime
import random
import string
import re
import sys
import json
import inspect

sys.path.append("../../")
from persona.prompt_modules.llm_structure import *
from global_methods import *

from utils import *


import inspect


def print_prompt_output(persona_name, prompt, output, elapsed_time, simple_log=False):
    func_name = inspect.stack()[1].function
    if not simple_log:
        output_str = (
            f"╔═════{persona_name}:<{func_name}>═════╗\n"
            + "  prompt: \n"
            + str(prompt)
            + "\n═══════════════════════════════════════════\n"
            + "  output: \n"
            + str(output)
            + f"\n  elapsed_time: {elapsed_time:.2f}s"
            + "\n╚═════════════════════════════════════════╝"
        )
        print_c(output_str)


def get_random_alphanumeric(i=6, j=6):
    k = random.randint(i, j)
    x = "".join(random.choices(string.ascii_letters + string.digits, k=k))
    return x


def extract_first_json_dict(data_str):
    # Find the first occurrence of a JSON object within the string
    start_idx = data_str.find("{")
    end_idx = data_str.find("}", start_idx) + 1

    # Check if both start and end indices were found
    if start_idx == -1 or end_idx == 0:
        return None

    # Extract the first JSON dictionary
    json_str = data_str[start_idx:end_idx]

    try:
        # Attempt to parse the JSON data
        json_dict = json.loads(json_str)
        return json_dict
    except json.JSONDecodeError:
        # If parsing fails, return None
        return None


def run_prompt_wake_up_time(persona):
    """

    返回给定persona的起床时间(integer)
    """
    if develop and persona.name == "李华":
        output = 6
        print("run_prompt_wake_up_time\n", output)
        return output

    def create_prompt_input(persona):
        prompt_input = [persona.direct_mem.get_str_mds()]
        return prompt_input

    def response_clean(response, prompt=""):
        return int(response.strip().lower().split("am")[0])

    def response_validate(response, prompt=""):
        try:
            response_clean(response, prompt=prompt)
        except:
            return False
        return True

    def get_fail_safe():
        fs = 7
        return fs

    model_param = {
        "model": specify_model,
        "max_tokens": 5,
        "temperature": 0.5,
        "top_p": 1,
        "stream": False,
        "stop": None,
    }
    prompt_file_path = f"{prompt_path}/plan/wake_up_time_v1.txt"
    prompt_input = create_prompt_input(persona)
    prompt = generate_prompt(prompt_input, prompt_file_path)
    output, elapsed_time = generate_response(
        prompt,
        model_param,
        func_clean=response_clean,
        func_valid=response_validate,
        get_fail_safe=get_fail_safe(),
    )
    print_prompt_output(persona.name, prompt, output, elapsed_time, True)
    return output


def run_prompt_daily_goals(persona, wake_up_time):
    if develop and persona.name == "李华":
        output = [
            "6点起床",
            "6点起床并完成洗漱和早饭",
            "7点到12点营业超市",
            "12点到13点去小区饭馆吃饭",
            "13点到22点继续营业超市",
            "22点到23点结束营业并回家休息",
        ]
        print("run_prompt_daily_goals\n", output)
        return output

    def create_prompt_input(persona, wake_up_time):
        prompt_input = []
        prompt_input += [persona.direct_mem.get_str_mds()]
        # prompt_input += [persona.direct_mem.get_curr_date()]
        # prompt_input += [f"{str(wake_up_time)}"]
        return prompt_input

    def response_clean(response, prompt=""):
        cl = []
        _cl = re.split(r"[)）]", response)
        for i in _cl[1:]:
            if i[-1].isdigit():
                i = i[:-1].strip()
            if i[-1] in [".", ",", "，", "。"]:
                cl += [i[:-1].strip()]
            else:
                cl += [i.strip()]
        return cl

    def response_validate(response, prompt=""):
        try:
            response_clean(response, prompt=prompt)
        except Exception as e:
            print(e)
            return False
        return True

    def get_fail_safe():
        fs = [
            "6点起床并完成洗漱和早饭",
            "7点到8点出门锻炼",
            "8点到11点回家看电视",
            "11点到12点出门买菜",
            "12点到13点在家做午饭并用餐",
            "13点到15点在家午休睡觉",
            "15点到18点在家看手机",
            "18点到19点出门去小区餐馆吃饭",
            "19点到20点散步锻炼",
            "20点到21点洗漱并准备睡觉",
            "22点上床睡觉",
        ]
        return fs

    model_param = {
        "model": specify_model,
        "max_tokens": 250,
        "temperature": 0.8,
        "top_p": 1,
        "stream": False,
        "stop": None,
    }
    prompt_file_path = f"{prompt_path}/plan/daily_planning_v1.txt"
    prompt_input = create_prompt_input(persona, wake_up_time)
    prompt = generate_prompt(prompt_input, prompt_file_path)
    output, elapsed_time = generate_response(
        prompt,
        model_param,
        func_clean=response_clean,
        func_valid=response_validate,
        get_fail_safe=get_fail_safe(),
    )
    output = [f"{wake_up_time}点起床"] + output
    print_prompt_output(persona.name, prompt, output, elapsed_time, True)
    return output


def run_prompt_generate_hourly_schedule(
    persona, curr_hour_str, hourly_activity, hour_str
):
    def create_prompt_input(persona, curr_hour_str, hourly_activity, hour_str):
        schedule_format = ""
        for i in hour_str:
            schedule_format += f"[{persona.direct_mem.get_curr_date()} - {i}]"
            schedule_format += f" 活动:[待填入]\n"
        schedule_format = schedule_format[:-1]

        daily_plan_intro = f"以下为{persona.direct_mem.get_name()}的大致日程:"
        for count, goal in enumerate(persona.direct_mem.daily_goals):
            daily_plan_intro += f"{str(count+1)}) {goal},"
        daily_plan_intro = daily_plan_intro[:-1]

        prior_schedule = ""
        if hourly_activity:
            prior_schedule = "\n"
        for count, i in enumerate(hourly_activity):
            prior_schedule += f"[(ID:{get_random_alphanumeric()})"
            prior_schedule += f" {persona.direct_mem.get_curr_date()} -"
            prior_schedule += f" {hour_str[count]}] 活动:"
            prior_schedule += f" {persona.direct_mem.get_name()}"
            prior_schedule += f" 正在 {i}\n"

        prompt_ending = f"[(ID:{get_random_alphanumeric()})"
        prompt_ending += f" {persona.direct_mem.get_curr_date()}"
        prompt_ending += f" - {curr_hour_str}] 活动:"
        prompt_ending += f" {persona.direct_mem.get_name()} 正在"

        prompt_input = []
        prompt_input += [schedule_format]
        prompt_input += [persona.direct_mem.get_str_mds()]

        prompt_input += [prior_schedule + "\n"]
        prompt_input += [daily_plan_intro]
        prompt_input += [prompt_ending]

        return prompt_input

    def response_clean(response, prompt=""):
        cl = response.strip().split()[-1]
        if cl[0] == "[":
            raise ValueError()
        if cl[-1] in [".", "。"]:
            cl = cl[:-1]
        return cl

    def response_validate(response, prompt=""):
        try:
            response_clean(response, prompt=prompt)
        except:
            return False
        return True

    def get_fail_safe():
        fs = "打发时间"
        return fs

    model_param = {
        "model": specify_model,
        "max_tokens": 120,
        "temperature": 1.3,
        "top_p": 1,
        "stream": False,
        "stop": None,
    }
    prompt_template = f"{prompt_path}/plan/hourly_schedule_v1.txt"
    prompt_input = create_prompt_input(
        persona, curr_hour_str, hourly_activity, hour_str
    )
    prompt = generate_prompt(prompt_input, prompt_template)
    output, elapsed_time = generate_response(
        prompt,
        model_param,
        func_clean=response_clean,
        func_valid=response_validate,
        get_fail_safe=get_fail_safe(),
    )
    print_prompt_output(persona.name, prompt, output, elapsed_time)
    return output


def run_prompt_simple_generate_hourly_schedule(
    persona, hour_str, wake_up_time, outing_time, new_day
):
    def create_prompt_input(persona, hour_str, wake_up_time, outing_time):
        schedule_format = ""
        for idx, i in enumerate(hour_str[:-1]):
            if idx > wake_up_time - 1:
                schedule_format += f"[{hour_str[idx]} - {hour_str[idx+1]}]"
                if outing_time and idx in outing_time:
                    schedule_format += (
                        f" 活动: {persona.direct_mem.name} 正在 离开小区\n"
                    )
                else:
                    schedule_format += f" 活动: 待填入\n"
        schedule_format += "[23:00 - 24:00] 活动: 待填入"
        if new_day == "first":
            daily_plan_intro = f"以下为{persona.direct_mem.get_name()}的大致日程:"
            for count, goal in enumerate(persona.direct_mem.daily_goals):
                daily_plan_intro += f"{str(count+1)}) {goal},"
            daily_plan_intro = daily_plan_intro[:-1]
        else:
            daily_plan_intro = ""
        prompt_input = []
        prompt_input += [schedule_format]
        prompt_input += [persona.direct_mem.get_str_mds()]
        prompt_input += [daily_plan_intro]

        return prompt_input

    def response_clean(response, prompt=""):
        if response[0] != "[":
            raise ValueError()
        else:
            return response

    def response_validate(response, prompt=""):
        try:
            response_clean(response, prompt=prompt)
        except:
            return False
        return True

    def get_fail_safe():
        fs = "Failure"
        return fs

    model_param = {
        "model": specify_model,
        "max_tokens": 800,
        "temperature": 0,
        "top_p": 1,
        "stream": False,
        "stop": None,
    }
    prompt_template = f"{prompt_path}/plan/hourly_schedule_Sv1.txt"
    prompt_input = create_prompt_input(persona, hour_str, wake_up_time, outing_time)
    prompt = generate_prompt(prompt_input, prompt_template)
    output, elapsed_time = generate_response(
        prompt,
        model_param,
        func_clean=response_clean,
        func_valid=response_validate,
        get_fail_safe=get_fail_safe(),
    )
    print_prompt_output(persona.name, prompt, output, elapsed_time)
    return output


def run_prompt_task_decomp(persona, task, duration):
    def create_prompt_input(persona, task, duration):
        curr_f_org_index = persona.direct_mem.get_daily_schedule_hourly_index()
        all_indices = []
        # if curr_f_org_index > 0:
        #   all_indices += [curr_f_org_index-1]
        all_indices += [curr_f_org_index]
        if curr_f_org_index + 1 <= len(persona.direct_mem.daily_schedule_hourly):
            all_indices += [curr_f_org_index + 1]
        if curr_f_org_index + 2 <= len(persona.direct_mem.daily_schedule_hourly):
            all_indices += [curr_f_org_index + 2]
        # print("<run_prompt_task_decomp> all_indices:", all_indices)

        curr_time_range = ""
        curr_task = ""

        summ_str = f'今天日期是 {persona.direct_mem.curr_time.strftime("%A %B %d")}。 '
        summ_str += f"从 "
        for index in all_indices:
            # print("index", index)
            if index < len(persona.direct_mem.daily_schedule_hourly):
                start_min = 0
                for i in range(index):
                    start_min += persona.direct_mem.daily_schedule_hourly[i][1]
                end_min = start_min + persona.direct_mem.daily_schedule_hourly[index][1]
                start_time = datetime.datetime.strptime(
                    "00:00:00", "%H:%M:%S"
                ) + datetime.timedelta(minutes=start_min)
                end_time = datetime.datetime.strptime(
                    "00:00:00", "%H:%M:%S"
                ) + datetime.timedelta(minutes=end_min)
                start_time_str = start_time.strftime("%H:%M")
                end_time_str = end_time.strftime("%H:%M")
                summ_str += f"{start_time_str} ~ {end_time_str}点, {persona.direct_mem.name} 正在 {persona.direct_mem.daily_schedule_hourly[index][0]}, "
                if curr_f_org_index + 1 == index:  # 当前index是下一个任务的index
                    curr_time_range = f"{start_time_str} ~ {end_time_str}"
                    curr_task = persona.direct_mem.daily_schedule_hourly[index][0]
        summ_str = summ_str[:-2] + "。"

        prompt_input = []
        prompt_input += [persona.direct_mem.get_str_mds()]
        prompt_input += [summ_str]
        prompt_input += [persona.direct_mem.name]
        prompt_input += [curr_time_range]

        prompt_input += [task]

        prompt_input += [duration]
        prompt_input += [persona.direct_mem.name]
        return prompt_input

    def response_clean(response, prompt=""):
        temp = [i.strip() for i in response.strip("\n").split("\n")]
        _cr = []
        cr = []
        for count, i in enumerate(temp):
            _cr += [" ".join([j.strip() for j in i.split(" ")][2:])]
        for count, i in enumerate(_cr):
            k = [j.strip() for j in i.split("（分钟时长：")]
            task = k[0]
            if task[-1] == "。":
                task = task[:-1]
            duration = int(k[1].split("，")[0].strip())
            cr += [[task, duration]]

        total_expected_min = int(prompt.split("（总时长：")[-1].split("）")[0].strip())

        curr_min_slot = [
            ["dummy", -1],
        ]  # (task_name, task_index)
        for count, i in enumerate(cr):
            i_task = i[0]
            i_duration = i[1]

            i_duration -= i_duration % 5
            if i_duration > 0:
                for j in range(i_duration):
                    curr_min_slot += [(i_task, count)]
        curr_min_slot = curr_min_slot[1:]

        if len(curr_min_slot) > total_expected_min:
            last_task = curr_min_slot[60]
            for i in range(1, 6):
                curr_min_slot[-1 * i] = last_task
        elif len(curr_min_slot) < total_expected_min:
            last_task = curr_min_slot[-1]
            for i in range(total_expected_min - len(curr_min_slot)):
                curr_min_slot += [last_task]

        cr_ret = [
            ["dummy", -1],
        ]
        for task, task_index in curr_min_slot:
            if task != cr_ret[-1][0]:
                cr_ret += [[task, 1]]
            else:
                cr_ret[-1][1] += 1
        cr = cr_ret[1:]
        return cr

    def response_validate(response, prompt=""):
        try:
            response_clean(response, prompt=prompt)
        except:
            return False
        return True

    def get_fail_safe():
        fs = "打发时间"
        return fs

    model_param = {
        "model": specify_CoT_model,
        "max_tokens": 4096,
        "temperature": 0,
        "top_p": 1,
        "stream": False,
        "stop": None,
    }
    prompt_template = f"{prompt_path}/plan/task_decomp_v2.txt"
    prompt_input = create_prompt_input(persona, task, duration)
    prompt = generate_prompt(prompt_input, prompt_template)
    output, elapsed_time = generate_response(
        prompt,
        model_param,
        func_clean=response_clean,
        func_valid=response_validate,
        get_fail_safe=get_fail_safe(),
    )
    task_decomp = output
    ret = []
    for decomp_task, duration in task_decomp:
        ret += [[f"{task}（{decomp_task}）", duration]]
    output = ret
    print_prompt_output(persona.name, prompt, output, elapsed_time)
    return output


def run_prompt_action_sector(act_desp, persona, maze):
    def create_prompt_input(act_desp, persona, maze):
        act_world = f"{maze.access_cell(persona.direct_mem.curr_cell)['world']}"

        prompt_input = []
        prompt_input += [persona.direct_mem.get_str_mds()]

        prompt_input += [persona.direct_mem.get_name()]  # 1
        prompt_input += [persona.direct_mem.living_area.split(":")[1]]
        x = f"{act_world}:{persona.direct_mem.living_area.split(':')[1]}"
        prompt_input += [persona.spatial_mem.get_str_accessible_sector_areas(x)]  # 3

        prompt_input += [persona.direct_mem.get_name()]
        prompt_input += [
            f"{maze.access_cell(persona.direct_mem.curr_cell)['sector']}"
        ]  # 5
        x = f"{act_world}:{maze.access_cell(persona.direct_mem.curr_cell)['sector']}"
        if maze.access_cell(persona.direct_mem.curr_cell)["sector"] != "小区大门":
            prompt_input += [persona.spatial_mem.get_str_accessible_sector_areas(x)]
        else:
            prompt_input += ["小区大门"]

        if persona.direct_mem.get_daily_plan_desc() != "":  # 7
            prompt_input += [f"\n{persona.direct_mem.get_daily_plan_desc()}"]
        else:
            prompt_input += [""]

        prompt_input += [persona.spatial_mem.get_str_accessible_sectors(act_world)]

        action_desc_1 = act_desp
        action_desc_2 = act_desp
        if "（" in act_desp:
            action_desc_1 = act_desp.split("（")[0].strip()
            action_desc_2 = act_desp.split("（")[-1][:-1]
        prompt_input += [persona.direct_mem.get_name()]
        prompt_input += [action_desc_1]  # 10

        prompt_input += [action_desc_2]
        prompt_input += [persona.direct_mem.get_name()]  # 12
        return prompt_input

    def response_clean(response, prompt=""):
        return response

    def response_validate(response, prompt=""):
        try:
            cleaned_up = response_clean(response, prompt=prompt)
            act_world = f"{maze.access_cell(persona.direct_mem.curr_cell)['world']}"
            if cleaned_up not in persona.spatial_mem.get_str_accessible_sectors(
                act_world
            ):
                return False
        except:
            return False
        return True

    def get_fail_safe():
        fs = persona.direct_mem.living_area.split(":")[1]
        return fs

    model_param = {
        "model": specify_model,
        "max_tokens": 20,
        "temperature": 0,
        "top_p": 1,
        "stream": False,
        "stop": None,
    }
    prompt_template = f"{prompt_path}/plan/action_location_sector_v1.txt"
    prompt_input = create_prompt_input(act_desp, persona, maze)
    prompt = generate_prompt(prompt_input, prompt_template)
    output, elapsed_time = generate_response(
        prompt,
        model_param,
        func_clean=response_clean,
        func_valid=response_validate,
        get_fail_safe=get_fail_safe(),
    )
    print_prompt_output(persona.name, prompt, output, elapsed_time)
    return output


def run_prompt_action_area(
    action_desc,
    persona,
    maze,
    act_world,
    act_sector,
):
    def create_prompt_input(action_desc, persona, maze, act_world, act_sector):
        prompt_input = []
        prompt_input = [persona.direct_mem.get_str_mds()]
        prompt_input += [persona.direct_mem.get_name()]
        x = f"{act_world}:{act_sector}"
        prompt_input += [act_sector]

        accessible_area_str = persona.spatial_mem.get_str_accessible_sector_areas(x)
        prompt_input += [accessible_area_str]

        action_desc_1 = action_desc
        action_desc_2 = action_desc
        if "（" in action_desc:
            action_desc_1 = action_desc.split("（")[0].strip()
            action_desc_2 = action_desc.split("（")[-1][:-1]
        prompt_input += [persona.direct_mem.get_name()]
        prompt_input += [action_desc_1]

        prompt_input += [action_desc_2]
        prompt_input += [persona.direct_mem.get_name()]

        prompt_input += [act_sector]
        prompt_input += [accessible_area_str]
        return prompt_input

    def response_clean(response, prompt=""):
        return response

    def response_validate(response, prompt=""):
        try:
            cleaned_up = response_clean(response, prompt=prompt)
            if cleaned_up not in persona.spatial_mem.get_str_accessible_sector_areas(
                f"{act_world}:{act_sector}"
            ):
                return False
        except:
            return False
        return True

    def get_fail_safe():
        fs = "厨房"
        return fs

    model_param = {
        "model": specify_model,
        "max_tokens": 20,
        "temperature": 0,
        "top_p": 1,
        "stream": False,
        "stop": None,
    }
    prompt_template = f"{prompt_path}/plan/action_location_area_v1.txt"
    prompt_input = create_prompt_input(
        action_desc, persona, maze, act_world, act_sector
    )
    prompt = generate_prompt(prompt_input, prompt_template)
    output, elapsed_time = generate_response(
        prompt,
        model_param,
        func_clean=response_clean,
        func_valid=response_validate,
        get_fail_safe=get_fail_safe(),
    )
    print_prompt_output(persona.name, prompt, output, elapsed_time)
    return output


def run_prompt_action_object(action_desc, persona, maze, temp_address):
    def create_prompt_input(action_desc, persona, temp_address):
        prompt_input = []
        if "（" in action_desc:
            action_desc = action_desc.split("（")[-1][:-1]

        prompt_input += [action_desc]
        prompt_input += [
            persona.spatial_mem.get_str_accessible_area_objects(temp_address)
        ]
        return prompt_input

    def response_clean(response, prompt=""):
        return response

    def response_validate(response, prompt=""):
        try:
            cleaned_up = response_clean(response, prompt=prompt)
            if cleaned_up not in persona.spatial_mem.get_str_accessible_area_objects(
                temp_address
            ):
                return False
        except:
            return False
        return True

    def get_fail_safe():
        return None

    model_param = {
        "model": specify_model,
        "max_tokens": 20,
        "temperature": 0.3,
        "top_p": 1,
        "stream": False,
        "stop": None,
    }
    prompt_template = f"{prompt_path}/plan/action_object_v1.txt"
    prompt_input = create_prompt_input(action_desc, persona, temp_address)
    prompt = generate_prompt(prompt_input, prompt_template)
    output, elapsed_time = generate_response(
        prompt,
        model_param,
        func_clean=response_clean,
        func_valid=response_validate,
        get_fail_safe=get_fail_safe(),
    )
    x = [
        i.strip()
        for i in persona.spatial_mem.get_str_accessible_area_objects(
            temp_address
        ).split(",")
    ]
    if output not in x:
        output = random.choice(x)
    print_prompt_output(persona.name, prompt, output, elapsed_time)
    return output


def run_prompt_event_triple(action_desc, persona):
    def create_prompt_input(action_desc, persona):
        if "（" in action_desc:
            action_desc = action_desc.split("（")[-1].split("）")[0]
        prompt_input = [persona.direct_mem.name, action_desc]
        return prompt_input

    def response_clean(response, prompt=""):
        cr = response.strip()
        cr = tuple([i.strip() for i in cr[1:].split(")")[0].split(",")])
        return cr

    def response_validate(response, prompt=""):
        try:
            response = response_clean(response, prompt=prompt)
            if len(response) != 3:
                return False
        except:
            return False
        return True

    def get_fail_safe():
        fs = (persona.direct_mem.name, "正在", "空闲")
        return fs

    model_param = {
        "model": specify_model,
        "max_tokens": 20,
        "temperature": 0.3,
        "top_p": 1,
        "stream": False,
        "stop": None,
    }
    prompt_template = f"{prompt_path}/plan/generate_event_triple_v1.txt"
    prompt_input = create_prompt_input(action_desc, persona)
    prompt = generate_prompt(prompt_input, prompt_template)
    output, elapsed_time = generate_response(
        prompt,
        model_param,
        func_clean=response_clean,
        func_valid=response_validate,
        get_fail_safe=get_fail_safe(),
    )
    print_prompt_output(persona.name, prompt, output, elapsed_time, True)
    return output


def run_prompt_act_obj_desc(
    act_object,
    act_desp,
    persona,
):
    def create_prompt_input(
        act_object,
        act_desp,
        persona,
    ):
        prompt_input = [
            act_object,
            persona.direct_mem.name,
            act_desp,
        ]
        return prompt_input

    def response_clean(response, prompt=""):
        cr = response.split("正在")[-1].strip()
        if cr[-1] == "。":
            cr = cr[:-1]
        return cr

    def response_validate(response, prompt=""):
        try:
            response_clean(response, prompt=prompt)
        except:
            return False
        return True

    def get_fail_safe():
        fs = f"空闲"
        return fs

    model_param = {
        "model": specify_model,
        "max_tokens": 20,
        "temperature": 0.3,
        "top_p": 1,
        "stream": False,
        "stop": None,
    }
    prompt_template = f"{prompt_path}/plan/generate_obj_event_v1.txt"
    prompt_input = create_prompt_input(
        act_object,
        act_desp,
        persona,
    )
    prompt = generate_prompt(prompt_input, prompt_template)
    output, elapsed_time = generate_response(
        prompt,
        model_param,
        func_clean=response_clean,
        func_valid=response_validate,
        get_fail_safe=get_fail_safe(),
    )
    print_prompt_output(persona.name, prompt, output, elapsed_time, True)
    return output


def run_prompt_act_obj_event_triple(
    act_object,
    act_obj_desc,
    persona,
):
    def create_prompt_input(
        act_object,
        act_obj_desc,
        persona,
    ):
        prompt_input = [act_object, act_obj_desc, act_object]
        return prompt_input

    def response_clean(response, prompt=""):
        cr = response.strip()
        cr = [i.strip() for i in cr[1:].split(")")[0].split(",")]
        return cr

    def response_validate(response, prompt=""):
        try:
            response = response_clean(response, prompt=prompt)
        except:
            return False
        return True

    def get_fail_safe():
        fs = (act_object, "正在", "空闲")
        return fs

    model_param = {
        "model": specify_model,
        "max_tokens": 20,
        "temperature": 0.3,
        "top_p": 1,
        "stream": False,
        "stop": None,
    }
    prompt_template = f"{prompt_path}/plan/generate_event_triple_v1.txt"
    prompt_input = create_prompt_input(
        act_object,
        act_obj_desc,
        persona,
    )
    prompt = generate_prompt(prompt_input, prompt_template)
    output, elapsed_time = generate_response(
        prompt,
        model_param,
        func_clean=response_clean,
        func_valid=response_validate,
        get_fail_safe=get_fail_safe(),
    )
    print_prompt_output(persona.name, prompt, output, elapsed_time)
    return output


def run_prompt_decide_to_talk(init_persona, target_persona, retrieved):
    def create_prompt_input(init_persona, target_persona, retrieved):
        prompt_input = []

        last_chat = init_persona.associate_mem.get_last_chat(target_persona.name)
        about_last_chat = ""
        if last_chat:
            last_chatted_time = last_chat.created.strftime("%B %d, %Y, %H:%M:%S")
            last_chat_about = last_chat.description
            about_last_chat = f"{init_persona.name} 和 {target_persona.name} 最后一次在 {last_chatted_time} 讨论了 {last_chat_about}"

        context = ""
        for c_node in retrieved["events"]:
            curr_desc = c_node.description.split(" ")
            curr_desc[1:2] = ["此前正在"]
            curr_desc = " ".join(curr_desc)
            context += f"{curr_desc}. "
            context += "\n"
        for c_node in retrieved["thoughts"]:
            context += f"{c_node.description}。"

        # 相关events和thoughts的context上下文
        curr_time = init_persona.direct_mem.curr_time.strftime("%B %d, %Y, %H:%M:%S %p")
        init_act_desc = init_persona.direct_mem.act_description
        if "（" in init_act_desc:
            init_act_desc = init_act_desc.split("（")[-1][:-1]

        if (
            len(init_persona.direct_mem.planned_path) == 0
            and "等待" not in init_act_desc
        ):
            init_p_desc = f"{init_persona.name} 正在 {init_act_desc}"  # is already
        elif "等待" in init_act_desc:
            init_p_desc = f"{init_persona.name} 正在 {init_act_desc}"  # is
        else:
            init_p_desc = f"{init_persona.name} 正在去 {init_act_desc} 的路上"

        target_act_desc = target_persona.direct_mem.act_description
        if "（" in target_act_desc:
            target_act_desc = target_act_desc.split("（")[-1][:-1]
        if (
            len(target_persona.direct_mem.planned_path) == 0
            and "等待" not in init_act_desc
        ):
            target_p_desc = f"{target_persona.name} 正在 {target_act_desc}"
        elif "等待" in init_act_desc:
            target_p_desc = f"{init_persona.name} 正在 {init_act_desc}"
        else:
            target_p_desc = f"{target_persona.name} 正在去 {target_act_desc} 的路上"

        prompt_input = []
        prompt_input += [context]
        prompt_input += [curr_time]

        prompt_input += [about_last_chat]

        prompt_input += [init_p_desc]
        prompt_input += [target_p_desc]
        prompt_input += [init_persona.name]
        prompt_input += [target_persona.name]
        return prompt_input

    def response_clean(response, prompt=""):
        response = extract_first_json_dict(response)
        cleaned_dict = dict()
        cleaned = []
        for key, val in response.items():
            cleaned += [val]
        cleaned_dict["inference"] = cleaned[0]
        cleaned_dict["answer"] = True
        if "f" in str(cleaned[1]) or "F" in str(cleaned[1]):
            cleaned_dict["answer"] = False

        return cleaned_dict
        # print("<run_prompt_decide_to_talk> response:", response)
        # return response[-1]

    def response_validate(response, prompt=""):
        try:
            extract_first_json_dict(response)
            return True
        except:
            return False

    def get_fail_safe():
        fs = {"inference": "get_fail_safe", "answer": True}
        return fs

    model_param = {
        "model": specify_model,
        "max_tokens": 4096,
        "temperature": 0,
        "top_p": 1,
        "stream": False,
        "stop": None,
    }
    prompt_template = f"{prompt_path}/plan/decide_to_talk_inner_thought_v1.txt"
    prompt_input = create_prompt_input(init_persona, target_persona, retrieved)
    prompt = generate_prompt(prompt_input, prompt_template)
    output, elapsed_time = generate_response(
        prompt,
        model_param,
        func_clean=response_clean,
        func_valid=response_validate,
        get_fail_safe=get_fail_safe(),
    )
    print_prompt_output(init_persona.name, prompt, output, elapsed_time)
    return output["answer"]


def run_prompt_decide_to_react(init_persona, target_persona, retrieved):
    def create_prompt_input(init_persona, target_persona, retrieved):
        context = ""
        for c_node in retrieved["events"][:20]:
            curr_desc = c_node.description.split(" ")
            curr_desc[1:2] = ["此前"]
            curr_desc = " ".join(curr_desc)
            context += f"{curr_desc}。"
        context += "\n"
        for c_node in retrieved["thoughts"][:20]:
            context += f"{c_node.description}。"

        curr_time = init_persona.direct_mem.curr_time.strftime("%B %d, %Y, %H:%M:%S %p")
        init_act_desc = init_persona.direct_mem.act_description
        if "（" in init_act_desc:
            init_act_desc = init_act_desc.split("（")[-1][:-1]
        if len(init_persona.direct_mem.planned_path) == 0:
            loc = ""
            if ":" in init_persona.direct_mem.act_address:
                loc = (
                    init_persona.direct_mem.act_address.split(":")[-2]
                    + " 的 "
                    + init_persona.direct_mem.act_address.split(":")[-1]
                )
            init_p_desc = f"{init_persona.name} 正在 {loc} {init_act_desc}"
        else:
            loc = ""
            if ":" in init_persona.direct_mem.act_address:
                loc = (
                    init_persona.direct_mem.act_address.split(":")[-2]
                    + " 的 "
                    + init_persona.direct_mem.act_address.split(":")[-1]
                )
            init_p_desc = f"{init_persona.name} 正在去 {loc} {init_act_desc} 的路上"

        target_act_desc = target_persona.direct_mem.act_description
        if "（" in target_act_desc:
            target_act_desc = target_act_desc.split("（")[-1][:-1]
        if len(target_persona.direct_mem.planned_path) == 0:
            loc = ""
            if ":" in target_persona.direct_mem.act_address:
                loc = (
                    target_persona.direct_mem.act_address.split(":")[-2]
                    + " 的 "
                    + target_persona.direct_mem.act_address.split(":")[-1]
                )
            target_p_desc = f"{target_persona.name} 正在 {loc} {target_act_desc}"
        else:
            loc = ""
            if ":" in target_persona.direct_mem.act_address:
                loc = (
                    target_persona.direct_mem.act_address.split(":")[-2]
                    + " 的 "
                    + target_persona.direct_mem.act_address.split(":")[-1]
                )
            target_p_desc = (
                f"{target_persona.name} 正在去 {loc} {target_act_desc} 的路上"
            )

        prompt_input = []
        prompt_input += [context]
        prompt_input += [curr_time]
        prompt_input += [init_p_desc]
        prompt_input += [target_p_desc]

        prompt_input += [init_persona.name]
        prompt_input += [init_act_desc]
        prompt_input += [target_persona.name]
        prompt_input += [target_act_desc]

        prompt_input += [init_act_desc]
        return prompt_input

    def response_clean(response, prompt=""):
        return response.split("答案：选项")[-1].strip()

    def response_validate(response, prompt=""):
        try:
            if response_clean(response, prompt=prompt) in ["1", "2"]:
                return True
            return False
        except:
            return False

    def get_fail_safe():
        fs = "2"
        return fs

    model_param = {
        "model": specify_model,
        "max_tokens": 4096,
        "temperature": 0.3,
        "top_p": 1,
        "stream": False,
        "stop": None,
    }
    prompt_template = f"{prompt_path}/plan/decide_to_react_v1.txt"
    prompt_input = create_prompt_input(init_persona, target_persona, retrieved)
    prompt = generate_prompt(prompt_input, prompt_template)
    output, elapsed_time = generate_response(
        prompt,
        model_param,
        func_clean=response_clean,
        func_valid=response_validate,
        get_fail_safe=get_fail_safe(),
    )
    print_prompt_output(init_persona.name, prompt, output, elapsed_time)
    return output


def run_prompt_event_poignancy(
    persona,
    event_description,
):
    def create_prompt_input(
        persona,
        event_description,
    ):
        prompt_input = [
            persona.direct_mem.get_str_mds(),
            persona.direct_mem.name,
            event_description,
        ]
        return prompt_input

    def response_clean(response, prompt=""):
        response = int(response.strip())
        return response

    def response_validate(response, prompt=""):
        try:
            response_clean(response, prompt=prompt)
        except:
            return False
        return True

    def get_fail_safe():
        fs = 4
        return fs

    model_param = {
        "model": specify_model,
        "max_tokens": 10,
        "temperature": 0.3,
        "top_p": 1,
        "stream": False,
        "stop": None,
    }
    prompt_template = f"{prompt_path}/retrieve/poignancy_event_v1.txt"
    prompt_input = create_prompt_input(
        persona,
        event_description,
    )
    prompt = generate_prompt(prompt_input, prompt_template)
    output, elapsed_time = generate_response(
        prompt,
        model_param,
        func_clean=response_clean,
        func_valid=response_validate,
        get_fail_safe=get_fail_safe(),
    )
    print_prompt_output(persona.name, prompt, output, elapsed_time, True)
    return output


def run_prompt_chat_poignancy(
    persona,
    event_description,
):
    def create_prompt_input(
        persona,
        event_description,
    ):
        prompt_input = [
            persona.direct_mem.get_str_mds(),
            persona.direct_mem.name,
            event_description,
        ]
        return prompt_input

    def response_clean(response, prompt=""):
        response = int(response.strip())
        return response

    def response_validate(response, prompt=""):
        try:
            response_clean(response, prompt=prompt)
        except:
            return False
        return True

    def get_fail_safe():
        fs = 4
        return fs

    model_param = {
        "model": specify_model,
        "max_tokens": 10,
        "temperature": 0.3,
        "top_p": 1,
        "stream": False,
        "stop": None,
    }
    prompt_template = f"{prompt_path}/retrieve/poignacy_chat_v1.txt"
    prompt_input = create_prompt_input(
        persona,
        event_description,
    )
    prompt = generate_prompt(prompt_input, prompt_template)
    output, elapsed_time = generate_response(
        prompt,
        model_param,
        func_clean=response_clean,
        func_valid=response_validate,
        get_fail_safe=get_fail_safe(),
    )
    print_prompt_output(persona.name, prompt, output, elapsed_time, True)
    return output


def run_prompt_focal_point(persona, statements, n):
    def create_prompt_input(persona, statements, n):
        return [statements, str(n)]

    def response_clean(response, prompt=""):
        cleaned = []
        for line in response.split("\n"):
            cleaned.append(line.split(")")[-1])
        return cleaned

    def response_validate(response, prompt=""):
        try:
            response_clean(response, prompt=prompt)
            return True
        except:
            return False

    def get_fail_safe(n):
        return [f"Untitled Topic {i+1}" for i in range(n)]

    model_param = {
        "model": specify_model,
        "max_tokens": 150,
        "temperature": 0,
        "top_p": 1,
        "stream": False,
        "stop": None,
    }

    prompt_template = f"{prompt_path}/reflect/generate_focal_point_v1.txt"
    prompt_input = create_prompt_input(persona, statements, n)
    prompt = generate_prompt(prompt_input, prompt_template)

    output, elapsed_time = generate_response(
        prompt,
        model_param,
        func_clean=response_clean,
        func_valid=response_validate,
        get_fail_safe=lambda: get_fail_safe(n),
    )

    print_prompt_output(persona.name, prompt, output, elapsed_time)
    return output


def run_prompt_insight_guidance(persona, statements, n):
    def create_prompt_input(persona, statements, n):
        prompt_input = []
        prompt_input += [f"姓名:{persona.direct_mem.name}"]
        prompt_input += [f"年龄:{persona.direct_mem.age}"]
        prompt_input += [f"性别:{persona.direct_mem.gender}"]
        prompt_input += [f"性格:{persona.direct_mem.personality}"]
        prompt_input += [f"背景:{persona.direct_mem.background}"]
        prompt_input += [statements]
        prompt_input += [persona.name]
        prompt_input += [str(n)]

        return prompt_input

    def response_clean(response, prompt=""):
        # response = "1. " + response.strip()
        result = dict()
        for line in response.split("\n"):
            content = line.split(". ")[-1]
            insight_part = content.split("(依据：")[0].strip()
            evidence_part = content.split("(依据：")[1].split(")")[0].strip()
            evidence_ids = [
                int(num.strip()) for num in re.findall(r"\d+", evidence_part)
            ]
            result[insight_part] = evidence_ids
        return result

    def response_validate(response, prompt=""):
        try:
            response_clean(response, prompt=prompt)
            return True
        except:
            return False

    def get_fail_safe():
        return ["未获取到洞察"] * n

    model_param = {
        "model": specify_model,
        "max_tokens": 200,
        "temperature": 0.3,
        "top_p": 1,
        "stream": False,
        "stop": None,
    }

    prompt_template = f"{prompt_path}/reflect/insight_guidance_v1.txt"
    prompt_input = create_prompt_input(persona, statements, n)
    prompt = generate_prompt(prompt_input, prompt_template)

    output, elapsed_time = generate_response(
        prompt,
        model_param,
        func_clean=response_clean,
        func_valid=response_validate,
        get_fail_safe=get_fail_safe(),
    )

    print_prompt_output(persona.name, prompt, output, elapsed_time)
    return output


def run_prompt_planning_thought_on_convo(persona, all_utt):
    def create_prompt_input(persona, all_utt):
        prompt_input = []
        prompt_input += [f"姓名:{persona.direct_mem.name}"]
        prompt_input += [f"年龄:{persona.direct_mem.age}"]
        prompt_input += [f"性别:{persona.direct_mem.gender}"]
        prompt_input += [f"性格:{persona.direct_mem.personality}"]
        prompt_input += [f"背景:{persona.direct_mem.background}"]
        prompt_input += [all_utt]
        prompt_input += [persona.name]
        prompt_input += [persona.name]
        prompt_input += [persona.name]
        return prompt_input

    def response_clean(response, prompt=""):
        return response.split('"')[0].strip()

    def response_validate(response, prompt=""):
        try:
            response_clean(response, prompt=prompt)
            return True
        except:
            return False

    def get_fail_safe():
        return "..."

    model_param = {
        "model": specify_model,
        "max_tokens": 100,
        "temperature": 0,
        "top_p": 1,
        "stream": False,
        "stop": None,
    }

    prompt_template = f"{prompt_path}/reflect/planning_thought_v1.txt"
    prompt_input = create_prompt_input(persona, all_utt)
    prompt = generate_prompt(prompt_input, prompt_template)

    output, elapsed_time = generate_response(
        prompt,
        model_param,
        func_clean=response_clean,
        func_valid=response_validate,
        get_fail_safe=get_fail_safe,
    )

    print_prompt_output(persona.name, prompt, output, elapsed_time)
    return output


def run_prompt_memo_on_convo(persona, all_utt):
    def create_prompt_input(persona, all_utt):
        return [
            all_utt,
            persona.direct_mem.name,
            persona.direct_mem.name,
            persona.direct_mem.name,
        ]

    def response_clean(response, prompt=""):
        return response.strip()

    def response_validate(response, prompt=""):
        try:
            response_clean(response, prompt=prompt)
            return True
        except:
            return False

    def get_fail_safe():
        return "..."

    model_param = {
        "model": specify_model,
        "max_tokens": 300,
        "temperature": 0,
        "top_p": 1,
        "stream": False,
        "stop": None,
    }

    prompt_template = f"{prompt_path}/reflect/memo_on_convo_v1.txt"
    prompt_input = create_prompt_input(persona, all_utt)
    prompt = generate_prompt(prompt_input, prompt_template)

    output, elapsed_time = generate_response(
        prompt,
        model_param,
        func_clean=response_clean,
        func_valid=response_validate,
        get_fail_safe=get_fail_safe,
    )

    print_prompt_output(persona.name, prompt, output, elapsed_time)
    return output


def run_prompt_new_decomp_schedule(
    persona,
    main_act_dur,
    truncated_act_dur,
    start_time_hour,
    end_time_hour,
    inserted_act,
    inserted_act_dur,
):
    def create_prompt_input(
        persona,
        main_act_dur,
        truncated_act_dur,
        start_time_hour,
        end_time_hour,
        inserted_act,
        inserted_act_dur,
    ):
        persona_name = persona.direct_mem.name
        start_hour_str = start_time_hour.strftime("%H:%M %p")
        end_hour_str = end_time_hour.strftime("%H:%M %p")

        original_plan = ""
        for_time = start_time_hour
        for i in main_act_dur:
            original_plan += (
                f'{for_time.strftime("%H:%M")} ~ {(for_time + datetime.timedelta(minutes=int(i[1]))).strftime("%H:%M")} -- '
                + i[0]
            )
            original_plan += "\n"
            for_time += datetime.timedelta(minutes=int(i[1]))

        new_plan_init = ""
        for_time = start_time_hour
        for count, i in enumerate(truncated_act_dur):
            new_plan_init += (
                f'{for_time.strftime("%H:%M")} ~ {(for_time + datetime.timedelta(minutes=int(i[1]))).strftime("%H:%M")} -- '
                + i[0]
            )
            new_plan_init += "\n"
            if count < len(truncated_act_dur) - 1:
                for_time += datetime.timedelta(minutes=int(i[1]))

        # new_plan_init += (for_time + datetime.timedelta(minutes=int(i[1]))).strftime(
        #     "%H:%M"
        # ) + " ~"
        # new_plan_init += "(从此处开始，生成后续日程)"

        prompt_input = [
            persona_name,
            start_hour_str,
            end_hour_str,
            original_plan,
            persona_name,
            inserted_act,
            inserted_act_dur,
            persona_name,
            start_hour_str,
            end_hour_str,
            end_hour_str,
            new_plan_init,
        ]
        return prompt_input

    def response_clean(response, prompt):
        new_schedule = (
            prompt.split("(从此处开始，仅生成后续日程)")[0] + response.strip()
        )
        new_schedule = new_schedule.split(
            "调整后的日程安排（仅输出变更时段之后的调整部分，即从以下日程结尾的下一项开始）："
        )[-1].strip()
        new_schedule = new_schedule.strip().split("\n")

        ret_temp = []
        for i in new_schedule:
            ret_temp += [i.split(" -- ")]

        ret = []
        for time_str, action in ret_temp:
            start_time = time_str.split(" ~ ")[0].strip()
            end_time = time_str.split(" ~ ")[1].strip()
            delta = datetime.datetime.strptime(
                end_time, "%H:%M"
            ) - datetime.datetime.strptime(start_time, "%H:%M")
            delta_min = int(delta.total_seconds() / 60)
            if delta_min < 0:
                delta_min = 0
            ret += [[action, delta_min]]

        return ret

    def response_validate(response, prompt=""):
        try:
            response = response_clean(response, prompt)
            dur_sum = 0
            for act, dur in response:
                dur_sum += dur
                if str(type(act)) != "<class 'str'>":
                    print_c(f"<run_prompt_new_decomp_schedule> act error: {act}")
                    return False
                if str(type(dur)) != "<class 'int'>":
                    print_c(f"<run_prompt_new_decomp_schedule> dur error: {dur}")
                    return False
            x = prompt.split("\n")[0].split("原本计划在")[-1].strip()[:-1]
            x_start = datetime.datetime.strptime(x.split("到")[0].strip(), "%H:%M %p")
            x_end = datetime.datetime.strptime(
                x.split("到")[-1].rsplit(" ", 1)[0].strip(), "%H:%M %p"
            )
            delta_min = int((x_end - x_start).total_seconds() / 60)

            if int(dur_sum) != int(delta_min):
                print_c(
                    f"<run_prompt_new_decomp_schedule> error dur_sum != delta_min: {dur_sum} != {delta_min}"
                )
                return False

        except:
            return False
        return True

    def get_fail_safe(main_act_dur, truncated_act_dur):
        dur_sum = 0
        for act, dur in main_act_dur:
            dur_sum += dur
        ret = truncated_act_dur[:]
        ret += main_act_dur[len(ret) - 1 :]
        # If there are access, we need to trim...
        ret_dur_sum = 0
        count = 0
        over = None
        for act, dur in ret:
            ret_dur_sum += dur
            if ret_dur_sum == dur_sum:
                break
            if ret_dur_sum > dur_sum:
                over = ret_dur_sum - dur_sum
                break
            count += 1
        if over:
            ret = ret[: count + 1]
            ret[-1][1] -= over
        return ret

    model_param = {
        "model": specify_CoT_model,
        "max_tokens": 4096,
        "temperature": 0.4,
        "top_p": 1,
        "stream": False,
        "stop": None,
    }
    prompt_template = f"{prompt_path}/plan/new_decomp_schedule_v1.txt"
    prompt_input = create_prompt_input(
        persona,
        main_act_dur,
        truncated_act_dur,
        start_time_hour,
        end_time_hour,
        inserted_act,
        inserted_act_dur,
    )
    prompt = generate_prompt(prompt_input, prompt_template)
    output, elapsed_time = generate_response(
        prompt,
        model_param,
        func_clean=response_clean,
        func_valid=response_validate,
        get_fail_safe=get_fail_safe(main_act_dur, truncated_act_dur),
    )
    print_prompt_output(persona.name, prompt, output, elapsed_time)
    return output


def run_prompt_agent_chat_summarize_relationship(
    persona,
    target_persona,
    statements,
):
    def create_prompt_input(persona, target_persona, statements):
        prompt_input = [
            statements,
            persona.direct_mem.name,
            target_persona.direct_mem.name,
        ]
        return prompt_input

    def response_clean(response, prompt=""):
        return response

    def response_validate(response, prompt=""):
        return True

    def get_fail_safe():
        fs = "..."
        return fs

    model_param = {
        "model": specify_model,
        "max_tokens": 50,
        "temperature": 0.5,
        "top_p": 1,
        "stream": False,
        "stop": None,
    }
    prompt_template = f"{prompt_path}/convo/summarize_chat_relationship_v1.txt"
    prompt_input = create_prompt_input(persona, target_persona, statements)
    prompt = generate_prompt(prompt_input, prompt_template)
    output, elapsed_time = generate_response(
        prompt,
        model_param,
        func_clean=response_clean,
        func_valid=response_validate,
        get_fail_safe=get_fail_safe(),
    )
    print_prompt_output(persona.name, prompt, output, elapsed_time)
    return output


def run_generate_iterative_chat_utt(
    maze,
    init_persona,
    target_persona,
    retrieved,
    curr_context,
    curr_chat,
):
    def create_prompt_input(
        maze,
        init_persona,
        target_persona,
        retrieved,
        curr_context,
        curr_chat,
    ):
        persona = init_persona
        prev_convo_insert = "\n"
        if persona.associate_mem.seq_chat:
            for i in persona.associate_mem.seq_chat:
                if i.object == target_persona.direct_mem.name:
                    v1 = int(
                        (persona.direct_mem.curr_time - i.created).total_seconds() / 60
                    )
                    prev_convo_insert += f"{str(v1)} 分钟之前，{persona.direct_mem.name} 和 {target_persona.direct_mem.name} 已经 {i.description} This context takes place after that conversation."  # 这句话怎么翻译？？？
                    break
        if prev_convo_insert == "\n":
            prev_convo_insert = "（暂无）"
        if persona.associate_mem.seq_chat:
            if (
                int(
                    (
                        persona.direct_mem.curr_time
                        - persona.associate_mem.seq_chat[-1].created
                    ).total_seconds()
                    / 60
                )
                > 480
            ):
                prev_convo_insert = "（暂无）"

        curr_sector = f"{maze.access_cell(persona.direct_mem.curr_cell)['sector']}"
        curr_area = f"{maze.access_cell(persona.direct_mem.curr_cell)['area']}"
        curr_location = f"{curr_sector}"
        if curr_area:
            curr_location += f" 中的 {curr_area}"

        retrieved_str = ""
        for key, vals in retrieved.items():
            for v in vals:
                retrieved_str += f"- {v.description}\n"

        convo_str = ""
        for i in curr_chat:
            convo_str += "： ".join(i) + "\n"
        if convo_str == "":
            convo_str = "[对话尚未开始 -- 请你开始他吧！]"

        init_iss = f"以下是对 {init_persona.direct_mem.name} 的简要描述\n{init_persona.direct_mem.get_str_mds()}"
        prompt_input = [
            init_iss,
            init_persona.direct_mem.name,
            retrieved_str,
            prev_convo_insert,
            curr_location,
            curr_context,
            init_persona.direct_mem.name,
            target_persona.direct_mem.name,
            convo_str,
            init_persona.direct_mem.name,
            target_persona.direct_mem.name,
            init_persona.direct_mem.name,
            init_persona.direct_mem.name,
        ]
        return prompt_input

    def response_clean(response, prompt=""):
        response = extract_first_json_dict(response)

        cleaned_dict = dict()
        cleaned = []
        for key, val in response.items():
            cleaned += [val]
        cleaned_dict["utterance"] = cleaned[0]
        cleaned_dict["end"] = True
        if "f" in str(cleaned[1]) or "F" in str(cleaned[1]):
            cleaned_dict["end"] = False

        return cleaned_dict

    def response_validate(response, prompt=""):
        try:
            extract_first_json_dict(response)
            return True
        except:
            return False

    def get_fail_safe():
        cleaned_dict = dict()
        cleaned_dict["utterance"] = "..."
        cleaned_dict["end"] = False
        return cleaned_dict

    model_param = {
        "model": specify_model,
        "max_tokens": 100,
        "temperature": 0.5,
        "top_p": 1,
        "stream": False,
        "stop": None,
    }
    prompt_template = f"{prompt_path}/convo/iterative_convo_v1.txt"
    prompt_input = create_prompt_input(
        maze, init_persona, target_persona, retrieved, curr_context, curr_chat
    )
    prompt = generate_prompt(prompt_input, prompt_template)
    output, elapsed_time = generate_response(
        prompt,
        model_param,
        func_clean=response_clean,
        func_valid=response_validate,
        get_fail_safe=get_fail_safe(),
    )
    print_prompt_output(init_persona.name, prompt, output, elapsed_time)
    return output


def run_prompt_summarize_conversation(
    persona,
    conversation,
):
    def create_prompt_input(
        persona,
        conversation,
    ):
        convo_str = ""
        for row in conversation:
            convo_str += f"{row[0]}： “{row[1]}”\n"

        prompt_input = [convo_str]
        return prompt_input

    def response_clean(response, prompt=""):
        ret = "谈论有关 " + response.split("这是一个关于")[-1]
        return ret

    def response_validate(response, prompt=""):
        try:
            response_clean(response, prompt=prompt)
            return True
        except:
            return False

    def get_fail_safe():
        return "谈论有关 生活方面的小事"

    model_param = {
        "model": specify_model,
        "max_tokens": 50,
        "temperature": 0.8,
        "top_p": 1,
        "stream": False,
        "stop": None,
    }
    prompt_template = f"{prompt_path}/convo/summarize_conversation_v1.txt"
    prompt_input = create_prompt_input(
        persona,
        conversation,
    )
    prompt = generate_prompt(prompt_input, prompt_template)

    output, elapsed_time = generate_response(
        prompt,
        model_param,
        func_clean=response_clean,
        func_valid=response_validate,
        get_fail_safe=get_fail_safe(),
    )
    print_prompt_output(persona.name, prompt, output, elapsed_time)
    return output


def run_prompt_summarize_ideas(persona, statements, question):
    def create_prompt_input(persona, statements, question):
        return [statements, persona.direct_mem.name, question]

    def response_clean(response, prompt=""):
        print_c(f"<run_prompt_summarize_ideas> response: {response}")
        return response.split('"')[0].strip()

    def response_validate(response, prompt=""):
        try:
            response_clean(response, prompt)
            return True
        except:
            return False

    def get_fail_safe():
        return "..."

    model_param = {
        "model": specify_model,  # TODO: specify_model更换为推理模型
        "max_tokens": 4096,
        "temperature": 0.4,
        "top_p": 1,
        "stream": False,
        "stop": None,
    }

    prompt_template = f"{prompt_path}/convo/summarize_ideas_v1.txt"
    prompt_input = create_prompt_input(persona, statements, question)
    prompt = generate_prompt(prompt_input, prompt_template)

    output, elapsed_time = generate_response(
        prompt,
        model_param,
        func_clean=response_clean,
        func_valid=response_validate,
        get_fail_safe=get_fail_safe(),
    )

    print_prompt_output(persona.direct_mem.name, prompt, output, elapsed_time)
    return output


def run_prompt_generate_next_convo_line(
    persona, interlocutor_desc, prev_convo, retrieved_summary
):
    def create_prompt_input(persona, interlocutor_desc, prev_convo, retrieved_summary):
        return [
            persona.direct_mem.name,
            persona.direct_mem.get_str_mds(),
            persona.direct_mem.name,
            interlocutor_desc,
            prev_convo,
            persona.direct_mem.name,
            retrieved_summary,
            persona.direct_mem.name,
        ]

    def response_clean(response, prompt=""):
        print_c(f"<run_prompt_generate_next_convo_line> response: {response}")
        return response.split('"')[-2]

    def response_validate(response, prompt=""):
        try:
            response_clean(response, prompt)
            return True
        except:
            return False

    def get_fail_safe():
        return "..."

    model_param = {
        "model": specify_model,
        "max_tokens": 4096,
        "temperature": 0.4,
        "top_p": 1,
        "stream": False,
        "stop": None,
    }

    prompt_template = f"{prompt_path}/convo/generate_next_convo_line_v1.txt"
    prompt_input = create_prompt_input(
        persona, interlocutor_desc, prev_convo, retrieved_summary
    )
    prompt = generate_prompt(prompt_input, prompt_template)

    output, elapsed_time = generate_response(
        prompt,
        model_param,
        func_clean=response_clean,
        func_valid=response_validate,
        get_fail_safe=get_fail_safe(),
    )

    print_prompt_output(persona.direct_mem.name, prompt, output, elapsed_time)
    return output


def run_prompt_generate_next_minds_line(
    persona, interlocutor_desc, prev_convo_minds, retrieved_summary
):
    def create_prompt_input(
        persona, interlocutor_desc, prev_convo_minds, retrieved_summary
    ):
        return [
            persona.direct_mem.name,
            persona.direct_mem.get_str_mds(),
            persona.direct_mem.name,
            interlocutor_desc,
            prev_convo_minds,
            persona.direct_mem.name,
            retrieved_summary,
        ]

    def response_clean(response, prompt=""):
        print_c(f"<run_prompt_generate_next_minds_line> response: {response}")
        return response.replace('"', "").replace("'", "")

    def response_validate(response, prompt=""):
        try:
            response_clean(response, prompt)
            return True
        except:
            return False

    def get_fail_safe():
        return "..."

    model_param = {
        "model": specify_model,
        "max_tokens": 4096,
        "temperature": 0.4,
        "top_p": 1,
        "stream": False,
        "stop": None,
    }

    prompt_template = f"{prompt_path}/convo/generate_next_convo_minds_v1.txt"
    prompt_input = create_prompt_input(
        persona, interlocutor_desc, prev_convo_minds, retrieved_summary
    )
    prompt = generate_prompt(prompt_input, prompt_template)

    output, elapsed_time = generate_response(
        prompt,
        model_param,
        func_clean=response_clean,
        func_valid=response_validate,
        get_fail_safe=get_fail_safe(),
    )

    print_prompt_output(persona.direct_mem.name, prompt, output, elapsed_time)
    return output


def run_prompt_generate_whisper_inner_thought(persona, whisper):
    def create_prompt_input(persona, whisper):
        return [persona.direct_mem.name, whisper]

    def response_clean(response, prompt=""):
        return response.split('"')[0].strip()

    def response_validate(response, prompt=""):
        try:
            response_clean(response, prompt)
            return True
        except:
            return False

    def get_fail_safe():
        return "..."

    model_param = {
        "model": specify_model,
        "max_tokens": 4096,
        "temperature": 0.4,
        "top_p": 1,
        "stream": False,
        "stop": None,
    }

    prompt_template = f"{prompt_path}/convo/whisper_inner_thought_v1.txt"
    prompt_input = create_prompt_input(persona, whisper)
    prompt = generate_prompt(prompt_input, prompt_template)

    output, elapsed_time = generate_response(
        prompt,
        model_param,
        func_clean=response_clean,
        func_valid=response_validate,
        get_fail_safe=get_fail_safe(),
    )

    print_prompt_output(persona.direct_mem.name, prompt, output, elapsed_time)
    return output


def generate_prompt(prompt_input, prompt_file_path):
    if type(prompt_input) == str:
        prompt_input = [prompt_input]
    prompt_input = [str(arg) for arg in prompt_input]

    f = open(prompt_file_path, "r", encoding="utf-8")
    prompt = f.read()
    f.close()
    for count, arg in enumerate(prompt_input):
        prompt = prompt.replace(f"#<INPUT {count}>#", arg)
    if "<BLOCK></BLOCK>" in prompt:
        prompt = prompt.split("<BLOCK></BLOCK>")[1]
    return prompt.strip()
