import sys

sys.path.append("../../")

import datetime
import json

from global_methods import *


class DirectMemory:
    def __init__(self, mem_path):
        """世界信息"""
        self.curr_time = None  # 感知到的世界时间
        self.curr_cell = None  # 当前位置坐标，格式为 (x, y)

        """个人核心信息"""
        self.name = None
        self.name_en = None
        self.age = None
        self.gender = None
        self.personality = None
        self.background = None
        self.curr_thing = None
        self.living_area = None
        self.life_style = None
        self.daily_plan_desc = None  # =daily_plan_req

        """个人超参数"""
        self.vision_r = 5  # 视觉范围，单位为块
        self.att_bandwidth = 3  # 每次选择接受的事件数量
        self.retention = 5  # 事件感知冷却step

        # self.latest_events = []
        # 是一个队列，最近感知到的事件列表，格式为 [(s, p, o, desc), ...]

        """每日计划"""
        # e.g., ['Work on her paintings for her upcoming show',
        #        'Take a break to watch some TV',
        #        'Make lunch for herself',
        #        'Work on her paintings some more',
        #        'Go to bed early']
        self.daily_goals = []
        # e.g., [['sleeping', 360],
        #         ['wakes up and ... (wakes up and stretches ...)', 5],
        #         ['wakes up and starts her morning routine (out of bed )', 10],
        #         ...
        #         ['having lunch', 60],
        #         ['working on her painting', 180], ...]
        self.daily_schedule = []
        self.daily_schedule_hourly = []

        """当前动作"""
        self.act_event = (
            self.name,
            None,
            None,
        )  # 三元组表示正在执行的动作，格式为 (主体, 动作, 目标)
        self.act_address = None  # "{world}:{sector}:{arena}:{game_objects}"
        self.act_start_time = None  # 动作开始时间
        self.act_duration = None  # 动作预计持续时间 int
        self.act_description = None  # 动作描述

        self.act_obj_event = (self.name, None, None)
        self.act_obj_description = None

        self.chatting_with = None  # 当前对话对象
        self.chatting_end_time = None  # 对话结束时间

        self.chat_history = None  # 对话历史
        self.chatting_with_buffer = dict()  # 对话历史
        # [["张三", "Hi"],
        # ["李四", "Hi"] ...]
        # 对话历史只传递内容，动作感知交给感知模块处理
        self.chatting_end_time = None

        self.act_path_set = False
        self.planned_path = []

        # reflection variables
        self.recency_w = 1
        self.relevance_w = 1
        self.importance_w = 1
        self.recency_decay = 0.99

        self.importance_trigger_max = 150
        self.importance_trigger_curr = self.importance_trigger_max
        self.importance_ele_n = 0

        if check_if_file_exists(mem_path):
            direct_mem_json = json.load(open(mem_path, encoding="utf-8"))

            self.vision_r = direct_mem_json["vision_r"]
            self.att_bandwidth = direct_mem_json["att_bandwidth"]
            self.retention = direct_mem_json["retention"]

            if direct_mem_json["curr_time"]:
                self.curr_time = datetime.datetime.strptime(
                    direct_mem_json["curr_time"], "%B %d, %Y, %H:%M:%S"
                )
            else:
                self.curr_time = None
            self.curr_cell = direct_mem_json["curr_cell"]

            self.name = direct_mem_json["name"]
            self.name_en = direct_mem_json["name_en"]
            self.age = direct_mem_json["age"]
            self.gender = direct_mem_json["gender"]
            self.personality = direct_mem_json["personality"]
            self.background = direct_mem_json["background"]
            self.curr_thing = direct_mem_json["curr_thing"]
            self.living_area = direct_mem_json["living_area"]
            self.life_style = direct_mem_json["life_style"]
            self.daily_plan_desc = direct_mem_json["daily_plan_desc"]

            self.daily_goals = direct_mem_json["daily_goals"]
            self.daily_schedule = direct_mem_json["daily_schedule"]
            self.daily_schedule_hourly = direct_mem_json["daily_schedule_hourly"]

            self.act_address = direct_mem_json["act_address"]
            if direct_mem_json["act_start_time"]:
                self.act_start_time = datetime.datetime.strptime(
                    direct_mem_json["act_start_time"], "%B %d, %Y, %H:%M:%S"
                )
            else:
                self.curr_time = None
            self.act_duration = direct_mem_json["act_duration"]
            self.act_description = direct_mem_json["act_description"]
            self.act_event = tuple(direct_mem_json["act_event"])

            self.act_obj_description = direct_mem_json["act_obj_description"]
            self.act_obj_event = tuple(direct_mem_json["act_obj_event"])

            self.chatting_with = direct_mem_json["chatting_with"]
            self.chat_history = direct_mem_json["chat_history"]
            self.chatting_with_buffer = direct_mem_json["chatting_with_buffer"]
            if direct_mem_json["chatting_end_time"]:
                self.chatting_end_time = datetime.datetime.strptime(
                    direct_mem_json["chatting_end_time"], "%B %d, %Y, %H:%M:%S"
                )
            else:
                self.chatting_end_time = None

            self.act_path_set = direct_mem_json["act_path_set"]
            self.planned_path = direct_mem_json["planned_path"]

            self.recency_w = direct_mem_json["recency_w"]
            self.relevance_w = direct_mem_json["relevance_w"]
            self.importance_w = direct_mem_json["importance_w"]
            self.recency_decay = direct_mem_json["recency_decay"]

            self.importance_trigger_max = direct_mem_json["importance_trigger_max"]
            self.importance_trigger_curr = direct_mem_json["importance_trigger_curr"]
            self.importance_ele_n = direct_mem_json["importance_ele_n"]

    def save(self, out_json):
        direct_mem = dict()

        direct_mem["vision_r"] = self.vision_r
        direct_mem["att_bandwidth"] = self.att_bandwidth
        direct_mem["retention"] = self.retention

        direct_mem["curr_time"] = self.curr_time.strftime("%B %d, %Y, %H:%M:%S")
        direct_mem["curr_cell"] = self.curr_cell

        direct_mem["name"] = self.name
        direct_mem["name_en"] = self.name_en
        direct_mem["age"] = self.age
        direct_mem["gender"] = self.gender
        direct_mem["personality"] = self.personality
        direct_mem["background"] = self.background
        direct_mem["curr_thing"] = self.curr_thing
        direct_mem["living_area"] = self.living_area
        direct_mem["life_style"] = self.life_style
        direct_mem["daily_plan_desc"] = self.daily_plan_desc

        direct_mem["daily_goals"] = self.daily_goals
        direct_mem["daily_schedule"] = self.daily_schedule
        direct_mem["daily_schedule_hourly"] = self.daily_schedule_hourly

        direct_mem["act_address"] = self.act_address
        direct_mem["act_start_time"] = self.act_start_time.strftime(
            "%B %d, %Y, %H:%M:%S"
        )
        direct_mem["act_duration"] = self.act_duration
        direct_mem["act_description"] = self.act_description
        direct_mem["act_event"] = self.act_event

        direct_mem["act_obj_description"] = self.act_obj_description
        direct_mem["act_obj_event"] = self.act_obj_event

        direct_mem["chatting_with"] = self.chatting_with
        direct_mem["chat_history"] = self.chat_history
        direct_mem["chatting_with_buffer"] = self.chatting_with_buffer
        if self.chatting_end_time:
            direct_mem["chatting_end_time"] = self.chatting_end_time.strftime(
                "%B %d, %Y, %H:%M:%S"
            )
        else:
            direct_mem["chatting_end_time"] = None

        direct_mem["act_path_set"] = self.act_path_set
        direct_mem["planned_path"] = self.planned_path

        direct_mem["recency_w"] = self.recency_w
        direct_mem["relevance_w"] = self.relevance_w
        direct_mem["importance_w"] = self.importance_w
        direct_mem["recency_decay"] = self.recency_decay

        direct_mem["importance_trigger_max"] = self.importance_trigger_max
        direct_mem["importance_trigger_curr"] = self.importance_trigger_curr
        direct_mem["importance_ele_n"] = self.importance_ele_n

        with open(out_json, "w", encoding="utf-8") as outfile:
            json.dump(direct_mem, outfile, indent=2, ensure_ascii=False, cls=MyEncoder)

    def act_check_finished(self):
        if not self.act_address:
            return True

        if self.chatting_with:
            end_time = self.chatting_end_time
        else:
            x = self.act_start_time
            if x.second != 0:
                x = x.replace(second=0)
                x = x + datetime.timedelta(minutes=1)
            end_time = x + datetime.timedelta(minutes=self.act_duration)

        if end_time.strftime("%H:%M:%S") == self.curr_time.strftime("%H:%M:%S"):
            return True
        return False

    def get_str_mds(self):
        """
        获得最小描述集合(Minimal description set),基本的角色信息
        """
        description = ""
        description += f"姓名:{self.name}\n"
        description += f"年龄:{self.age}\n"
        description += f"性别:{self.gender}\n"
        description += f"性格:{self.personality}\n"
        description += f"个人背景:{self.background}\n"
        description += f"近期事项:{self.curr_thing}\n"
        description += f"生活方式:{self.life_style}\n"
        # description += f"居住区域:{self.living_area}\n"
        description += f"生活规划:{self.daily_plan_desc}\n"
        description += f"当前日期:{self.curr_time.strftime('%A %B %d')}"
        return description

    def get_name(self):
        return self.name

    def get_daily_plan_desc(self):
        return self.daily_plan_desc

    def get_curr_event(self):
        if not self.act_address:  # 无当前event，返回persona,None*3
            return (self.name, None, None, None)
        else:
            return (
                self.act_event[0],
                self.act_event[1],
                self.act_event[2],
                self.act_description,
            )

    def get_curr_obj_event(self):
        if not self.act_address:  # 无当前event，没有obj被使用
            return ("", None, None, None)
        else:
            return (
                self.act_address,
                self.act_obj_event[1],
                self.act_obj_event[2],
                self.act_obj_description,
            )

    def get_curr_date(self):
        return self.curr_time.strftime("%A %B %d")

    def get_daily_schedule_index(self, advance=0):
        today_min_elapsed = 0
        today_min_elapsed += self.curr_time.hour * 60
        today_min_elapsed += self.curr_time.minute
        today_min_elapsed += advance

        x = 0
        for task, duration in self.daily_schedule_hourly:
            x += duration
        curr_index = 0
        elapsed = 0
        for task, duration in self.daily_schedule:
            elapsed += duration
            if elapsed > today_min_elapsed:
                return curr_index
            curr_index += 1

        return curr_index

    def get_daily_schedule_hourly_index(self, advance=0):
        """
        We get the current index of self.daily_schedule_hourly_org.
        It is otherwise the same as get_daily_schedule_index.

        INPUT
        advance: Integer value of the number minutes we want to look into the
                future. This allows us to get the index of a future timeframe.
        OUTPUT
        an integer value for the current index of daily_schedule.
        """
        # We first calculate teh number of minutes elapsed today.
        today_min_elapsed = 0
        today_min_elapsed += self.curr_time.hour * 60
        today_min_elapsed += self.curr_time.minute
        today_min_elapsed += advance
        # We then calculate the current index based on that.
        curr_index = 0
        elapsed = 0
        for task, duration in self.daily_schedule_hourly:
            elapsed += duration
            if elapsed > today_min_elapsed:
                return curr_index
            curr_index += 1
        return curr_index

    def add_new_action(
        self,
        act_address,
        act_duration,
        act_description,
        # action_pronunciatio,
        act_event,
        chatting_with,
        chat_history,
        chatting_with_buffer,
        chatting_end_time,
        act_obj_description,
        # act_obj_pronunciatio,
        act_obj_event,
        act_start_time=None,
    ):
        self.act_address = act_address
        self.act_duration = act_duration
        self.act_description = act_description
        # self.act_pronunciatio = action_pronunciatio
        self.act_event = act_event

        self.chatting_with = chatting_with
        self.chat_history = chat_history
        if chatting_with_buffer:
            self.chatting_with_buffer.update(chatting_with_buffer)
        self.chatting_end_time = chatting_end_time

        self.act_obj_description = act_obj_description
        # self.act_obj_pronunciatio = act_obj_pronunciatio
        self.act_obj_event = act_obj_event

        self.act_start_time = self.curr_time

        self.act_path_set = False
