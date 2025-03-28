import sys
import datetime
import os
import json
import chromadb
from chromadb.config import Settings
from pypinyin import lazy_pinyin
from functools import lru_cache
import time

sys.path.append("../../")
from global_methods import *

# 全局ChromaDB客户端单例
_chroma_client = None


def get_chroma_client(chromadb_path):
    """获取或创建全局ChromaDB客户端单例"""
    global _chroma_client
    if _chroma_client is None:
        # 确保存储目录存在
        persist_dir = chromadb_path
        os.makedirs(persist_dir, exist_ok=True)

        _chroma_client = chromadb.Client(
            Settings(persist_directory=persist_dir, allow_reset=True)
        )
    return _chroma_client


class ConceptNode:
    def __init__(
        self,
        node_id,
        node_count,
        type_count,
        node_type,
        depth,
        created,
        expiration,
        s,
        p,
        o,
        description,
        embedding_key,
        poignancy,
        keywords,
        filling,
    ):
        self.node_id = node_id
        self.node_count = node_count
        self.type_count = type_count
        self.type = node_type  # thought / event / chat
        self.depth = depth

        self.created = created
        self.expiration = expiration
        self.last_accessed = self.created

        self.subject = s
        self.predicate = p
        self.object = o

        self.description = description
        self.embedding_key = embedding_key
        self.poignancy = poignancy
        self.keywords = keywords
        self.filling = filling

    def spo_summary(self):
        return (self.subject, self.predicate, self.object)

    def to_dict(self):
        """将节点转换为字典，用于Chroma存储"""
        return {
            "node_id": self.node_id,
            "node_count": self.node_count,
            "type_count": self.type_count,
            "type": self.type,
            "depth": self.depth,
            "created": self.created.strftime("%Y-%m-%d %H:%M:%S"),
            "expiration": (
                self.expiration.strftime("%Y-%m-%d %H:%M:%S")
                if self.expiration
                else None
            ),
            "subject": self.subject,
            "predicate": self.predicate,
            "object": self.object,
            "description": self.description,
            "embedding_key": self.embedding_key,
            "poignancy": self.poignancy,
            "keywords": list(self.keywords),
            "filling": self.filling,
        }


class AssociativeMemory:
    def __init__(self, f_saved, persona_name, sim_path):
        # self.persist_dir = f_saved
        self.id_to_node = {}

        chromadb_path = f"{sim_path}/personas"
        # 提取角色名称作为集合名称前缀

        # 节点序列，按类型分类
        self.seq_event = []
        self.seq_thought = []
        self.seq_chat = []

        # 关键词到节点的映射
        self.kw_to_event = {}
        self.kw_to_thought = {}
        self.kw_to_chat = {}

        # 关键词强度统计
        self.kw_strength_event = {}
        self.kw_strength_thought = {}

        # 向量嵌入缓存 - 使用字典存储文本到向量的映射
        self.embeddings = {}

        # 确保存储目录存在
        os.makedirs(f_saved, exist_ok=True)

        # 使用共享的Chroma客户端
        self.chroma_client = get_chroma_client(chromadb_path)

        pinyin_name = "_".join(lazy_pinyin(persona_name))
        self.collection_name = f"memory_nodes_{pinyin_name}"

        # 创建或获取节点集合
        self.node_collection = self._initialize_collection()

        # 加载已有向量到缓存
        self._load_embeddings_to_cache()

        # 加载所有节点
        self._load_nodes_from_chroma()

    def _initialize_collection(self):
        """初始化Chroma集合并设置索引参数"""
        try:
            return self.chroma_client.get_collection(self.collection_name)
        except Exception:
            return self.chroma_client.create_collection(
                name=self.collection_name,
                metadata={
                    "hnsw:space": "cosine",
                },
            )

    @lru_cache(maxsize=1000)
    def get_cached_embedding(self, text):
        """获取缓存的向量表示，限制缓存大小"""
        return self.get_embedding_for_text(text)

    # def batch_add_nodes(self, nodes, embeddings):
    #     """批量添加节点到Chroma集合"""
    #     ids = [node.node_id for node in nodes]
    #     metadatas = [node.to_dict() for node in nodes]
    #     documents = [node.description for node in nodes]
    #     try:
    #         self.node_collection.add(
    #             ids=ids, embeddings=embeddings, metadatas=metadatas, documents=documents
    #         )
    #     except Exception as e:
    #         print(f"批量添加节点时出错: {e}")

    def clean_expired_nodes(self):
        """清理过期节点"""
        now = datetime.datetime.now()
        expired_ids = []
        for node in self.id_to_node.values():
            if node.expiration and node.expiration < now:
                expired_ids.append(node.node_id)
        if expired_ids:
            try:
                self.node_collection.delete(ids=expired_ids)
                for node_id in expired_ids:
                    del self.id_to_node[node_id]
                print(f"清理了{len(expired_ids)}个过期节点")
            except Exception as e:
                print(f"清理过期节点时出错: {e}")

    def timed_operation(operation_name):
        """性能监控装饰器"""

        def decorator(func):
            def wrapper(*args, **kwargs):
                start = time.time()
                result = func(*args, **kwargs)
                print(f"{operation_name}耗时: {time.time() - start:.3f}秒")
                return result

            return wrapper

        return decorator

    def _load_embeddings_to_cache(self):
        """从Chroma加载已有向量到缓存"""
        try:
            # 获取所有条目
            result = self.node_collection.get(include=["metadatas", "embeddings"])

            # 如果数据库为空，直接返回
            if not result["ids"]:
                return

            # 加载向量到缓存
            for i, metadata in enumerate(result["metadatas"]):
                embedding_key = metadata.get("embedding_key")
                if embedding_key and embedding_key not in self.embeddings:
                    self.embeddings[embedding_key] = result["embeddings"][i]
        except Exception as e:
            print(f"加载向量到缓存时出错: {e}")

    @timed_operation("加载节点")
    def _load_nodes_from_chroma(self):
        """从Chroma加载所有节点数据"""
        result = self.node_collection.get(
            include=["metadatas", "documents", "embeddings"]
        )

        # 如果数据库为空，直接返回
        if not result["ids"]:
            return

        # 恢复节点对象
        for i, node_id in enumerate(result["ids"]):
            metadata = result["metadatas"][i]
            embedding = result["embeddings"][i]

            # 从元数据恢复节点属性
            node_count = metadata.get("node_count")
            type_count = metadata.get("type_count")
            node_type = metadata.get("type")
            depth = metadata.get("depth")

            created = datetime.datetime.strptime(
                metadata.get("created"), "%Y-%m-%d %H:%M:%S"
            )

            expiration = None
            if metadata.get("expiration"):
                expiration = datetime.datetime.strptime(
                    metadata.get("expiration"), "%Y-%m-%d %H:%M:%S"
                )

            s = metadata.get("subject")
            p = metadata.get("predicate")
            o = metadata.get("object")
            description = metadata.get("description")
            embedding_key = metadata.get("embedding_key", node_id)
            poignancy = metadata.get("poignancy", 0.5)
            keywords = set(json.loads(metadata.get("keywords", "[]")))
            filling = json.loads(metadata.get("filling", []))

            # 创建节点对象
            node = ConceptNode(
                node_id,
                node_count,
                type_count,
                node_type,
                depth,
                created,
                expiration,
                s,
                p,
                o,
                description,
                embedding_key,
                poignancy,
                keywords,
                filling,
            )

            # 添加到适当的集合
            if node_type == "event":
                self.seq_event.append(node)
                for kw in keywords:
                    if kw in self.kw_to_event:
                        self.kw_to_event[kw].append(node)
                    else:
                        self.kw_to_event[kw] = [node]
                if f"{p} {o}" != "正在 空闲":
                    for kw in keywords:
                        if kw in self.kw_strength_event:
                            self.kw_strength_event[kw] += 1
                        else:
                            self.kw_strength_event[kw] = 1
            elif node_type == "thought":
                self.seq_thought.append(node)
                for kw in keywords:
                    if kw in self.kw_to_thought:
                        self.kw_to_thought[kw].append(node)
                    else:
                        self.kw_to_thought[kw] = [node]
                if f"{p} {o}" != "正在 空闲":
                    for kw in keywords:
                        if kw in self.kw_strength_thought:
                            self.kw_strength_thought[kw] += 1
                        else:
                            self.kw_strength_thought[kw] = 1
            elif node_type == "chat":
                self.seq_chat.append(node)
                for kw in keywords:
                    if kw in self.kw_to_chat:
                        self.kw_to_chat[kw].append(node)
                    else:
                        self.kw_to_chat[kw] = [node]

            # 添加到ID查找字典
            self.id_to_node[node_id] = node

        # 对各序列按照创建时间排序（最新的在前）
        self.seq_event.sort(key=lambda x: x.created, reverse=True)
        self.seq_thought.sort(key=lambda x: x.created, reverse=True)
        self.seq_chat.sort(key=lambda x: x.created, reverse=True)

    def save(self, out_dir):
        """保存内存状态到共享的Chroma数据库"""
        # 确保输出目录存在
        os.makedirs(out_dir, exist_ok=True)

        # Chroma数据库已经通过persist_directory自动持久化
        # 只需保存关键词强度统计，因为它不是向量数据
        kw_strength = {
            "kw_strength_event": self.kw_strength_event,
            "kw_strength_thought": self.kw_strength_thought,
        }

        with open(f"{out_dir}/kw_strength.json", "w", encoding="utf-8") as outfile:
            json.dump(kw_strength, outfile, ensure_ascii=False, indent=2)

    def add_event(
        self,
        created,
        expiration,
        s,
        p,
        o,
        description,
        keywords,
        poignancy,
        embedding_pair,
        filling,
    ):
        # 获取节点ID和计数
        node_count = len(self.id_to_node.keys()) + 1
        type_count = len(self.seq_event) + 1
        node_type = "event"
        node_id = f"node_{str(node_count)}"
        depth = 0

        # 特定节点类型的清理
        if "（" in description:
            description = (
                " ".join(description.split()[:2])
                + " "
                + description.split("（")[-1][:-1]
            )

        # 创建节点对象
        node = ConceptNode(
            node_id,
            node_count,
            type_count,
            node_type,
            depth,
            created,
            expiration,
            s,
            p,
            o,
            description,
            embedding_pair[0],
            poignancy,
            keywords,
            filling,
        )

        # 更新各种集合
        self.seq_event.insert(0, node)
        keywords_list = list(keywords)
        for kw in keywords_list:
            if kw in self.kw_to_event:
                self.kw_to_event[kw].insert(0, node)
            else:
                self.kw_to_event[kw] = [node]
        self.id_to_node[node_id] = node

        # 更新关键词强度
        if f"{p} {o}" != "正在 空闲":
            for kw in keywords_list:
                if kw in self.kw_strength_event:
                    self.kw_strength_event[kw] += 1
                else:
                    self.kw_strength_event[kw] = 1

        # 添加到Chroma
        self._add_node_to_chroma(node, embedding_pair[1])

        # 同时添加到缓存
        self.embeddings[embedding_pair[0]] = embedding_pair[1]

        return node

    def add_thought(
        self,
        created,
        expiration,
        s,
        p,
        o,
        description,
        keywords,
        poignancy,
        embedding_pair,
        filling,
    ):
        # 获取节点ID和计数
        node_count = len(self.id_to_node.keys()) + 1
        type_count = len(self.seq_thought) + 1
        node_type = "thought"
        node_id = f"node_{str(node_count)}"
        depth = 1
        try:
            if filling:
                depth += max([self.id_to_node[i].depth for i in filling])
        except:
            pass

        # 创建节点对象
        node = ConceptNode(
            node_id,
            node_count,
            type_count,
            node_type,
            depth,
            created,
            expiration,
            s,
            p,
            o,
            description,
            embedding_pair[0],
            poignancy,
            keywords,
            filling,
        )

        # 更新各种集合
        self.seq_thought.insert(0, node)
        keywords_list = list(keywords)
        for kw in keywords_list:
            if kw in self.kw_to_thought:
                self.kw_to_thought[kw].insert(0, node)
            else:
                self.kw_to_thought[kw] = [node]
        self.id_to_node[node_id] = node

        # 更新关键词强度
        if f"{p} {o}" != "正在 空闲":
            for kw in keywords_list:
                if kw in self.kw_strength_thought:
                    self.kw_strength_thought[kw] += 1
                else:
                    self.kw_strength_thought[kw] = 1

        # 添加到Chroma
        self._add_node_to_chroma(node, embedding_pair[1])

        # 同时添加到缓存
        self.embeddings[embedding_pair[0]] = embedding_pair[1]

        return node

    def add_chat(
        self,
        created,
        expiration,
        s,
        p,
        o,
        description,
        keywords,
        poignancy,
        embedding_pair,
        filling,
    ):
        # 获取节点ID和计数
        node_count = len(self.id_to_node.keys()) + 1
        type_count = len(self.seq_chat) + 1
        node_type = "chat"
        node_id = f"node_{str(node_count)}"
        depth = 0

        # 创建节点对象
        node = ConceptNode(
            node_id,
            node_count,
            type_count,
            node_type,
            depth,
            created,
            expiration,
            s,
            p,
            o,
            description,
            embedding_pair[0],
            poignancy,
            keywords,
            filling,
        )

        # 更新各种集合
        self.seq_chat.insert(0, node)
        keywords_list = list(keywords)
        for kw in keywords_list:
            if kw in self.kw_to_chat:
                self.kw_to_chat[kw].insert(0, node)
            else:
                self.kw_to_chat[kw] = [node]
        self.id_to_node[node_id] = node

        # 添加到Chroma
        self._add_node_to_chroma(node, embedding_pair[1])

        # 同时添加到缓存
        self.embeddings[embedding_pair[0]] = embedding_pair[1]

        return node

    @timed_operation("添加节点到Chroma")
    def _add_node_to_chroma(self, node, embedding):
        """将节点添加到Chroma集合"""
        # 准备节点元数据
        metadata = {
            "node_count": node.node_count,
            "type_count": node.type_count,
            "type": node.type,
            "depth": node.depth,
            "created": node.created.strftime("%Y-%m-%d %H:%M:%S"),
            "expiration": (
                node.expiration.strftime("%Y-%m-%d %H:%M:%S")
                if node.expiration
                else ""  # 使用空字符串代替None
            ),
            "subject": node.subject or "",  # 确保不为None
            "predicate": node.predicate or "",  # 确保不为None
            "object": node.object or "",  # 确保不为None
            "description": node.description or "",  # 确保不为None
            "embedding_key": node.embedding_key or "",  # 确保不为None
            "poignancy": node.poignancy or 0.0,  # 确保不为None
            "keywords": (
                str(list(node.keywords)) if node.keywords else "[]"
            ),  # 确保不为None
            "filling": str(node.filling) if node.filling else "[]",  # 确保不为None
        }

        # 添加到Chroma
        try:
            self.node_collection.add(
                ids=[node.node_id],
                embeddings=[embedding],
                metadatas=[metadata],
                documents=[node.description or ""],  # 确保描述不为None
            )
        except Exception as e:
            print(f"Error adding node to Chroma: {e}")

    def get_embedding(self, node_id):
        """获取节点的向量表示"""
        result = self.node_collection.get(ids=[node_id], include=["embeddings"])

        if result and result["embeddings"] and len(result["embeddings"]) > 0:
            return result["embeddings"][0]
        return None

    def retrieve_similar_nodes(self, query_embedding, n_results=5, filter_type=None):
        """检索与查询向量最相似的节点"""
        # 设置过滤条件（可选）
        where_filter = None
        if filter_type:
            where_filter = {"type": filter_type}

        # 执行相似度查询
        results = self.node_collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where_filter,
            include=["metadatas", "documents", "distances"],
        )

        # 返回节点ID和相似度分数
        node_ids = results["ids"][0]
        similarities = [
            1.0 - dist for dist in results["distances"][0]
        ]  # 距离转换为相似度

        return list(zip(node_ids, similarities))

    def get_summarized_latest_events(self, retention):
        ret_set = set()
        for e_node in self.seq_event[:retention]:
            ret_set.add(e_node.spo_summary())
        return ret_set

    def retrieve_relevant_thoughts(self, s_content, p_content, o_content):
        contents = [s_content, p_content, o_content]

        ret = []
        for i in contents:
            if i in self.kw_to_thought:
                ret += self.kw_to_thought[i]
        ret = set(ret)
        return ret

    def retrieve_relevant_events(self, s_content, p_content, o_content):
        contents = [s_content, p_content, o_content]

        ret = []
        for i in contents:
            if i in self.kw_to_event:
                ret += self.kw_to_event[i]
        ret = set(ret)
        return ret

    def get_last_chat(self, target_persona_name):
        if target_persona_name in self.kw_to_chat:
            return self.kw_to_chat[target_persona_name][0]
        else:
            return False

    def get_embedding_for_text(self, text):
        """根据文本获取向量表示，先查缓存，没有再从ChromaDB查询"""
        if text in self.embeddings:
            return self.embeddings[text]

        # 尝试从ChromaDB查询
        try:
            # 使用文本作为查询条件查找可能匹配的文档
            results = self.node_collection.query(
                query_texts=[text], n_results=1, include=["metadatas", "embeddings"]
            )

            if results["distances"][0] and results["distances"][0][0] < 0.1:
                # 如果距离很小，表示找到了几乎相同的文本
                embedding = results["embeddings"][0][0]
                # 添加到缓存
                self.embeddings[text] = embedding
                return embedding
        except Exception as e:
            print(f"从ChromaDB查询向量时出错: {e}")

        # 如果没有找到匹配的向量，返回None
        return None
