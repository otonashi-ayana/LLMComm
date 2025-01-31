import sys

sys.path.append("../")
from persona.memory_modules.direct_memory import *
from persona.memory_modules.spatial_memory import *
from persona.cognitive_modules.plan import *
from persona.cognitive_modules.perceive import *


class Persona:
    def __init__(self, name, saved_path):
        self.name = name

        direct_memory_path = f"{saved_path}/direct_memory.json"
        self.direct_mem = DirectMemory(direct_memory_path)

        spatial_memory_path = f"{saved_path}/spatial_memory.json"
        self.spatial_mem = MemoryTree(spatial_memory_path)

    def save(self, saved_path):
        self.direct_mem.save(
            f"{saved_path}/direct_memory.json"
        )  # 调用direct_mem的保存方法，保存到角色的文件夹

    def perceive(self, maze):
        return perceive(self, maze)

    def plan(self, maze, personas, new_day, retrieved):
        return plan(self, maze, personas, new_day, retrieved)

    def move(self, maze, personas, curr_time):
        new_day = False
        if not self.direct_mem.curr_time:
            new_day = "first"
        elif self.direct_mem.curr_time.strftime("%A %B %d") != curr_time.strftime(
            "%A %B %d"
        ):
            new_day = "new"
        # 否则就是同一天内，new_day = False
        self.direct_mem.curr_time = curr_time

        perceived = self.perceive(maze)
        # perceived: a list of <ConceptNode> that are perceived and new.

        # retrieved = self.retrieve(perceived)
        plan = self.plan(maze, personas, new_day, perceived)
        return self.execute(maze, personas, plan)
