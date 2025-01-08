"""
定义运行prompt的所有函数
"""


def run_prompt_wake_up_time(persona):
    """
    返回给定persona的起床时间(integer)
    """

    def create_prompt_args(persona):
        prompt_args = [persona.scratch.get_str_mds()]
        return prompt_args

    prompt_file_path = "persona/prompt_modules/templates/wake_up_time_v1.txt"
    prompt_args = create_prompt_args(persona)
    prompt = generate_prompt(prompt_file_path, prompt_args)
    output = prompt  # TODO 添加结果检查
    if debug:
        # TODO 输出prompt、prompt_args等
        pass
    return output


def generate_prompt(prompt_file_path, prompt_args):
    if type(prompt_args) == str:
        prompt_args = [prompt_args]
    prompt_args = [str(arg) for arg in prompt_args]

    f = open(prompt_file_path, "r", encoding="utf-8")
    prompt = f.read()
    f.close()
    for count, arg in enumerate(prompt_args):
        prompt = prompt.replace(f"#<INPUT {count}>#", arg)
    if "<BLOCK></BLOCK>" in prompt:
        prompt = prompt.split("<BLOCK></BLOCK>")[1]
    return prompt.strip()
