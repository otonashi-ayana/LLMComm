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
from concurrent.futures import ThreadPoolExecutor

os.system("cls")


class SimulationServer:
    def __init__(self, fork_sim_code, sim_code):
        self.fork_sim_code = fork_sim_code
        self.sim_code = sim_code
        self.server_sleep = 0.5

        self.fork_path = f"{storage_path}/{self.fork_sim_code}"
        self.curr_path = f"{storage_path}/{self.sim_code}"
        copyanything(self.fork_path, self.curr_path)

        init_logger()

        with open(f"{self.curr_path}/meta.json", "r+", encoding="utf-8") as json_file:
            reverie_meta = json.load(json_file)
            reverie_meta["fork_sim_code"] = fork_sim_code  # 更新元数据的code标记
            json_file.seek(0)
            json_file.truncate()
            json.dump(reverie_meta, json_file, indent=2, ensure_ascii=False)

        self.start_time = datetime.datetime.strptime(
            reverie_meta["start_date"], "%B %d, %Y, %H:%M:%S"
        )
        self.curr_time = datetime.datetime.strptime(
            reverie_meta["curr_time"], "%B %d, %Y, %H:%M:%S"
        )
        self.sec_per_step = reverie_meta["sec_per_step"]
        self.maze = Maze()
        self.step = reverie_meta["step"]

        self.personas = dict()  # personas["李华"] = Persona("李华")
        self.personas_cell = dict()  # personas_cell["李华"] = (1, 1)

        init_env_path = f"{self.curr_path}/environment/{self.step}.json"
        init_env = json.load(open(init_env_path, "r", encoding="utf-8"))
        for persona_name in reverie_meta["persona_names"]:
            persona_path = f"{self.curr_path}/personas/{persona_name}"
            p_x = init_env[persona_name]["x"]
            p_y = init_env[persona_name]["y"]

            curr_persona = Persona(persona_name, persona_path)
            self.personas[persona_name] = curr_persona
            self.personas_cell[persona_name] = (p_x, p_y)
            self.maze.cells[p_y][p_x]["events"].add(
                curr_persona.direct_mem.get_curr_event()
            )  # 从加载的persona中恢复direct_mem的event记忆

        # temp_storage_path包含模拟当前的sim_code和当前step，用于传递给前端s
        curr_sim_code = dict()
        curr_sim_code["sim_code"] = self.sim_code
        with open(
            f"{temp_storage_path}/curr_sim_code.json", "w", encoding="utf-8"
        ) as outfile:
            outfile.write(json.dumps(curr_sim_code, indent=2, ensure_ascii=False))

        curr_step = dict()
        curr_step["step"] = self.step
        with open(
            f"{temp_storage_path}/curr_step.json", "w", encoding="utf-8"
        ) as outfile:
            outfile.write(json.dumps(curr_step, indent=2, ensure_ascii=False))

    def start_simulation(self, steps_count):
        obj_clean = dict()
        while True:
            print(
                "当前要计算的时间:",
                self.curr_time.strftime("%B %d, %Y, %H:%M:%S"),
                "当前要运算的step:",
                self.step,
            )
            if steps_count == 0:
                break
            # curr_env_path = f"{self.curr_path}/environment/{self.step}.json" 此处为前端返回的路径
            curr_env_path = f"{self.curr_path}/environment/{self.step}.json"
            if check_if_file_exists(curr_env_path):
                try:
                    with open(curr_env_path, encoding="utf-8") as json_file:
                        new_env = json.load(json_file)
                        env_retrieved = True
                except:
                    pass

                if env_retrieved:
                    # 重置上一轮obj的event
                    for key, val in obj_clean.items():
                        self.maze.turn_event_idle_from_cell(key, val)
                    obj_clean = dict()

                    # 更新personas和maze.cell的相关信息：
                    for persona_name, persona in self.personas.items():
                        # step 1：根据new_env更新personas_cell信息
                        curr_cell = self.personas_cell[persona_name]
                        if (
                            self.maze.get_cell_path(curr_cell, "object").split(":")[-1]
                            == "<小区外部>"
                        ):
                            print(
                                "<start_simulation>当前cell在 <小区外部>,坐标设置为outing_cell"
                            )
                            new_cell = outing_cell
                        else:
                            new_cell = (
                                new_env[persona_name]["x"],
                                new_env[persona_name]["y"],
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

                    with ThreadPoolExecutor(max_workers=len(self.personas)) as executor:
                        future_to_name = {
                            executor.submit(
                                persona.move, self.maze, self.personas, self.curr_time
                            ): persona_name
                            for persona_name, persona in self.personas.items()
                        }
                        for future in future_to_name:
                            persona_name = future_to_name[future]
                            # try:
                            next_cell, desc = future.result()
                            # except Exception as exc:
                            # print(f"{persona_name} 的 move() 发生异常: {exc}")
                            # next_cell, desc = None, ""
                            movements["persona"][persona_name] = {
                                "next_cell": next_cell,
                                "description": desc,
                                "chat_history": self.personas[
                                    persona_name
                                ].direct_mem.chat_history,
                            }
                    movements["curr_time"] = self.curr_time.strftime(
                        "%B %d, %Y, %H:%M:%S"
                    )

                    with open(
                        f"{self.curr_path}/movement/{self.step}.json",
                        "w",
                        encoding="utf-8",
                    ) as json_file:
                        json.dump(movements, json_file, indent=2, ensure_ascii=False)

                    self.curr_time += datetime.timedelta(seconds=self.sec_per_step)
                    self.step += 1  # step最后才增加，以上所有step等于上一次循环的move()所返回的step.json，也就是最新要处理的step batch

                    #### temp for creating environment response ####
                    environments = dict()
                    for persona_name, persona in self.personas.items():
                        environments[persona_name] = {}
                        environments[persona_name]["x"] = movements["persona"][
                            persona_name
                        ]["next_cell"][0]
                        environments[persona_name]["y"] = movements["persona"][
                            persona_name
                        ]["next_cell"][1]
                    with open(
                        f"{self.curr_path}/environment/{self.step}.json",
                        "w",
                        encoding="utf-8",
                    ) as json_file:
                        json.dump(environments, json_file, indent=2, ensure_ascii=False)
                    ###############################################

                    steps_count -= 1
            # time.sleep(self.server_sleep)

    def save(self):
        curr_path = f"{storage_path}/{self.sim_code}"
        # 1.保存模拟meta信息(meta.json)
        reverie_meta = dict()
        reverie_meta["fork_sim_code"] = self.fork_sim_code
        reverie_meta["start_date"] = self.start_time.strftime("%B %d, %Y, %H:%M:%S")
        reverie_meta["curr_time"] = self.curr_time.strftime("%B %d, %Y, %H:%M:%S")
        reverie_meta["sec_per_step"] = self.sec_per_step
        reverie_meta["persona_names"] = list(self.personas.keys())
        reverie_meta["step"] = self.step
        reverie_meta_f = f"{curr_path}/meta.json"
        with open(reverie_meta_f, "w", encoding="utf-8") as outfile:
            outfile.write(json.dumps(reverie_meta, indent=2, ensure_ascii=False))

        # 2.保存persona的direct_m\spatial_m\associate_m
        for persona_name, persona in self.personas.items():
            save_path = f"{curr_path}/personas/{persona_name}"
            persona.save(save_path)

    def start_server(self):
        # count = 0
        while True:
            try:
                # if count == 0:
                #     command = "run 5"
                # else:
                command = input("输入指令:").strip().lower()
                # count += 1
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

    origin = input("输入要加载的模拟记录名称：").strip()
    target = input("输入要新创建的模拟记录名称：").strip()

    # origin = "base_comm"
    # target = "base_comm_1"

    server = SimulationServer(origin, target)
    server.start_server()
