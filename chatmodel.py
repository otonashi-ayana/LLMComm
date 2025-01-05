from openai import OpenAI
from typing import *


class ChatModel:
    def __init__(self) -> None:
        self.load_model(
            "sk-f690a69ebfdd4298a8c7ef763c42de28",
            "https://dashscope.aliyuncs.com/compatible-mode/v1",
        )
        self.specify_model("qwen-plus")

    def load_model(self, api_key: str, base_url: str) -> None:
        self.client = OpenAI(api_key=api_key, base_url=base_url)

    def specify_model(self, model_name: str) -> None:
        self.model_name = model_name

    def get_response(
        self,
        messages: str,  # tools: list[dict[str, Any]]
    ) -> dict[str, Any]:
        model_completion = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            response_format={"type": "json_object"},
        )
        return model_completion.model_dump()
