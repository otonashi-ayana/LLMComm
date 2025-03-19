import sys

sys.path.append("../")
from persona.memory_modules.direct_memory import *
from persona.memory_modules.spatial_memory import *
from persona.cognitive_modules.plan import *
from persona.cognitive_modules.perceive import *
from persona.cognitive_modules.retrieve import *
from persona.cognitive_modules.execute import *
from persona.cognitive_modules.reflect import *
from persona.cognitive_modules.converse import *
from maze import *


class Persona:
    def __init__(self, name, saved_path):
        self.name = name

        direct_memory_path = f"{saved_path}/direct_memory.json"
        self.direct_mem = DirectMemory(direct_memory_path)

        spatial_memory_path = f"{saved_path}/spatial_memory.json"
        self.spatial_mem = MemoryTree(spatial_memory_path)

        associate_memory_path = f"{saved_path}/associative_memory"
        self.associate_mem = AssociativeMemory(associate_memory_path)

    def save(self, saved_path):
        self.direct_mem.save(f"{saved_path}/direct_memory.json")
        self.spatial_mem.save(f"{saved_path}/spatial_memory.json")
        self.associate_mem.save(f"{saved_path}/associative_memory")

    def perceive(self, maze):
        return perceive(self, maze)

    def retrieve(self, perceived):
        return retrieve(self, perceived)

    def plan(self, maze, personas, new_day, retrieved):
        return plan(self, maze, personas, new_day, retrieved)

    def reflect(self):
        reflect(self)

    def execute(self, maze, personas, plan):
        return execute(self, maze, personas, plan)

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
        if self.direct_mem.curr_cell == outing_cell:
            # 如果当前cell是小区外部
            print(
                f"<move> 当前cell在outing_cell,act_description:{self.direct_mem.act_description}"
            )

            if (
                self.direct_mem.act_check_finished()
            ):  # 如果当前动作已经完成(则进行新的规划，不perceive和retrieve)
                self.direct_mem.curr_cell = backing_cell
                print("<move> 已经返回小区,恢复到backing_cell")
                plan = self.plan(maze, personas, new_day, retrieved=dict())
                self.reflect()
                return self.execute(maze, personas, plan)

            print("<move> 尚未返回小区")

            execution = (
                self.direct_mem.curr_cell,
                f"在 <小区外部>，{self.direct_mem.act_description}",
            )
            self.reflect()
            return execution
        perceived = self.perceive(maze)
        retrieved = self.retrieve(perceived)
        plan = self.plan(maze, personas, new_day, retrieved)
        self.reflect()
        return self.execute(maze, personas, plan)

    def open_convo_session(self, convo_mode):
        open_convo_session(self, convo_mode)
