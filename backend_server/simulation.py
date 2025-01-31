"""
定义执行Agent生成模拟的程序入口
"""

import datetime
import json
import traceback
from global_methods import *
from persona.persona import *
from maze import *
from utils import *
import os
from logger import init_logger

os.system("cls")


class SimulationServer:
    def __init__(self, fork_sim_code, sim_code):
        self.fork_sim_code = fork_sim_code
        self.sim_code = sim_code
        self.server_sleep = 0.05

        self.fork_path = f"{storage_path}/{self.fork_sim_code}"
        self.curr_path = f"{storage_path}/{self.sim_code}"
        copyanything(self.fork_path, self.curr_path)

        init_logger()

        with open(f"{self.curr_path}/meta.json", "r+", encoding="utf-8") as json_file:
            reverie_meta = json.load(json_file)
            reverie_meta["fork_sim_code"] = fork_sim_code  # 更新元数据的code标记
            json_file.seek(0)
            json_file.truncate()
            json.dump(reverie_meta, json_file, indent=2)

        self.start_time = datetime.datetime.strptime(
            reverie_meta["start_date"], "%B %d, %Y, %H:%M:%S"
        )
        self.curr_time = datetime.datetime.strptime(
            reverie_meta["curr_time"], "%B %d, %Y, %H:%M:%S"
        )
        self.sec_per_step = reverie_meta["sec_per_step"]
        self.maze = Maze()
        self.step = reverie_meta["step"]

        self.personas = dict()  # ["李华"] = Persona("李华")
        self.personas_cell = dict()  # ["李华"] = (1, 1)
        init_loca_path = f"{self.curr_path}/location/{self.step}.json"
        init_loca = json.load(open(init_loca_path, "r", encoding="utf-8"))
        for persona_name in reverie_meta["persona_names"]:
            persona_path = f"{self.curr_path}/personas/{persona_name}"
            p_x = init_loca[persona_name]["x"]
            p_y = init_loca[persona_name]["y"]

            curr_persona = Persona(persona_name, persona_path)
            self.personas[persona_name] = curr_persona
            self.personas_cell[persona_name] = (p_x, p_y)
            self.maze.cells[p_y][p_x]["events"].add(
                curr_persona.direct_mem.get_curr_event()
            )  # 从加载的persona中恢复direct_mem的event记忆

        # TODO 与前端通信curr_code curr_step

    def start_simulation(self, steps_count):
        obj_clean = dict()
        while True:
            if steps_count == 0:
                break
            curr_loca_path = f"{self.curr_path}/location/{self.step}.json"
            if check_if_file_exists(curr_loca_path):
                try:
                    with open(curr_loca_path, encoding="utf-8") as json_file:
                        new_loca = json.load(json_file)
                        loca_retrieved = True
                except:
                    pass

                if loca_retrieved:
                    # 重置上一轮obj的event
                    for key, val in obj_clean.items():
                        self.maze.turn_event_idle_from_cell(key, val)
                    obj_clean = dict()

                    # 更新personas和maze.cell的相关信息：
                    for persona_name, persona in self.personas.items():
                        # step 1：根据new_loca更新personas_cell信息
                        curr_cell = self.personas_cell[persona_name]
                        new_cell = (
                            new_loca[persona_name]["x"],
                            new_loca[persona_name]["y"],
                        )
                        self.personas_cell[persona_name] = new_cell
                        # step 2：更新direct_mem的curr_cell
                        self.personas[persona_name].direct_mem.curr_cell = new_cell
                        # step 3：去除旧cell与该persona相关的event，添加到新cell
                        self.maze.remove_subject_event_from_cell(
                            persona.name, curr_cell
                        )
                        self.maze.add_event_to_cell(
                            persona.direct_mem.get_curr_event(), new_cell
                        )
                        # step 4：
                        if not persona.direct_mem.planned_path:
                            obj_clean[persona.direct_mem.get_curr_obj_event] = new_cell
                            # key:event的四元组，value:cell实例
                            self.maze.add_event_to_cell(
                                persona.direct_mem.get_curr_obj_event(), new_cell
                            )

                            blank = (
                                persona.direct_mem.get_curr_obj_event()[0],
                                None,
                                None,
                                None,
                            )
                            self.maze.remove_event_from_cell(blank, new_cell)

                    movements = {"persona": dict(), "curr_time": ""}
                    # 执行move,输出movements
                    for persona_name, persona in self.personas.items():
                        next_cell, desc = persona.move(
                            self.maze,
                            self.personas,
                            # self.personas_cell[persona_name],
                            self.curr_time,
                        )
                        movements["persona"][persona_name] = {}
                        movements["persona"][persona_name]["next_cell"] = next_cell
                        movements["persona"][persona_name]["description"] = desc
                        movements["persona"][persona_name][
                            "chat_history"
                        ] = persona.direct_mem.chat_history
                    movements["curr_time"] = self.curr_time.strftime(
                        "%B %d, %Y, %H:%M:%S"
                    )
                    with open(
                        f"{self.curr_path}/movements/{self.step}.json",
                        "w",
                        encoding="utf-8",
                    ) as json_file:
                        json.dump(movements, json_file, indent=2)

                    self.curr_time += datetime.timedelta(seconds=self.sec_per_step)
                    self.step += 1  # step最后才增加，以上所有step等于上一次循环的move()所返回的step.json，也就是最新要处理的step batch
                    steps_count -= 1
            time.sleep(self.server_sleep)

    def save(self):
        pass

    def start_server(self):
        count = 0
        while True:
            try:
                if count == 0:
                    command = "run 5"
                else:
                    command = input("输入指令:").strip().lower()
                count += 1
                if command[:3] == "run":
                    int_steps = int(command.split()[-1])
                    server.start_simulation(int_steps)
                elif command in ["q", "quit"]:
                    shutil.rmtree(self.curr_path)
                    break
                elif command in ["f", "finish"]:
                    self.save()
                    break
            except:
                traceback.print_exc()
                print("Error.")
                pass


if __name__ == "__main__":

    # origin = input("输入要加载的模拟记录名称").strip()
    # target = input("输入要新创建的模拟记录名称").strip()
    origin = "base_comm"
    target = "base_comm_1"

    server = SimulationServer(origin, target)
    server.start_server()
