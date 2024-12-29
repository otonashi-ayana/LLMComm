from agent import Agent
from chatmodel import ChatModel
from tools import Tools
from Place import Place

tools = Tools()
ChatModel = ChatModel()

market = Place("超市")

shared_mem = []
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

shared_memories = []

current_chat = "'赵强':{'target':'李华','context':'老板来包华子。今天超市生意怎么样？'}"
shared_memories.append(current_chat)

for i in range(5):
    for member in market.members:
        other_members = [str(mem) for mem in market.members if mem != member]
        res_dict = member.generate_answer(
            current_chat=current_chat,
            member_info="\n".join(other_members),
            shared_memory="\n".join(shared_memories),
        )
        # current_chat =
    # shared_mem.append()
