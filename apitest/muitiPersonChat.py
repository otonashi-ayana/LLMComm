import uuid
import random
from openai import OpenAI

tools = [
    {
        "type": "function",
        "function": {
            "name": "end_talk",
            "description": "当你们准备再见时，此功能可以结束你们的聊天",
            "parameters": {},
        },
    },
]


class DigitalHuman:
    def __init__(self, name, age, work, personality, background):
        self.id = str(uuid.uuid4())
        self.name = name
        self.age = age
        self.work = work
        self.personality = personality
        self.background = background
        self.place = None  # 所在场所
        self.memory = []  # 个人的聊天记忆
        self.active = True  # 是否仍参与聊天
        self.speak_probability = 0.5  # 后续根据大模型评分或性格得分计算

    def decide_to_speak(self):
        """决定是否发言"""
        return random.random() < self.speak_probability

    def join_place(self, place):
        """加入一个聊天场所"""
        if self.place:
            self.leave_place()
        self.place = place
        place.add_member(self)

    def leave_place(self):
        """离开当前聊天场所"""
        if self.place:
            self.place.remove_member(self)
            self.place = None

    def receive_message(self, client, shared_memory, current_memory):
        """
        处理收到的消息，target 指定是否明确谈话对象。
        """
        mentioned = False
        for mem in current_memory:
            if self.name not in mem:
                continue
            else:
                # print(current_memory)
                mentioned = True
                break
        if not mentioned and not self.decide_to_speak():
            return None

        system_prompt = (
            f"1.你是一位社区居民，正在与其他居民进行一对一或群体聊天。请参考你的个人信息和历史对话内容，仅输出你的发言部分，不要包含其他任何信息。确保语言风格口语化、生活化，接地气，贴近日常交流。注意事项：\n- 当感觉到聊天内容不再有进展或你想要离开场所时，请礼貌地结束对话并同时调用`end_talk`函数。\n- 内向型居民较少发言, 外向型居民可以发言频率略高。\n- 回复应自然流畅，避免使用过于正式或书面化的表达方式，单次发言不得超过20字。 "
            f"2.以下是你的个人信息：姓名：{self.name}\n 年龄：{self.age}\n 工作：{self.work}\n 性格特征：{self.personality}\n 背景故事：{self.background}\n"
        )
        # 添加场所中其他成员的个人信息
        system_prompt += "3.当前场所中的其他居民信息如下：\n"
        for member in self.place.members:
            if member != self:
                system_prompt += f"- 姓名：{member.name}，年龄：{member.age}，工作：{member.work}，性格特征：{member.personality}，背景故事：{member.background}\n"
        system_prompt += "4.场所中最近的发言记录如下：\n"
        for idx, mem in enumerate(shared_memory[-10:]):  # 只取最近的10条公共记忆
            system_prompt += f"{idx+1}. {mem}\n"
        member_list = [member.name for member in self.place.members if member != self]

        user_prompt = (
            f"场所中的成员有：[{', '.join(member_list)}]。\n"
            f'现在你需要：\n1. 决定是否发言；如果必须要发言，选择你发言的对象并说出内容。返回结构化的 JSON，包含 `target` 字段（值为场所中成员的名称。如果没有特定的对象，则值为“全体”）和 `context` 字段（回复内容）。\n2. 如果不发言，返回空JSON"{{}}"。\n'
        )

        response = client.chat.completions.create(
            model="qwen-plus",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            tools=tools,
        )
        # print(system_prompt)
        # print(user_prompt)
        return response.choices[0].message

    def generate_answer(self, response_message, shared_memory):
        """
        解析结构化回复或调用工具。
        """
        if not response_message:
            return "no_reply"
        if response_message.tool_calls:  # 检查工具调用
            for tool_call in response_message.tool_calls:
                function = tool_call.function
                # if function.name != "reply":
                #     return "no_reply"
                if function.name == "end_talk":
                    print(f"[{self.name}] 结束谈话。")
                    self.active = False

        try:
            # print(self.name,response_message)
            reply_data = eval(response_message.content)  # 假设返回是有效 JSON 格式
            target = reply_data.get("target", "全体")
            context = reply_data.get("context", "")
            if context:
                message_context = f"[{self.name}] 对 [{target}] 说：{context}"
                shared_memory.append(message_context)
                print(message_context)
                return message_context
            else:
                return "no_reply"
        except Exception as e:
            print(f"[{self.name}] 回复解析错误：{e}")
            return None


class Place:
    def __init__(self, name):
        self.name = name
        self.members = []  # 当前场所内的居民
        self.shared_memory = []  # 场所的共享聊天记录

    def add_member(self, member):
        """添加成员到场所"""
        self.members.append(member)
        print(f"{member.name} 来到了 {self.name}。")

    def remove_member(self, member):
        """从场所移除成员"""
        if member in self.members:
            self.members.remove(member)
            print(f"{member.name} 离开了 {self.name}。")

    def broadcast_message(
        self,
        client,
        sender,
        message,
        target=None,
    ):
        """
        在场所中广播消息，并生成回复。
        target: None 表示全体发言，字符串表示特定对象。
        """
        sender_name = sender.name
        message_context = f"[{sender_name}] 对 [{target.name}] 说：{message}"
        self.shared_memory.append(message_context)
        print(message_context)

        # 遍历其他成员，让他们基于共享记录生成回复
        for member in self.members:
            if (
                member != sender
                and target.name == member.name
                or member.decide_to_speak()
                and member.active
            ):
                response_message = member.receive_message(
                    client,
                    self.shared_memory,
                    current_memory=[f" 对 [{target.name}] 说：{message}"],
                )
                reply = member.generate_answer(response_message, self.shared_memory)
                if reply == "no_reply":
                    continue
                if not member.active:
                    # 如果某个成员调用了 end_talk，则移除该成员
                    self.remove_member(member)

    def start_conversation(self, client, sender, message, target=None):
        """
        启动自动化群聊逻辑。
        """
        self.broadcast_message(client, sender, message, target)
        temp_current_memory = []
        while len(self.members) > 1:  # 至少两人时继续聊天
            current_memory = []
            for member in list(self.members):  # 遍历当前活跃的成员
                if not sender.active:
                    continue
                response_message = member.receive_message(
                    client, self.shared_memory, temp_current_memory
                )
                reply = member.generate_answer(response_message, self.shared_memory)
                if reply == "no_reply":
                    continue
                current_memory.append(reply.split("]", 1)[1])
                if not member.active:
                    # 如果某个成员调用了 end_talk，则移除该成员
                    self.remove_member(member)
            temp_current_memory = current_memory


def main():
    client = OpenAI(
        api_key="sk-f690a69ebfdd4298a8c7ef763c42de28",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )

    # 创建场所
    supermarket = Place("超市")

    # 创建居民
    residents = [
        DigitalHuman(
            "李华", 45, "超市老板", "开朗善良，喜欢聊天", "在社区内开有一家小超市"
        ),
        DigitalHuman("王敏", 46, "企业员工", "内向，不善交际", "上班族，喜欢钓鱼"),
        DigitalHuman("赵强", 50, "出租车司机", "幽默风趣", "熟悉城市角落，喜欢讲故事"),
        DigitalHuman(
            "张三", 15, "初中生", "活泼乐观", "喜欢买零食，与社区居民关系融洽"
        ),
    ]

    # 加入场所
    for resident in residents:
        resident.join_place(supermarket)

    # 开始聊天
    supermarket.start_conversation(
        client=client,
        sender=residents[2],
        message="老板来包华子。今天超市生意怎么样？",
        target=residents[0],
    )


if __name__ == "__main__":
    main()
