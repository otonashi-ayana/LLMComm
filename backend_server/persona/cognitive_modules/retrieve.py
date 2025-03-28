import sys

sys.path.append("../../")

from global_methods import *
from persona.prompt_modules.llm_structure import *

from numpy import dot
from numpy.linalg import norm


def cos_sim(a, b):
    """
    This function calculates the cosine similarity between two input vectors
    'a' and 'b'. Cosine similarity is a measure of similarity between two
    non-zero vectors of an inner product space that measures the cosine
    of the angle between them.

    INPUT:
      a: 1-D array object
      b: 1-D array object
    OUTPUT:
      A scalar value representing the cosine similarity between the input
      vectors 'a' and 'b'.

    Example input:
      a = [0.3, 0.2, 0.5]
      b = [0.2, 0.2, 0.5]
    """
    return dot(a, b) / (norm(a) * norm(b))


def normalize_dict_floats(d, target_min, target_max):
    """
    This function normalizes the float values of a given dictionary 'd' between
    a target minimum and maximum value. The normalization is done by scaling the
    values to the target range while maintaining the same relative proportions
    between the original values.

    INPUT:
      d: Dictionary. The input dictionary whose float values need to be
         normalized.
      target_min: Integer or float. The minimum value to which the original
                  values should be scaled.
      target_max: Integer or float. The maximum value to which the original
                  values should be scaled.
    OUTPUT:
      d: A new dictionary with the same keys as the input but with the float
         values normalized between the target_min and target_max.

    Example input:
      d = {'a':1.2,'b':3.4,'c':5.6,'d':7.8}
      target_min = -5
      target_max = 5
    """
    min_val = min(val for val in d.values())
    max_val = max(val for val in d.values())
    range_val = max_val - min_val

    if range_val == 0:
        for key, val in d.items():
            d[key] = (target_max - target_min) / 2
    else:
        for key, val in d.items():
            d[key] = (val - min_val) * (
                target_max - target_min
            ) / range_val + target_min
    return d


def top_highest_x_values(d, x):
    """
    This function takes a dictionary 'd' and an integer 'x' as input, and
    returns a new dictionary containing the top 'x' key-value pairs from the
    input dictionary 'd' with the highest values.

    INPUT:
      d: Dictionary. The input dictionary from which the top 'x' key-value pairs
         with the highest values are to be extracted.
      x: Integer. The number of top key-value pairs with the highest values to
         be extracted from the input dictionary.
    OUTPUT:
      A new dictionary containing the top 'x' key-value pairs from the input
      dictionary 'd' with the highest values.

    Example input:
      d = {'a':1.2,'b':3.4,'c':5.6,'d':7.8}
      x = 3
    """
    top_v = dict(sorted(d.items(), key=lambda item: item[1], reverse=True)[:x])
    return top_v


def extract_recency(persona, nodes):
    """
    Gets the current Persona object and a list of nodes that are in a
    chronological order, and outputs a dictionary that has the recency score
    calculated.

    INPUT:
      persona: Current persona whose memory we are retrieving.
      nodes: A list of Node object in a chronological order.
    OUTPUT:
      recency_out: A dictionary whose keys are the node.node_id and whose values
                   are the float that represents the recency score.
    """
    recency_vals = [
        persona.direct_mem.recency_decay**i for i in range(1, len(nodes) + 1)
    ]

    recency_out = dict()
    for count, node in enumerate(nodes):
        recency_out[node.node_id] = recency_vals[count]

    return recency_out


def extract_importance(persona, nodes):
    """
    Gets the current Persona object and a list of nodes that are in a
    chronological order, and outputs a dictionary that has the importance score
    calculated.

    INPUT:
      persona: Current persona whose memory we are retrieving.
      nodes: A list of Node object in a chronological order.
    OUTPUT:
      importance_out: A dictionary whose keys are the node.node_id and whose
                      values are the float that represents the importance score.
    """
    importance_out = dict()
    for count, node in enumerate(nodes):
        importance_out[node.node_id] = node.poignancy

    return importance_out


def extract_relevance(persona, nodes, focal_pt):
    """
    获取与焦点文本最相关的节点相关性分数
    """
    focal_embedding = get_embedding(focal_pt)

    relevance_out = dict()
    
    # 对于每个节点，使用Chroma获取向量相似度
    for node in nodes:
        node_embedding = persona.associate_mem.get_embedding(node.node_id)
        if node_embedding:
            relevance_out[node.node_id] = cos_sim(node_embedding, focal_embedding)
        else:
            # 如果无法获取embedding，设置一个低相关性得分
            relevance_out[node.node_id] = 0.0

    return relevance_out


def retrieve(persona, perceived):
    # We rerieve events and thoughts separately.
    retrieved = dict()
    for event in perceived:
        retrieved[event.description] = dict()
        retrieved[event.description]["curr_event"] = event

        relevant_events = persona.associate_mem.retrieve_relevant_events(
            event.subject, event.predicate, event.object
        )
        retrieved[event.description]["events"] = list(relevant_events)

        relevant_thoughts = persona.associate_mem.retrieve_relevant_thoughts(
            event.subject, event.predicate, event.object
        )
        retrieved[event.description]["thoughts"] = list(relevant_thoughts)

    return retrieved


def new_retrieve(persona, focal_points, n_count=10):
    """
    基于焦点文本检索相关记忆节点
    """
    # <retrieved> is the main dictionary that we are returning
    retrieved = dict()
    for focal_pt in focal_points:
        # 使用向量相似度检索一批候选节点
        focal_embedding = get_embedding(focal_pt)
        
        # 获取所有节点
        nodes = [
            [i.last_accessed, i]
            for i in persona.associate_mem.seq_event + persona.associate_mem.seq_thought
            if "空闲" not in i.description
        ]
        nodes = sorted(nodes, key=lambda x: x[0], reverse=True)
        nodes = [i for created, i in nodes]

        # 计算各个组件分数并标准化
        recency_out = extract_recency(persona, nodes)
        recency_out = normalize_dict_floats(recency_out, 0, 1)
        
        importance_out = extract_importance(persona, nodes)
        importance_out = normalize_dict_floats(importance_out, 0, 1)
        
        relevance_out = extract_relevance(persona, nodes, focal_pt)
        relevance_out = normalize_dict_floats(relevance_out, 0, 1)

        # 计算最终得分
        gw = [1, 2, 2]  # 权重： [recency, relevance, importance]
        master_out = dict()
        for key in recency_out.keys():
            master_out[key] = (
                persona.direct_mem.recency_w * recency_out[key] * gw[0]
                + persona.direct_mem.relevance_w * relevance_out[key] * gw[1]
                + persona.direct_mem.importance_w * importance_out[key] * gw[2]
            )

        # 选择最高分的n_count个节点
        master_out = top_highest_x_values(master_out, n_count)
        master_nodes = [
            persona.associate_mem.id_to_node[key] for key in list(master_out.keys())
        ]

        # 更新最后访问时间
        for n in master_nodes:
            n.last_accessed = persona.direct_mem.curr_time

        retrieved[focal_pt] = master_nodes

    return retrieved
