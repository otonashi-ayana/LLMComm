from tools import Tools
from chatmodel import ChatModel
import uuid


class Agent:
    def __init__(self, name, age, work, personality, background) -> None:
        self.toolConfig = Tools().toolConfig
        self.model = ChatModel()
        self._prompt()

        self.id = str(uuid.uuid4())
        self.name = name
        self.age = age
        self.work = work
        self.personality = personality
        self.background = background
        self.place = None

    def __str__(self):
        return f"{self.name}，年龄：{self.age}，职业：{self.work}，性格：{self.personality}，背景故事：{self.background}"

    def _prompt(self) -> None:
        self.PROMPT = """你是一位社区居民，正在与其他居民进行聊天。参考所提供对话内容，作出你的回复或行为。发言务必口语化、生活化，贴近日常交流，自然流畅。严禁使用不符合日常生活的书面语，单次发言不得超过20字。注意事项：
        1.你可以使用以下工具来帮助完成你的目的：\n{tool_info}
        2.你的个人信息为：{self_info}
        3.当前你所在场所“{place}”的在场成员信息为：\n{member_info}
        4.当前场所中最近的发言记录如下：\n{shared_memory}
        5.务必输出JSON格式回答：{{
        'Thought':str(针对聊天给出关于下一步回应的思考),
        'Action':None|str(根据思考选择是否调用工具，如果不调用则为None),
        'Parameter':None|str(输入工具的参数),
        'Answer':{{'target':None|str(你的发言所指定的对象，如果不特定某人则为None),'context':None|str(发言内容)}}}}"""
        self.TOOL_INFO = "{name}：工具描述：{description}，输入参数：{parameters}"

    def build_system_input(self, member_info, shared_memory) -> str:
        tool_info = []
        for tool in self.toolConfig:
            tool_info.append(self.TOOL_INFO.format(**tool["function"]))
        tool_info = "\n".join(tool_info)
        return self.PROMPT.format(
            tool_info=tool_info,
            self_info=self.__str__(),
            place=self.place.name,
            member_info=member_info,
            shared_memory=shared_memory,
        )

    def generate_answer(self, current_chat, member_info, shared_memory):
        system_input = self.build_system_input(member_info, shared_memory)
        messages = [
            {"role": "system", "content": system_input},
            {"role": "user", "content": current_chat},
        ]
        print(f"{self.name}:")
        print(messages)
        res_dict = self.model.get_response(messages=messages)["choices"][0]["message"]
        print(res_dict)
        print()
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
