from tools import Tools
from chatmodel import ChatModel
import uuid, json, textwrap


class Agent:
    def __init__(self, name, age, work, personality, background) -> None:
        self.toolConfig = Tools().toolConfig
        self.model = ChatModel()

        self.id = str(uuid.uuid4())
        self.name = name
        self.age = age
        self.work = work
        self.personality = personality
        self.background = background
        self.place = None
        self._prompt()

    def __str__(self):
        return f"{self.name}，年龄：{self.age}，职业：{self.work}，性格：{self.personality}，背景故事：{self.background}"

    def _prompt(self) -> None:
        self.PROMPT = textwrap.dedent(
            """
        {scenario}你的角色信息如下：
        - 姓名：{name}
        - 年龄：{age}
        - 职业：{work}
        - 性格：{personality}
        - 背景：{background}

        你的任务：
        1. 参与对话，回复其他人的发言，或者主动发起交流。
        2. 回复语言要口语化、生活化，符合中国人日常语言风格，单次发言不得超过 20 字。
        3. 使用以下工具来帮助完成任务，当你认为有必要使用时，务必主动使用：
        {tool_info}
        
        务必按照以下格式输出（JSON）：
        {{
            "Thought": str,  # 你的思考
            "Action": None|str,  # 是否调用工具，若不调用则为 None
            "Parameter": None|str,  # 工具调用所需参数
            "Answer": {{
                "receiver": None|str,  # 发言的目标对象，若不特定某人则为 None
                "context": str  # 发言内容
            }}
        }}
        """
        )
        self.TOOL_INFO = "{name}（工具描述：{description}，输入参数：{parameters}）"

    def build_system_content(self, scenario) -> str:
        tool_info = []
        for tool in self.toolConfig:
            tool_info.append(self.TOOL_INFO.format(**tool["function"]))
        tool_info = "\n".join(tool_info)
        return self.PROMPT.format(
            scenario=scenario,
            name=self.name,
            age=self.age,
            work=self.work,
            personality=self.personality,
            background=self.background,
            tool_info=tool_info,
        )

    def build_user_content(self, member_info, shared_memory) -> str:
        shared_memory_text = "\n".join(
            [
                f"[{dialogue['timestamp']}]【{dialogue['sender']}】对【{dialogue['receiver'] if dialogue['receiver'] else '全体'}】说：{dialogue['context']} (Action: {dialogue['action']}, Action param: {dialogue['action_param']})"
                for dialogue in shared_memory
            ]
        )
        content_lines = [
            f"当前场所信息：",
            f"- 场所名称：{self.place.name if self.place else '未知'}",
            f"- 场所中的其他成员：",
            f"{member_info}",
            f"",
            f"最近对话记录：",
            f"{shared_memory_text}",
        ]
        return "\n".join(content_lines).strip()

    def generate_answer(self, scenario, member_info, shared_memory):
        system_content = self.build_system_content(scenario)
        user_content = self.build_user_content(member_info, shared_memory)
        messages = [
            {"role": "system", "content": system_content},
            {"role": "user", "content": user_content},
        ]
        print("=" * 70)
        print(f"发言者 {self.name}:")
        # print("messages内容：")
        # for message in messages:
        #     print(message["content"])
        res_dict = self.model.get_response(messages=messages)["choices"][0]["message"][
            "content"
        ]
        print(f"\n生成结果：\n{res_dict}")
        return res_dict

    def join_place(self, place):
        if self.place:
            self.leave_place()
        self.place = place
        place.add_member(self)  # ?

    def leave_place(self):
        if self.place:
            self.place.remove_member(self)
            self.place = None
