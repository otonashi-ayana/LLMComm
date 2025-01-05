from agent import Agent
from chatmodel import ChatModel
from tools import Tools
from Place import Place
from datetime import datetime
import json
import os

os.system("cls")
tools = Tools()
ChatModel = ChatModel()

market = Place("超市")
scenario = "你是一位社区居民，正在与其他居民进行日常聊天。"
shared_memory = []
residents_info = []

residents = [
    Agent("李华", 45, "超市老板", "开朗善良，喜欢聊天", "在社区内开有一家小超市"),
    Agent("王敏", 46, "企业员工", "内向，不善交际", "上班族，喜欢钓鱼"),
    Agent("赵强", 50, "出租车司机", "幽默风趣", "熟悉城市角落，喜欢讲故事"),
    Agent("张三", 15, "初中生", "活泼乐观", "喜欢买零食，与社区居民关系融洽"),
]

for resident in residents:
    residents_info.append(str(resident))

for resident in residents:
    resident.join_place(market)


def save_dialogue(sender, receiver, context, action=None, action_param=None):
    dialogue = {
        "timestamp": datetime.now().isoformat(),
        "sender": sender,
        "receiver": receiver,
        "context": context,
        "action": action,
        "action_param": action_param,
    }
    shared_memory.append(dialogue)
    if len(shared_memory) > 10:
        shared_memory.pop(0)


save_dialogue("赵强", "李华", "老板来包华子。今天超市生意怎么样？")
print(shared_memory)
for i in range(10):
    for member in market.members:
        respond = member.generate_answer(
            scenario=scenario,
            member_info="\n".join(
                [str(mem) for mem in market.members if mem != member]
            ),
            shared_memory=shared_memory,
        )
        # 将返回结果中的 content 字符串解析为字典
        content = json.loads(respond)

        save_dialogue(
            member.name,
            content["Answer"]["receiver"],  # 访问解析后的字典
            content["Answer"]["context"],
        )
