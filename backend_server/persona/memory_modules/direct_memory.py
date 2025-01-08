import json


class DirectMemory:
    def __init__(self):
        """世界信息"""
        self.curr_time = None  # 感知到的世界时间
        self.curr_tile = None  # 当前位置坐标，格式为 (x, y)

        """个人核心信息"""
        self.name = None
        self.name_en = None
        self.age = None
        self.gender = None
        self.personality = None
        self.background = None
        self.living_area = None

        """个人超参数"""
        self.vision_r = 5  # 视觉范围，单位为块

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

        # self.act_obj_event = (self.name, None, None)
        # self.act_obj_description = None

        self.chatting_with = None  # 当前对话对象
        self.chatting_end_time = None  # 对话结束时间

        self.chat_history = None  # 对话历史
        # [["张三", "Hi"],
        # ["李四", "Hi"] ...]
        # 对话历史只传递内容，动作感知交给感知模块处理

        # TODO:读取保存到本地的memory文件，恢复记忆状态

    def save(self, out_json):
        scratch = dict()
        scratch["curr_time"] = self.curr_time.strftime("%B %d, %Y, %H:%M:%S")
        scratch["curr_tile"] = self.curr_tile

        scratch["name"] = self.name
        scratch["name_en"] = self.name_en
        scratch["age"] = self.age
        scratch["gender"] = self.gender
        scratch["personality"] = self.personality
        scratch["background"] = self.background
        scratch["living_area"] = self.living_area

        scratch["vision_r"] = self.vision_r

        scratch["daily_goals"] = self.daily_goals
        scratch["daily_schedule"] = self.daily_schedule

        scratch["act_event"] = self.act_event
        scratch["act_address"] = self.act_address
        scratch["act_start_time"] = self.act_start_time.strftime("%B %d, %Y, %H:%M:%S")
        scratch["act_duration"] = self.act_duration
        scratch["act_description"] = self.act_description

        # scratch["act_obj_event"] = self.act_obj_event
        # scratch["act_obj_description"] = self.act_obj_description

        scratch["chatting_with"] = self.chatting_with
        if self.chatting_end_time:
            scratch["chatting_end_time"] = self.chatting_end_time.strftime(
                "%B %d, %Y, %H:%M:%S"
            )
        else:
            scratch["chatting_end_time"] = None

        with open(out_json, "w") as outfile:
            json.dump(scratch, outfile, indent=2)

    def get_str_mds(self):
        """
        获得最小描述集合(Minimal description set),基本的角色信息
        """
        description = ""
        description += f"姓名:{self.name}\n"
        description += f"年龄:{self.age}\n"
        description += f"性别:{self.gender}\n"
        description += f"性格:{self.personality}\n"
        description += f"背景:{self.background}\n"
        # description += f"居住区域:{self.living_area}\n"
        description += f"日常目标:{self.daily_goals}\n"
        description += f"当前日期:{self.curr_time.strftime('%A %B %d')}\n"
        return description

    # TODO:get方法

    def add_new_action(
        self,
        action_event,
        action_address,
        action_duration,
        action_description,
        chatting_with,
        chat_history,
        chatting_end_time,
    ):
        self.act_event = action_event
        self.act_address = action_address
        self.act_duration = action_duration
        self.act_description = action_description

        self.chatting_with = chatting_with
        self.chat_history = chat_history
        self.chatting_end_time = chatting_end_time

        # self.act_obj_description = act_obj_description
        # self.act_obj_event = act_obj_event

        self.act_start_time = self.curr_time  # 动作开始时间是新的当前时间
