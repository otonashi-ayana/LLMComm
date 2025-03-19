import sys

sys.path.append("../../")
import time
from openai import OpenAI, OpenAIError
from utils import *
from global_methods import *


def temp_sleep(seconds=0.1):
    time.sleep(seconds)


def CoT_LLM_request(prompt, parameter):
    temp_sleep()

    # 添加思维链引导
    cot_prompt = f"""任何输出都要有思考过程，输出内容必须以 "<think>\n\n嗯" 开头。仔细揣摩用户意图，在思考过程之后，提供逻辑清晰且内容完整的回答。\n\n{prompt}"""

    client = OpenAI(api_key=api_key, base_url=base_url)
    for i in range(3):
        try:
            start_time = time.time()
            response = client.chat.completions.create(
                model=parameter["model"],
                messages=[{"role": "user", "content": cot_prompt}],
                max_tokens=parameter["max_tokens"],
                temperature=parameter["temperature"],
                top_p=parameter["top_p"],
                stream=parameter["stream"],
                stop=parameter["stop"],
                timeout=300,
            )
            break
        except OpenAIError as e:
            print(f"CoT尝试次数({i}) LLM_request错误:", e)
    else:
        return "思维链请求失败，无法获取回复。", 0

    end_time = time.time()
    elapsed_time = end_time - start_time
    response_dump = response.model_dump()
    response_message = response_dump["choices"][0]["message"]
    try:
        reasoning_reasoning = response_message["reasoning_content"]
    except KeyError:
        reasoning_reasoning = None

    reasoning_content = response_dump["choices"][0]["message"]["content"]

    return (reasoning_reasoning, reasoning_content), elapsed_time


def LLM_request(prompt, parameter):
    temp_sleep()

    client = OpenAI(api_key=api_key, base_url=base_url)
    for i in range(3):
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
        if parameter["model"] == specify_CoT_model:
            (reasoning_reasoning, curr_response), elapsed_time = CoT_LLM_request(
                prompt, parameter
            )
            # print_c("reasoning_reasoning:", reasoning_reasoning)
        else:
            curr_response, elapsed_time = LLM_request(prompt, parameter)
        if func_valid(curr_response, prompt=prompt):
            return func_clean(curr_response, prompt=prompt), elapsed_time
        print_c("\n--- Wrong response repeat:", i, "---")
        print(curr_response)
        print_c("--------------------------------------")
    print_c(f"Fail-safe: {get_fail_safe}")
    return get_fail_safe, 0
