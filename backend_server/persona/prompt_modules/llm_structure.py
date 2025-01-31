import sys

sys.path.append("../../")
import time
from openai import OpenAI
from utils import *
from global_methods import *


def temp_sleep(seconds=0.1):
    time.sleep(seconds)


def LLM_request(prompt, parameter):
    temp_sleep()
    client = OpenAI(api_key=api_key, base_url=base_url)
    # try:
    response = client.chat.completions.create(
        model=parameter["model"],
        messages=[{"role": "user", "content": prompt}],
        max_tokens=parameter["max_tokens"],
        temperature=parameter["temperature"],
        top_p=parameter["top_p"],
        stream=parameter["stream"],
        # presence_penalty=parameter["presence_penalty"],
        stop=parameter["stop"],
    )
    response_dump = response.model_dump()
    if debug:
        print_c(
            "prompt_tokens(cache hit):",
            response_dump["usage"]["prompt_cache_hit_tokens"],
        )
        print_c(
            "prompt_tokens(cache_miss):",
            response_dump["usage"]["prompt_cache_miss_tokens"],
        )
        print_c("completion_tokens:", response_dump["usage"]["completion_tokens"])
    return response_dump["choices"][0]["message"]["content"]


def generate_response(
    prompt,
    parameter,
    func_clean=None,
    func_valid=None,
):
    for i in range(3):
        curr_gpt_response = LLM_request(prompt, parameter)
        if func_valid(curr_gpt_response):
            return func_clean(curr_gpt_response)
        print("\n### Wrong response repeat count: ", i, "###")
        print(curr_gpt_response)
        print("########################################")
    return "error"
