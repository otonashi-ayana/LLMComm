"""
定义执行Agent生成模拟的程序入口
"""

import datetime
import json
import traceback
from global_methods import *
from persona.persona import *


class SimulationServer:
    def __init__(self, fork_sim_code, sim_code):
        self.fork_sim_code = fork_sim_code
        self.sim_code = sim_code
        self.server_sleep = 0.05

        self.fork_path = f"{storage_path}/{self.fork_sim_code}"
        self.curr_path = f"{storage_path}/{self.sim_code}"
        copyanything(fork_path, self.curr_path)

        with open(f"{self.curr_path}/meta.json", "r+") as json_file:
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
        self.maze = Maze(reverie_meta["maze"])
        self.step = reverie_meta["step"]

        self.personas = dict()  # ["李华"] = Persona("李华")
        self.personas_cell = dict()  # ["李华"] = (1, 1)
        init_loca_path = f"{self.curr_path}/location/{self.step}.json"
        init_loca = json.load(open(init_loca_path, "r", encoding="utf-8"))
        for persona_name in init_loca["persona"]:
            persona_path = f"{self.curr_path}/personas/{persona_name}"
            p_x = init_loca[persona_name]["x"]
            p_y = init_loca[persona_name]["y"]

            curr_persona = Persona(persona_name,persona_path)
            self.personas[persona_name] = curr_persona
            self.personas_cell[persona_name] = (p_x, p_y)
            self.maze.cells[p_y][p_x]["events"].add(
                #TODO 从角色的direct mem恢复所在cell的event
            )

        # TODO 与前端通信curr_code curr_step

    def start_simulation(self, steps):
        
    def save(self):
        pass
        
    def start_server(self):
        while True:
            command = input("输入指令:").strip().lower()
            try:
                if command[:3] == "run":
                    int_steps = int(command.split()[-1])
                    server.start_simulation(int_steps)
                elif command in ["q","quit"]:
                    shutil.rmtree(self.curr_path)
                    break
                elif command in ["f","finish"]:
                    self.save()
                    break
            except:
                traceback.print_exc()
                print("Error.")
                pass

                


if __name__ == "__main__":

    origin = input("输入要加载的模拟记录名称").strip()
    target = input("输入要新创建的模拟记录名称").strip()

    server = SimulationServer(origin, target)
    server.start_server()
