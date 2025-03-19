"""
定义执行Agent生成模拟的程序入口
"""

import datetime
import json
import traceback
import time  # 添加导入time模块用于计时
from global_methods import *
from persona.persona import *
from maze import *
from utils import *
import os
import sys  # 添加sys模块用于解析命令行参数
from logger import init_logger
from concurrent.futures import ThreadPoolExecutor
import shutil  # 添加导入shutil模块
import glob  # 添加导入glob模块

os.system("cls")


class SimulationServer:
    def __init__(self, fork_sim_code, sim_code):
        self.fork_sim_code = fork_sim_code
        self.sim_code = sim_code
        # self.server_sleep = 0.5
        self.step_durations = []  # 新增：用于记录每个step的耗时

        self.fork_path = f"{storage_path}/{self.fork_sim_code}"
        self.curr_path = f"{storage_path}/{self.sim_code}"

        # 如果目标目录存在，清除该目录的文件
        if os.path.exists(self.curr_path):
            shutil.rmtree(self.curr_path)
        # 根据optimize_clone参数决定克隆方式
        if optimize_clone:
            # 优化克隆模式，只复制必要文件
            os.makedirs(self.curr_path, exist_ok=True)

            # 复制meta.json
            shutil.copy2(f"{self.fork_path}/meta.json", f"{self.curr_path}/meta.json")

            # 确保目录结构存在
            dirs_to_create = ["environment", "movement", "personas"]
            for dir_name in dirs_to_create:
                os.makedirs(f"{self.curr_path}/{dir_name}", exist_ok=True)

            # 复制personas目录（需要完整复制）
            if os.path.exists(f"{self.fork_path}/personas"):
                shutil.copytree(
                    f"{self.fork_path}/personas",
                    f"{self.curr_path}/personas",
                    dirs_exist_ok=True,
                )

            # 查找并复制environment目录中最新的json文件
            env_files = glob.glob(f"{self.fork_path}/environment/*.json")
            if env_files:
                latest_env_file = max(
                    env_files, key=lambda x: int(os.path.basename(x).split(".")[0])
                )
                shutil.copy2(
                    latest_env_file,
                    f"{self.curr_path}/environment/{os.path.basename(latest_env_file)}",
                )

            # 查找并复制movement目录中最新的json文件
            mov_files = glob.glob(f"{self.fork_path}/movement/*.json")
            if mov_files:
                latest_mov_file = max(
                    mov_files, key=lambda x: int(os.path.basename(x).split(".")[0])
                )
                shutil.copy2(
                    latest_mov_file,
                    f"{self.curr_path}/movement/{os.path.basename(latest_mov_file)}",
                )
        else:
            # 标准模式，完全复制
            copyanything(self.fork_path, self.curr_path)

        init_logger(f"{storage_path}/{sim_code}/output.log")

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
        self.maze.export_map_structure()
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
            if (p_x, p_y) != outing_cell:
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
                "当前要计算的 { 时间:",
                self.curr_time.strftime("%B %d, %Y, %H:%M:%S"),
                "step:",
                self.step,
                "}",
            )
            if steps_count == 0:
                break

            step_start_time = time.time()  # 记录step开始时间

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
                        if self.personas[persona_name].direct_mem.act_address and (
                            self.personas[persona_name].direct_mem.act_address.split(
                                ":"
                            )[-1]
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
                        if curr_cell != outing_cell and new_cell != outing_cell:
                            self.maze.remove_subject_event_from_cell(
                                persona.name, curr_cell
                            )
                            self.maze.add_event_to_cell(
                                persona.direct_mem.get_curr_event(), new_cell
                            )
                            # step 4：
                            if not persona.direct_mem.planned_path:
                                obj_clean[persona.direct_mem.get_curr_obj_event] = (
                                    new_cell
                                )
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

                    # 记录该step的耗时
                    step_end_time = time.time()
                    step_duration = step_end_time - step_start_time
                    self.step_durations.append(step_duration)
            # time.sleep(self.server_sleep)

    def print_timing_statistics(self):
        """计算并打印step耗时统计信息"""
        if not self.step_durations:
            return

        # 计算统计信息
        max_duration = max(self.step_durations)
        min_duration = min(self.step_durations)
        avg_duration = sum(self.step_durations) / len(self.step_durations)

        # 计算95%耗时（排序后的第95百分位数）
        sorted_durations = sorted(self.step_durations)
        percentile_95_index = int(len(sorted_durations) * 0.95)
        percentile_95 = sorted_durations[percentile_95_index]

        # 打印统计信息
        print("\n===== Step耗时统计 =====")
        print(f"总执行step数: {len(self.step_durations)}")
        print(f"最长耗时: {max_duration:.3f}秒")
        print(f"最短耗时: {min_duration:.3f}秒")
        print(f"95%耗时: {percentile_95:.3f}秒")
        print(f"平均耗时: {avg_duration:.3f}秒")
        print("========================")

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

    def start_server(self, auto_run_steps=None):
        # 如果指定了自动运行步数，则直接运行并保存
        if auto_run_steps is not None:
            print(f"自动运行 {auto_run_steps} 步...")
            self.start_simulation(auto_run_steps)
            self.print_timing_statistics()
            self.save()
            return

        # 原有的交互式逻辑
        while True:
            try:
                command = input("输入指令:").strip().lower()
                if command[:3] == "run":
                    int_steps = int(command.split()[-1])
                    server.start_simulation(int_steps)
                elif "secrun" in command:
                    int_secs = int(command.split()[-1])
                    server.start_simulation(int_secs // self.sec_per_step)
                elif "minrun" in command:
                    int_mins = int(command.split()[-1])
                    server.start_simulation(int_mins * 60 // self.sec_per_step)
                elif "hourrun" in command:
                    int_hours = int(command.split()[-1])
                    server.start_simulation(int_hours * 3600 // self.sec_per_step)
                elif command in ["q", "quit"]:
                    # 退出前打印统计信息
                    self.print_timing_statistics()
                    shutil.rmtree(self.curr_path, ignore_errors=True)
                    break
                elif command in ["f", "finish"]:
                    # 结束模拟前打印统计信息
                    self.print_timing_statistics()
                    self.save()
                    break
                elif command in ["m", "maze"]:
                    print(self.maze.cells_of_addr.keys())
                    print(self.maze.cells_of_addr)
                elif "interview" in command:
                    persona_name = command[len("interview") :].strip()
                    self.personas[persona_name].open_convo_session("interview")
                # elif "whisper" in command:
                #     # 单独对某角色进行whisper
                #     # whisper 李华
                #     persona_name = command[len("whisper") :].strip()
                #     self.personas[persona_name].open_convo_session("whisper")
                elif "order" in command:
                    # 单独对某角色进行order
                    # order 李华 张三每天中午都会去公园散步 30
                    args = command[len("order") :].strip().split()
                    persona_name = args[0]
                    order_content = args[1]
                    expired_time = int(args[2])
                    self.personas[persona_name].direct_mem.ordered_minds.append(
                        [
                            self.curr_time.strftime("%A %B %d - %H:%M"),
                            order_content,
                            expired_time,
                        ]
                    )
                elif "action" in command:
                    # 单独对某角色进行action
                    # action 李华 随手扔垃圾到地上 1
                    args = command[len("action") :].strip().split()
                    persona_name = args[0]
                    action_input = args[1]  # 子任务内容
                    action_dur = int(args[2])  # 持续时间（分钟）
                    self.personas[persona_name].direct_mem.specify_action = [
                        action_input,
                        action_dur,
                    ]
                elif "whisper load" in command:
                    # 批量读取whisper csv
                    # whisper load Comm/whisper/agent_history_init_n3.csv
                    curr_file = (
                        maze_assets_loc + "/" + command[len("whisper load") :].strip()
                    )
                    rows = read_file_to_list(curr_file, header=True, strip_trail=True)[
                        1
                    ]
                    clean_whispers = []
                    for row in rows:
                        agent_name = row[0].strip()
                        whispers = row[1].split(";")
                        whispers = [whisper.strip() for whisper in whispers]
                        for whisper in whispers:
                            clean_whispers += [[agent_name, whisper]]

                    load_whisper_csv(self.personas, clean_whispers)
            except:
                traceback.print_exc()
                print("Error.")
                pass


if __name__ == "__main__":
    # 检查命令行参数
    if len(sys.argv) >= 4:
        # 格式: python simulation.py <steps> <origin> <target>
        steps = int(sys.argv[1])
        origin = sys.argv[2]
        target = sys.argv[3]

        server = SimulationServer(origin, target)
        server.start_server(steps)
    else:
        # 原来的交互式逻辑
        origin = input("输入要加载的模拟记录名称：").strip()
        target = input("输入要新创建的模拟记录名称：").strip()

        server = SimulationServer(origin, target)
        server.start_server()
