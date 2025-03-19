import sys

sys.path.append("../")
from global_methods import *

from persona.memory_modules.spatial_memory import *
from persona.memory_modules.associate_memory import *
from persona.memory_modules.direct_memory import *
from persona.cognitive_modules.retrieve import *
from persona.cognitive_modules.perceive import *
from persona.prompt_modules.run_prompt import *
import threading

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


def generate_summarize_ideas(persona, nodes, question):
    statements = ""
    for n in nodes:
        statements += f"{n.created} {n.embedding_key}\n"
    summarized_idea = run_prompt_summarize_ideas(persona, statements, question)
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
            prev_convo_minds += f"[内心想法]：{curr_minds[index//2]}\n"

    next_minds = run_prompt_generate_next_minds_line(
        persona, interlocutor_desc, prev_convo_minds, summarized_idea
    )
    return next_minds


def generate_inner_thought(persona, whisper):
    inner_thought = run_prompt_generate_whisper_inner_thought(persona, whisper)
    return inner_thought


def generate_action_event_triple(act_desp, persona):
    return run_prompt_event_triple(act_desp, persona)


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


def open_convo_session(persona, convo_mode):
    if convo_mode == "interview":
        curr_convo = []
        curr_minds = []
        interlocutor_desc = "采访者"

        while True:
            line = input("请输入内容(输入 end 终止访谈): ")
            if line == "end":
                break

            else:
                retrieved = new_retrieve(persona, [line], 70)[line]
                summarized_idea = generate_summarize_ideas(persona, retrieved, line)
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
                        print(f"[内心想法]：{curr_minds[index//2]}")

    elif convo_mode == "whisper":
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
