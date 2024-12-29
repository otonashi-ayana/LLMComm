import uuid
import os
from openai import OpenAI

tools = [
    {
        "type": "function",
        "function": {
            "name": "end_talk",
            "description": "当你们准备再见时，此功能可以结束你们的聊天",
            "parameters": {}
        }
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
        self.memory = []

    def generate_prompt(self, message):
        system_prompt = f"姓名：{self.name}\n年龄：{self.age}\n工作：{self.work}\n性格特征：{self.personality}\n背景故事：{self.background}\n"

        system_prompt += "以下是之前的对话：\n"
        for idx, mem in enumerate(self.memory[-5:]):
            system_prompt += f"{idx+1}. {mem}\n"
        user_prompt = f"现在，{self.name}听到回复：\"{message}\""
        return system_prompt, user_prompt

    def receive_message(self, client, message):
        system_prompt, user_prompt = self.generate_prompt(message)

        response = client.chat.completions.create(
            model="qwen-plus",
            messages=[
                {
                    "role": "system",
                    "content": '你是一位社区居民，正在与其他居民进行聊天。请参考提供的历史对话内容，仅输出你的回复部分，不要包含其他任何信息。确保语言风格口语化、生活化，贴近日常交流。'
                               '注意事项： - 当感觉到聊天话题即将结束或双方开始重复相同的内容时，请礼貌地结束对话并同时调用`end_talk`函数。'
                               ' - 回复应自然流畅，避免使用过于正式或书面化的表达方式，单次发言不得超过20字。 历史对话：' + system_prompt
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ],
            tools=tools,
            # temperature=1.6,
        )
        response_message = response.choices[0].message
        print(response_message)
        return response_message
    
    def generate_answer(self,response_message, message):
        reply_content = response_message.content #我的回复文本
        self.memory.append(f"对方：{message}\n我：{reply_content}")
        print(f"[{self.name}] :{reply_content}\n")

        #检查是否调用end_talk
        if response_message.tool_calls: 
            for tool_call in response_message.tool_calls:
                function = tool_call.function
                if function and function.name == "end_talk":
                    return None
        return reply_content


def main():
    client = OpenAI(
        api_key="sk-f690a69ebfdd4298a8c7ef763c42de28",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
    )

    digital_human_a = DigitalHuman(
        name='李华',
        age=45,
        work='超市老板',
        personality='开朗善良，喜欢聊天',
        background='在社区内开有一家小规模私人超市，经常有社区居民光顾'
    )

    digital_human_b = DigitalHuman(
        name='王敏',
        age=46,
        work='企业员工',
        personality='内向，不善交际，理性老实',
        background='上班族，平日比较忙，喜欢钓鱼'
    )

    message_from_b = '老李早啊，去不去打麻将？'
    print(f"[{digital_human_b.name}说]：{message_from_b}")
    while True:
        response_message_a = digital_human_a.receive_message(client, message_from_b)
        reply_a = digital_human_a.generate_answer(response_message_a, message_from_b)
        if reply_a: message_from_a = reply_a
        else: break

        response_message_b = digital_human_b.receive_message(client, message_from_a)
        reply_b = digital_human_b.generate_answer(response_message_b, message_from_a)
        if reply_b: message_from_b = reply_b
        else: break

if __name__ == '__main__':
    main()
