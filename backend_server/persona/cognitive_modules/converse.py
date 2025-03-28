import sys
import traceback

sys.path.append("../")
from global_methods import *
from persona.memory_modules.spatial_memory import *
from persona.memory_modules.associate_memory import *
from persona.memory_modules.direct_memory import *
from persona.cognitive_modules.retrieve import *
from persona.cognitive_modules.perceive import *
from persona.prompt_modules.run_prompt import *
import threading
import concurrent.futures

convo_lock = threading.Lock()

# convo_map: 记录多个对话提案
# key: frozenset({A_name, B_name})
# value: {
#   'status': WAITING | 'IN_PROGRESS' | 'DONE' | 'CANCELLED',
#   'participants': set([A_name, B_name]),
# }
convo_map = {}


def register_convo(persona_name, target_name):
    """在对话管理器中注册一个新的对话提案"""
    pair = frozenset({persona_name, target_name})
    with convo_lock:
        if pair not in convo_map:
            convo_map[pair] = {
                "status": "IN_PROGRESS",
                "participants": set([persona_name, target_name]),
                "cond": threading.Condition(),
            }
        return convo_map[pair]


def update_convo_status_from_map(persona_name, target_name, new_status):
    pair = frozenset({persona_name, target_name})
    with convo_lock:
        if pair in convo_map:
            proposal = convo_map[pair]
            with proposal["cond"]:
                convo_map[pair]["status"] = new_status
                convo_map[pair]["cond"].notify_all()  # 唤醒所有等待线程


def check_participants_form_map(persona):
    with convo_lock:
        for value in convo_map.values():
            if persona in value["participants"]:
                print("<convo_map> existed persona:", persona, value)
                return (value["participants"] - {persona}).pop()
        return False


def wait_until_chat_done(persona_name, target_name):
    pair = frozenset({persona_name, target_name})
    with convo_lock:
        proposal = convo_map[pair]
        cond = proposal["cond"]
    with cond:
        while proposal["status"] != "DONE":
            print(
                f"<wait_until_chat_done> {persona_name} 等待 {target_name} 生成对话中"
            )
            cond.wait()


def remove_convo_from_map(persona_name, target_name):
    """对话完成后，从管理器中移除"""
    pair = frozenset({persona_name, target_name})
    with convo_lock:
        if pair in convo_map:
            del convo_map[pair]


def generate_summarize_agent_relationship(init_persona, target_persona, retrieved):
    description = list()
    for key, val in retrieved.items():
        for i in val:
            if i.predicate == "正在":
                description += [i.description.replace("正在 ", "")]
            else:
                description += [i.description]
    description_str = ""
    for i in description:
        description_str += f"{i}\n"

    summarized_relationship = run_prompt_agent_chat_summarize_relationship(
        init_persona, target_persona, description_str
    )
    return summarized_relationship


def generate_one_utterance(maze, init_persona, target_persona, retrieved, curr_chat):
    # Chat version optimized for speed via batch generation
    curr_context = (
        f"{init_persona.direct_mem.name} "
        + f"正在 {init_persona.direct_mem.act_description}。"
        + f"当 {init_persona.direct_mem.name} "
        + f"看到 {target_persona.direct_mem.name} "
        + f"正在 {target_persona.direct_mem.act_description}时，"
    )
    curr_context += (
        f"{init_persona.direct_mem.name} "
        + f"开始了一段和"
        + f"{target_persona.direct_mem.name}的对话。"
    )

    x = run_generate_iterative_chat_utt(
        maze, init_persona, target_persona, retrieved, curr_context, curr_chat
    )

    return x["utterance"], x["end"]


def agent_chat_v2(maze, init_persona, target_persona):
    curr_chat = []

    for i in range(4):
        # init_persona视角
        focal_points = [f"{target_persona.direct_mem.name}"]
        retrieved = new_retrieve(init_persona, focal_points, 20)
        relationship = generate_summarize_agent_relationship(
            init_persona, target_persona, retrieved
        )
        last_chat = ""
        for i in curr_chat[-4:]:
            last_chat += "： ".join(i) + "\n"
        if last_chat:
            focal_points = [
                f"{relationship}",
                f"{target_persona.direct_mem.name} 正在 {target_persona.direct_mem.act_description}",
                last_chat,
            ]
        else:
            focal_points = [
                f"{relationship}",
                f"{target_persona.direct_mem.name} 正在 {target_persona.direct_mem.act_description}",
            ]
        retrieved = new_retrieve(init_persona, focal_points, 10)
        utt, end = generate_one_utterance(
            maze, init_persona, target_persona, retrieved, curr_chat
        )

        curr_chat += [[init_persona.direct_mem.name, utt]]
        if end:
            break

        # target_persona视角
        focal_points = [f"{init_persona.direct_mem.name}"]
        retrieved = new_retrieve(target_persona, focal_points, 20)
        relationship = generate_summarize_agent_relationship(
            target_persona, init_persona, retrieved
        )
        last_chat = ""
        for i in curr_chat[-4:]:
            last_chat += "： ".join(i) + "\n"
        if last_chat:
            focal_points = [
                f"{relationship}",
                f"{init_persona.direct_mem.name} 正在 {init_persona.direct_mem.act_description}",
                last_chat,
            ]
        else:
            focal_points = [
                f"{relationship}",
                f"{init_persona.direct_mem.name} 正在 {init_persona.direct_mem.act_description}",
            ]
        retrieved = new_retrieve(target_persona, focal_points, 10)
        utt, end = generate_one_utterance(
            maze, target_persona, init_persona, retrieved, curr_chat
        )

        curr_chat += [[target_persona.direct_mem.name, utt]]
        if end:
            break

    print("agent_chat_v2 curr_chat：")
    for row in curr_chat:
        print(row)

    return curr_chat


def generate_summarize_interview_ideas(persona, nodes, question):
    statements = ""
    for n in nodes:
        statements += f"{n.created} {n.embedding_key}\n"
    summarized_idea = run_prompt_summarize_interview_ideas(
        persona, statements, question
    )
    return summarized_idea


def generate_summarize_survey_ideas(persona, nodes, survey_name, question):
    statements = ""
    for n in nodes:
        statements += f"{n.created} {n.embedding_key}\n"
    summarized_idea = run_prompt_summarize_survey_ideas(
        persona, statements, survey_name, question
    )
    return summarized_idea


def generate_next_line(persona, interlocutor_desc, curr_convo, summarized_idea):
    prev_convo = ""
    for row in curr_convo:
        prev_convo += f"{row[0]}: {row[1]}\n"

    next_line = run_prompt_generate_next_convo_line(
        persona, interlocutor_desc, prev_convo, summarized_idea
    )
    return next_line


def generate_next_minds(
    persona, interlocutor_desc, curr_convo, curr_minds, summarized_idea
):
    prev_convo_minds = ""
    for index, row in enumerate(curr_convo):
        prev_convo_minds += f"{row[0]}: {row[1]}\n"
        if index % 2 == 1:
            prev_convo_minds += f"{curr_minds[index//2]}\n"

    next_minds = run_prompt_generate_next_minds_line(
        persona, interlocutor_desc, prev_convo_minds, summarized_idea
    )
    return next_minds


def generate_inner_thought(persona, whisper):
    inner_thought = run_prompt_generate_whisper_inner_thought(persona, whisper)
    return inner_thought


def generate_action_event_triple(act_desp, persona):
    return run_prompt_event_triple(act_desp, persona)


def generate_survey_answer(persona, survey_name, requirement, question):
    retrieved = new_retrieve(persona, [question], 70)[question]
    summarized_idea = generate_summarize_survey_ideas(
        persona, retrieved, survey_name, question
    )
    requirement
    answer = run_prompt_generate_survey_answer(
        persona, summarized_idea, survey_name, requirement, question
    )
    return answer


def load_whisper_csv(personas, whispers):
    for count, row in enumerate(whispers):
        persona = personas[row[0]]
        whisper = row[1]

        thought = generate_inner_thought(persona, whisper)

        created = persona.direct_mem.curr_time
        expiration = persona.direct_mem.curr_time + datetime.timedelta(days=30)
        s, p, o = generate_action_event_triple(thought, persona)
        keywords = set([s, p, o])
        # thought_poignancy = generate_poig_score(persona, "event", whisper)
        thought_embedding_pair = (thought, get_embedding(thought))
        persona.associate_mem.add_thought(
            created,
            expiration,
            s,
            p,
            o,
            thought,
            keywords,
            # thought_poignancy,
            8,
            thought_embedding_pair,
            None,
        )


def open_convo_session(persona, convo_mode, convo_text):
    if convo_mode == "interview":
        curr_convo = []
        curr_minds = []
        interlocutor_desc = "采访者"

        while True:
            if convo_text:
                line = convo_text.pop(0)
            else:
                line = input("请输入内容(输入 end 终止访谈): ")

            if line == "end":
                break

            else:
                retrieved = new_retrieve(persona, [line], 70)[line]
                summarized_idea = generate_summarize_interview_ideas(
                    persona, retrieved, line
                )
                curr_convo += [[interlocutor_desc, line]]

                next_line = generate_next_line(
                    persona, interlocutor_desc, curr_convo, summarized_idea
                )
                next_minds = generate_next_minds(
                    persona, interlocutor_desc, curr_convo, curr_minds, summarized_idea
                )

                curr_convo += [[persona.direct_mem.name, next_line]]
                curr_minds += [next_minds]

                for index, convo in enumerate(curr_convo):
                    print(f"{convo[0]}: {convo[1]}")
                    if index % 2 == 1:
                        print(f"{curr_minds[index//2]}")

    elif convo_mode == "whisper":
        if convo_text:
            whisper = convo_text
        else:
            whisper = input("请输入内容: ")
        thought = generate_inner_thought(persona, whisper)

        created = persona.direct_mem.curr_time
        expiration = persona.direct_mem.curr_time + datetime.timedelta(days=30)
        s, p, o = generate_action_event_triple(thought, persona)
        keywords = set([s, p, o])
        # thought_poignancy = generate_poig_score(persona, "event", whisper)
        # 这里可以把值改高直接定为10
        thought_embedding_pair = (thought, get_embedding(thought))
        persona.associate_mem.add_thought(
            created,
            expiration,
            s,
            p,
            o,
            thought,
            keywords,
            # thought_poignancy,
            8,
            thought_embedding_pair,
            None,
        )


def execute_survey(server, targets, survey_name, requirement, survey_file):
    """
    执行调查功能：从CSV文件读取问题，多线程向目标提问，保存回答
    :param targets: 调查目标列表或群组描述
    :param survey_name: 调查问卷名称
    :param requirement: 回答要求描述
    :param survey_file: 调查问题CSV文件路径
    """
    file_path = survey_file
    if not os.path.exists(file_path):
        print(f"错误：调查文件 {file_path} 不存在")
        return
    questions = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            csv_reader = csv.reader(f)
            for row in csv_reader:
                if row and len(row) > 0:
                    questions.append(row[0])
    except Exception as e:
        print(f"读取CSV文件时出错: {e}")
        traceback.print_exc()
        return
    if not questions:
        print("错误：未找到任何问题")
        return

    was_running = server.pause_simulation.is_set()
    server.pause_simulation.clear()

    try:
        # 创建存储结果的CSV文件
        timestamp = time.strftime("%Y%m%d_%H%M%S", time.localtime())
        result_filename = f"survey_result_{timestamp}.csv"
        survey_result_file = f"{survey_result_path}/{result_filename}"

        # 创建结果文件并写入表头
        with open(survey_result_file, "w", encoding="utf-8", newline="") as f:
            csv_writer = csv.writer(f)
            header = ["问题"] + targets
            csv_writer.writerow(header)

        # 对每个目标进行多线程调查
        def survey_persona(persona_name):
            """对单个角色进行调查的线程函数"""
            results = []
            try:
                for question in questions:
                    try:
                        answer = server.personas[persona_name].generate_survey_answer(
                            survey_name, requirement, question
                        )
                        results.append(answer)
                    except Exception as e:
                        print(f"调查 {persona_name} 问题 '{question}' 时出错: {e}")
                        traceback.print_exc()
                        results.append(f"ERROR: {str(e)}")
                return persona_name, results
            except Exception as e:
                print(f"调查 {persona_name} 时发生未预期错误: {e}")
                traceback.print_exc()
                return persona_name, ["ERROR"] * len(questions)

        # 使用线程池并行调查所有目标
        all_results = {}
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=min(5, len(targets))
        ) as executor:
            futures = {
                executor.submit(survey_persona, target): target for target in targets
            }
            for future in concurrent.futures.as_completed(futures):
                try:
                    persona_name, answers = future.result()
                    all_results[persona_name] = answers
                except Exception as e:
                    target = futures[future]
                    print(f"获取 {target} 的调查结果时出错: {e}")
                    all_results[target] = ["ERROR"] * len(questions)

        # 将所有结果写入CSV文件
        with open(survey_result_file, "w", encoding="utf-8", newline="") as f:
            csv_writer = csv.writer(f)
            # 写入表头
            header = ["问题"] + targets
            csv_writer.writerow(header)

            # 写入每个问题和所有人的回答
            for i, question in enumerate(questions):
                row = [question]
                for target in targets:
                    if target in all_results and i < len(all_results[target]):
                        row.append(all_results[target][i])
                    else:
                        row.append("")
                csv_writer.writerow(row)

        print(f"调查完成，结果已保存到：{survey_result_file}")

    except Exception as e:
        print(f"执行调查时出错: {e}")
        traceback.print_exc()
    finally:
        if was_running:
            server.pause_simulation.set()
