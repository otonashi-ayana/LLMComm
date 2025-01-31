"""
定义运行prompt的所有函数
"""

import datetime
import random
import string
import re
import sys

sys.path.append("../../")
from persona.prompt_modules.llm_structure import *
from global_methods import *

from utils import *


def get_random_alphanumeric(i=6, j=6):
    k = random.randint(i, j)
    x = "".join(random.choices(string.ascii_letters + string.digits, k=k))
    return x


def run_prompt_wake_up_time(persona):
    """

    返回给定persona的起床时间(integer)
    """

    def create_prompt_input(persona):
        prompt_input = [persona.direct_mem.get_str_mds()]
        return prompt_input

    def response_clean(response):
        return int(response.strip().lower().split("am")[0])

    def response_validate(response):
        try:
            response_clean(response)
        except:
            return False
        return True

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
    if debug:
        print("\n")
        print_c("╔═════<run_prompt_wake_up_time> prompt═════╗")
        print(prompt)
        print_c(
            "╚══════════════════════════════════════════╝",
        )
    output = generate_response(
        prompt, model_param, func_clean=response_clean, func_valid=response_validate
    )
    if debug:
        print_c("╔═════<run_prompt_wake_up_time> output═════╗")
        print(output)
        print_c("╚══════════════════════════════════════════╝")
    return output


def run_prompt_daily_goals(persona, wake_up_time):
    def create_prompt_input(persona, wake_up_time):
        prompt_input = []
        prompt_input += [persona.direct_mem.get_str_mds()]
        # prompt_input += [persona.direct_mem.get_curr_date()]
        # prompt_input += [f"{str(wake_up_time)}"]
        return prompt_input

    def response_clean(response):
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

    def response_validate(response):
        try:
            response_clean(response)
        except Exception as e:
            print(e)
            return False
        return True

    model_param = {
        "model": specify_model,
        "max_tokens": 100,
        "temperature": 1.3,
        "top_p": 1,
        "stream": False,
        "stop": None,
    }
    prompt_file_path = f"{prompt_path}/plan/daily_planning_v1.txt"
    prompt_input = create_prompt_input(persona, wake_up_time)
    prompt = generate_prompt(prompt_input, prompt_file_path)
    if debug:
        print("\n")
        print_c("╔═════<run_prompt_daily_goals> prompt═════╗")
        print(prompt)
        print_c("╚═════════════════════════════════════════╝")
    output = generate_response(
        prompt, model_param, func_clean=response_clean, func_valid=response_validate
    )
    output = [f"{wake_up_time}点起床"] + output
    if debug:
        print_c("╔═════<run_prompt_daily_goals> output═════╗")
        print(output)
        print_c("╚═════════════════════════════════════════╝")
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

    def response_clean(response):
        cl = response.strip().split()[-1]
        if cl[0] == "[":
            raise ValueError()
        if cl[-1] in [".", "。"]:
            cl = cl[:-1]
        return cl

    def response_validate(response):
        try:
            response_clean(response)
        except:
            return False
        return True

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
    if debug:
        print("\n")
        print_c("╔══<run_prompt_generate_hourly_schedule> prompt══╗")
        print(prompt)
        print_c("╚════════════════════════════════════════════════╝")
    output = generate_response(
        prompt, model_param, func_clean=response_clean, func_valid=response_validate
    )
    if debug:
        print_c("╔══<run_prompt_generate_hourly_schedule> output══╗")
        print(output)
        print_c("╚════════════════════════════════════════════════╝")
    return output


def run_gpt_prompt_task_decomp(persona, task, duration):
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

        curr_time_range = ""

        summ_str = f'今天日期是 {persona.direct_mem.curr_time.strftime("%A %B %d")}. '
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
                summ_str += f"{start_time_str} ~ {end_time_str}点, {persona.direct_mem.name} 计划 {persona.direct_mem.daily_schedule_hourly[index][0]}, "
                if curr_f_org_index + 1 == index:
                    curr_time_range = f"{start_time_str} ~ {end_time_str}"
        summ_str = summ_str[:-2] + "."

        prompt_input = []
        prompt_input += [persona.direct_mem.get_str_mds()]
        prompt_input += [summ_str]
        # prompt_input += [persona.direct_mem.get_str_curr_date_str()]
        prompt_input += [persona.direct_mem.name]
        prompt_input += [curr_time_range]
        prompt_input += [task]
        prompt_input += [duration]
        prompt_input += [persona.direct_mem.name]
        return prompt_input

    def response_clean(response):
        temp = [i.strip() for i in response.split("\n")]
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

    def response_validate(response):
        try:
            response_clean(response)
        except:
            return False
        return True

    model_param = {
        "model": specify_model,
        "max_tokens": 700,
        "temperature": 1,
        "top_p": 1,
        "stream": False,
        "stop": None,
    }
    prompt_template = f"{prompt_path}/plan/task_decomp_v1.txt"
    prompt_input = create_prompt_input(persona, task, duration)
    prompt = generate_prompt(prompt_input, prompt_template)
    if debug:
        print("\n")
        print_c("╔═════<run_gpt_prompt_task_decomp> prompt═════╗")
        print(prompt)
        print_c("╚═════════════════════════════════════════════╝")
    output = generate_response(
        prompt, model_param, func_clean=response_clean, func_valid=response_validate
    )
    if debug:
        print_c("╔═════<run_gpt_prompt_task_decomp> output═════╗")
        print(output)
        print_c("╚═════════════════════════════════════════════╝")
    return output


def run_gpt_prompt_action_sector(act_desp, persona, maze):
    def create_prompt_input(act_desp, persona, maze):
        prompt_input = []
        return prompt_input

    def response_clean(response):
        pass

    def response_validate(response):
        try:
            response_clean(response)
        except:
            return False
        return True

    model_param = {
        "model": specify_model,
        "max_tokens": 5,
        "temperature": 0.8,
        "top_p": 0.8,
        "stream": False,
        "stop": None,
    }
    prompt_template = f"{prompt_path}/#TODO/#TODO.txt"
    prompt_input = create_prompt_input()
    prompt = generate_prompt(prompt_input, prompt_template)
    if debug:
                 print("\n")
        print_c("╔══<#TODO> prompt══╗")
                 print(prompt)
        print_c("╚══════════════════╝")
    output = generate_response(
        prompt, model_param, func_clean=response_clean, func_valid=response_validate
    )
    if debug:
        print_c("╔══<#TODO> output══╗")
                 print(output)
        print_c("╚══════════════════╝")
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
