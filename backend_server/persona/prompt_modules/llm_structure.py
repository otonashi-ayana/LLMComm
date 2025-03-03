import sys

sys.path.append("../../")
import time
from openai import OpenAI, OpenAIError
from utils import *
from global_methods import *


def temp_sleep(seconds=0.1):
    time.sleep(seconds)


def LLM_request(prompt, parameter):
    temp_sleep()

    client = OpenAI(api_key=api_key, base_url=base_url)
    for i in range(5):
        try:
            start_time = time.time()
            response = client.chat.completions.create(
                model=parameter["model"],
                messages=[{"role": "user", "content": prompt}],
                max_tokens=parameter["max_tokens"],
                temperature=parameter["temperature"],
                top_p=parameter["top_p"],
                stream=parameter["stream"],
                # presence_penalty=parameter["presence_penalty"],
                stop=parameter["stop"],
                # timeout=60,
            )
            break
        except OpenAIError as e:
            print(f"tried times({i}) LLM_request error:", e)
    end_time = time.time()
    elapsed_time = end_time - start_time
    response_dump = response.model_dump()
    if base_url == "https://api.deepseek.com":
        print_c(
            "prompt_tokens(cache hit):",
            response_dump["usage"]["prompt_cache_hit_tokens"],
        )
        print_c(
            "prompt_tokens(cache_miss):",
            response_dump["usage"]["prompt_cache_miss_tokens"],
        )
        print_c("completion_tokens:", response_dump["usage"]["completion_tokens"])
    return response_dump["choices"][0]["message"]["content"], elapsed_time


def get_embedding(text, model=emb_specify_model):
    text = text.replace("\n", " ")
    if not text:
        text = "this is blank"
    client = OpenAI(api_key=emb_api_key, base_url=emb_base_url)
    response = client.embeddings.create(
        model=model, input=text, dimensions=1024, encoding_format="float"
    )
    response_dump = response.model_dump()
    return response_dump["data"][0]["embedding"]


def generate_response(
    prompt,
    parameter,
    func_clean=None,
    func_valid=None,
    get_fail_safe="error",
):
    for i in range(4):
        curr_gpt_response, elapsed_time = LLM_request(prompt, parameter)
        if func_valid(curr_gpt_response):
            return func_clean(curr_gpt_response), elapsed_time
        print_c("\n--- Wrong response repeat count:", i, "---")
        print(curr_gpt_response)
        print_c("--------------------------------------------")
        temp_sleep(1)
    return get_fail_safe, 0
