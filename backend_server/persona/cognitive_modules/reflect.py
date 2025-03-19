import sys

sys.path.append("../../")

import datetime
from global_methods import *
from persona.prompt_modules.run_prompt import *
from persona.prompt_modules.llm_structure import *
from persona.cognitive_modules.retrieve import *
from persona.cognitive_modules.plan import *
from persona.cognitive_modules.perceive import *


def generate_focal_points(persona, n=3):
    nodes = [
        [i.last_accessed, i]
        for i in persona.associate_mem.seq_event + persona.associate_mem.seq_thought
        if "空闲" not in i.embedding_key
    ]

    nodes = sorted(nodes, key=lambda x: x[0])
    nodes = [i for created, i in nodes]

    statements = ""
    for node in nodes[-1 * persona.direct_mem.importance_ele_n :]:
        statements += node.embedding_key + "\n"
    # statements = statements[:30]
    return run_prompt_focal_point(persona, statements, n)


def generate_insights_and_evidence(persona, nodes, n=5):

    statements = ""
    for count, node in enumerate(nodes):
        statements += f"{str(count+1)}. {node.embedding_key}\n"

    ret = run_prompt_insight_guidance(persona, statements, n)

    # try:
    for thought, evi_raw in ret.items():
        evidence_node_id = [nodes[i - 1].node_id for i in evi_raw]
        ret[thought] = evidence_node_id
    return ret
    # except:
    #     return {"this is blank": "node_1"}


def generate_planning_thought_on_convo(persona, all_utt):
    return run_prompt_planning_thought_on_convo(persona, all_utt)


def generate_memo_on_convo(persona, all_utt):
    return run_prompt_memo_on_convo(persona, all_utt)


def run_reflect(persona):
    """
    Run the actual reflection. We generate the focal points, retrieve any
    relevant nodes, and generate thoughts and insights.

    INPUT:
      persona: Current Persona object
    Output:
      None
    """
    # Reflection requires certain focal points. Generate that first.
    focal_points = generate_focal_points(persona, 3)
    # Retrieve the relevant Nodes object for each of the focal points.
    # <retrieved> has keys of focal points, and values of the associated Nodes.
    retrieved = new_retrieve(persona, focal_points)

    # For each of the focal points, generate thoughts and save it in the
    # agent's memory.
    for focal_pt, nodes in retrieved.items():
        xx = [i.embedding_key for i in nodes]
        for xxx in xx:
            print(xxx)

        thoughts = generate_insights_and_evidence(persona, nodes, 5)
        for thought, evidence in thoughts.items():
            created = persona.direct_mem.curr_time
            expiration = persona.direct_mem.curr_time + datetime.timedelta(days=30)
            s, p, o = generate_action_event_triple(thought, persona)
            keywords = set([s, p, o])
            thought_poignancy = generate_poig_score(persona, "thought", thought)
            thought_embedding_pair = (thought, get_embedding(thought))

            persona.associate_mem.add_thought(
                created,
                expiration,
                s,
                p,
                o,
                thought,
                keywords,
                thought_poignancy,
                thought_embedding_pair,
                evidence,
            )


def reflection_trigger(persona):
    """
    Given the current persona, determine whether the persona should run a
    reflection.

    Our current implementation checks for whether the sum of the new importance
    measure has reached the set (hyper-parameter) threshold.

    INPUT:
      persona: Current Persona object
    Output:
      True if we are running a new reflection.
      False otherwise.
    """
    # print(
    #     persona.direct_mem.name,
    #     "persona.direct_mem.importance_trigger_curr:",
    #     persona.direct_mem.importance_trigger_curr,
    # )
    # print(persona.direct_mem.importance_trigger_max)

    if (
        persona.direct_mem.importance_trigger_curr <= 0
        and [] != persona.associate_mem.seq_event + persona.associate_mem.seq_thought
    ):
        return True
    return False


def reset_reflection_counter(persona):
    """
    We reset the counters used for the reflection trigger.

    INPUT:
      persona: Current Persona object
    Output:
      None
    """
    persona_imt_max = persona.direct_mem.importance_trigger_max
    persona.direct_mem.importance_trigger_curr = persona_imt_max
    persona.direct_mem.importance_ele_n = 0


def reflect(persona):
    """
    The main reflection module for the persona. We first check if the trigger
    conditions are met, and if so, run the reflection and reset any of the
    relevant counters.

    INPUT:
      persona: Current Persona object
    Output:
      None
    """
    if reflection_trigger(persona):
        run_reflect(persona)
        reset_reflection_counter(persona)

    # print (persona.direct_mem.name, "al;sdhfjlsad", persona.direct_mem.chatting_end_time)
    if persona.direct_mem.chatting_end_time:
        # print("DEBUG", persona.direct_mem.curr_time + datetime.timedelta(0,10))
        if (
            persona.direct_mem.curr_time + datetime.timedelta(0, 10)
            == persona.direct_mem.chatting_end_time
        ):
            all_utt = ""
            if persona.direct_mem.chat_history:
                for row in persona.direct_mem.chat_history:
                    all_utt += f"{row[0]}: {row[1]}\n"

            # planning_thought = generate_planning_thought_on_convo(persona, all_utt)
            # print ("init planning: aosdhfpaoisdh90m     ::", f"For {persona.direct_mem.name}'s planning: {planning_thought}")
            # planning_thought = generate_planning_thought_on_convo(target_persona, all_utt)
            # print ("target planning: aosdhfpaodish90m     ::", f"For {target_persona.direct_mem.name}'s planning: {planning_thought}")

            # memo_thought = generate_memo_on_convo(persona, all_utt)
            # print ("init memo: aosdhfpaoisdh90m     ::", f"For {persona.direct_mem.name} {memo_thought}")
            # memo_thought = generate_memo_on_convo(target_persona, all_utt)
            # print ("target memo: aosdhfpsaoish90m     ::", f"For {target_persona.direct_mem.name} {memo_thought}")

            # make sure you set the fillings as well

            # print (persona.associate_mem.get_last_chat(persona.direct_mem.chatting_with).node_id)

            evidence = [
                persona.associate_mem.get_last_chat(
                    persona.direct_mem.chatting_with
                ).node_id
            ]
            planning_thought = generate_planning_thought_on_convo(persona, all_utt)
            planning_thought = (
                f"针对 {persona.direct_mem.name} 的计划: {planning_thought}"
            )

            created = persona.direct_mem.curr_time
            expiration = persona.direct_mem.curr_time + datetime.timedelta(days=30)
            s, p, o = generate_action_event_triple(planning_thought, persona)
            keywords = set([s, p, o])
            thought_poignancy = generate_poig_score(
                persona, "thought", planning_thought
            )
            thought_embedding_pair = (planning_thought, get_embedding(planning_thought))

            persona.associate_mem.add_thought(
                created,
                expiration,
                s,
                p,
                o,
                planning_thought,
                keywords,
                thought_poignancy,
                thought_embedding_pair,
                evidence,
            )

            memo_thought = generate_memo_on_convo(persona, all_utt)
            memo_thought = f"{persona.direct_mem.name} {memo_thought}"

            created = persona.direct_mem.curr_time
            expiration = persona.direct_mem.curr_time + datetime.timedelta(days=30)
            s, p, o = generate_action_event_triple(memo_thought, persona)
            keywords = set([s, p, o])
            thought_poignancy = generate_poig_score(persona, "thought", memo_thought)
            thought_embedding_pair = (memo_thought, get_embedding(memo_thought))

            persona.associate_mem.add_thought(
                created,
                expiration,
                s,
                p,
                o,
                memo_thought,
                keywords,
                thought_poignancy,
                thought_embedding_pair,
                evidence,
            )
