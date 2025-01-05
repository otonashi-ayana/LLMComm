from typing import *


class Tools:
    def __init__(self) -> None:
        self.toolConfig = self._tools()

    def _tools(self) -> list[dict, Any]:
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "leave_chat",
                    "description": "如果你认为对话已经自然结束、对话变得无意义或重复、或者你无话可说，务必调用该工具来结束发言",
                    "parameters": {},
                },
            },
        ]
        return tools

    def leave_chat(self) -> None:
        print("Tools: leave_chat function was called")
