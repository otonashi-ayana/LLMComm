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
                    "description": "当你想离开当前的发言时非常有用",
                    "parameters": {},
                },
            },
        ]
        return tools

    def leave_chat(self) -> None:
        print("Tools: leave_chat function was called")
