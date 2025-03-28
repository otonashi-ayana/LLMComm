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
import queue  # 添加队列模块
import threading  # 添加线程模块
import subprocess  # 添加子进程模块
import win32pipe, win32file  # 添加Windows管道通信模块
import time
import argparse  # 添加用于解析命令行参数

os.system("cls")

# 定义命名管道名称
PIPE_NAME = r"\\.\pipe\simulation_command_pipe"


class SimulationServer:
    def __init__(self, fork_sim_code, sim_code, sec_per_step=None):
        self.fork_sim_code = fork_sim_code
        self.sim_code = sim_code
        # self.server_sleep = 0.5
        self.step_durations = []  # 新增：用于记录每个step的耗时

        # 添加命令队列和控制标志
        self.command_queue = queue.Queue()
        self.is_running = False
        self.pause_simulation = threading.Event()
        self.pause_simulation.set()  # 初始状态为不暂停
        self.in_conversation = False

        # 命令窗口进程
        self.command_process = None
        # 命名管道通信
        self.pipe = None

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
            # 如果指定了sec_per_step，则更新meta.json中的值
            if sec_per_step is not None:
                reverie_meta["sec_per_step"] = int(sec_per_step)
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
        self.maze = Maze(self.fork_sim_code, self.sim_code)
        self.maze.export_map_structure()
        self.step = reverie_meta["step"]

        self.personas = dict()  # personas["李华"] = Persona("李华")
        self.personas_cell = dict()  # personas_cell["李华"] = (1, 1)

        init_env_path = f"{self.curr_path}/environment/{self.step}.json"
        init_env = json.load(open(init_env_path, "r", encoding="utf-8"))
        for persona_name in reverie_meta["persona_names"]:
            # persona_path = f"{self.curr_path}/personas/{persona_name}"
            p_x = init_env[persona_name]["x"]
            p_y = init_env[persona_name]["y"]

            curr_persona = Persona(persona_name, self.curr_path)
            self.personas[persona_name] = curr_persona
            self.personas_cell[persona_name] = (p_x, p_y)
            if (p_x, p_y) != outing_cell:
                self.maze.cells[p_y][p_x]["events"].add(
                    curr_persona.direct_mem.get_curr_event()
                )  # 从加载的persona中恢复direct_mem的event记忆

        # temp_storage_path包含模拟当前的sim_code和当前step，用于传递给前端
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

    # 添加处理命令的方法
    def process_command(self, command):
        """处理命令队列中的命令"""
        try:
            print(f"\n处理命令: {command}")
            if "interview" in command:
                persona_name = command[len("interview") :].strip()
                # 暂停模拟
                was_running = self.pause_simulation.is_set()
                self.pause_simulation.clear()
                print(f"模拟暂停，正在与 {persona_name} 进行interview...")
                self.in_conversation = True
                self.personas[persona_name].open_convo_session("interview")
                print("interview结束，继续模拟...")
                self.in_conversation = False
                if was_running:
                    self.pause_simulation.set()
            elif "whisper" in command and "load" not in command:
                persona_name = command[len("whisper") :].strip()
                # 暂停模拟
                was_running = self.pause_simulation.is_set()
                self.pause_simulation.clear()
                print(f"模拟暂停，正在对 {persona_name} 进行whisper...")
                self.in_conversation = True
                self.personas[persona_name].open_convo_session("whisper")
                self.in_conversation = False
                print("whisper结束，继续模拟...")
                if was_running:
                    self.pause_simulation.set()
            elif "order" in command:
                args = command[len("order") :].strip().split()
                persona_name = args[0]
                order_content = " ".join(args[1:-1])  # 中间部分作为内容
                expired_time = int(args[-1])
                self.personas[persona_name].direct_mem.ordered_minds.append(
                    [
                        self.curr_time.strftime("%A %B %d - %H:%M"),
                        order_content,
                        expired_time,
                    ]
                )
                print(
                    f"已对 {persona_name} 下达指令: {order_content}，有效时间: {expired_time}"
                )
            elif "action" in command:
                args = command[len("action") :].strip().split()
                persona_name = args[0]
                action_input = " ".join(args[1:-1])  # 中间部分作为内容
                action_dur = int(args[-1])
                self.personas[persona_name].direct_mem.specify_action = [
                    action_input,
                    action_dur,
                ]
                print(
                    f"已为 {persona_name} 指定动作: {action_input}，持续时间: {action_dur}"
                )
            elif "whisper load" in command:
                curr_file = command[len("whisper load") :].strip()
                was_running = self.pause_simulation.is_set()
                self.pause_simulation.clear()
                print(f"模拟暂停，正在加载whisper文件...")
                rows = read_file_to_list(curr_file, header=True, strip_trail=True)[1]
                clean_whispers = []
                for row in rows:
                    agent_name = row[0].strip()
                    whispers = row[1].split(";")
                    whispers = [whisper.strip() for whisper in whispers]
                    for whisper in whispers:
                        clean_whispers += [[agent_name, whisper]]
                load_whisper_csv(self.personas, clean_whispers)
                print("whisper加载完成，继续模拟...")
                if was_running:
                    self.pause_simulation.set()
        except Exception as e:
            print(f"处理命令时出错: {e}")
            traceback.print_exc()
            # 确保处理错误后继续运行
            self.pause_simulation.set()

    # 重构命令窗口启动和监听逻辑
    def create_command_pipe(self):
        """创建命令通信管道"""
        try:
            # 创建命名管道
            print("正在创建命令通信管道...")
            self.pipe = win32pipe.CreateNamedPipe(
                PIPE_NAME,
                win32pipe.PIPE_ACCESS_INBOUND,
                win32pipe.PIPE_TYPE_MESSAGE
                | win32pipe.PIPE_READMODE_MESSAGE
                | win32pipe.PIPE_WAIT,
                1,
                65536,
                65536,
                0,
                None,
            )
            return True
        except Exception as e:
            print(f"创建命令通信管道失败: {e}")
            traceback.print_exc()
            return False

    def start_command_window(self):
        """启动单独的命令输入窗口"""
        try:
            # 启动命令输入进程
            script_dir = os.path.dirname(os.path.abspath(__file__))
            command_script = os.path.join(script_dir, "command_input.py")

            # 确保命令脚本存在
            if not os.path.exists(command_script):
                with open(command_script, "w", encoding="utf-8") as f:
                    f.write(
                        """
# 命令输入窗口
import sys
import win32pipe, win32file
import os

PIPE_NAME = r'\\.\pipe\\simulation_command_pipe'

def main():
    os.system("cls")
    print("========= 模拟命令输入窗口 =========")
    print("常用命令：")
    print("  pause - 暂停模拟")
    print("  resume - 继续模拟")
    print("  save - 保存当前模拟状态")
    print("  save <名称> - 保存到指定名称")
    print("  quit/q - 停止模拟")
    print("  interview <角色名> - 与角色对话")
    print("  whisper <角色名> - 对角色进行whisper")
    print("====================================")
    
    # 连接到命名管道
    try:
        pipe = win32file.CreateFile(
            PIPE_NAME,
            win32file.GENERIC_WRITE,
            0, None,
            win32file.OPEN_EXISTING,
            0, None
        )
        
        while True:
            command = input(">> ").strip()
            if not command:
                continue
                
            # 发送命令到模拟进程
            win32file.WriteFile(pipe, command.encode('utf-8'))
            
            if command.lower() in ["q", "quit"]:
                print("命令窗口关闭中...")
                break
                
    except Exception as e:
        print(f"错误: {e}")
    finally:
        try:
            win32file.CloseHandle(pipe)
        except:
            pass
        
if __name__ == "__main__":
    main()
"""
                    )

            # 使用subprocess启动新的命令窗口
            print("正在启动命令输入窗口...")
            self.command_process = subprocess.Popen(
                ["start", "python", command_script],
                shell=True,
                creationflags=subprocess.CREATE_NEW_CONSOLE,
            )

            # 等待客户端连接到管道
            win32pipe.ConnectNamedPipe(self.pipe, None)
            print("命令窗口已连接，可以在命令窗口中输入命令")

            return True
        except Exception as e:
            print(f"启动命令窗口失败: {e}")
            traceback.print_exc()
            return False

    def start_command_listener(self):
        """启动命令监听线程"""
        # 创建管道
        if not self.create_command_pipe():
            return False

        # 启动命令窗口
        if not self.start_command_window():
            return False

        # 标记为运行状态
        self.is_running = True

        # 启动线程监听管道命令
        self.pipe_thread = threading.Thread(target=self.listen_pipe_commands)
        self.pipe_thread.daemon = True
        self.pipe_thread.start()

        return True

    def stop_command_listener(self):
        """停止命令监听"""
        print("正在停止命令监听...")
        self.is_running = False

        # 关闭管道
        try:
            if self.pipe:
                # 使用DisconnectNamedPipe来避免ReadFile阻塞
                win32pipe.DisconnectNamedPipe(self.pipe)
                win32file.CloseHandle(self.pipe)
                self.pipe = None
                print("命名管道已关闭")
        except Exception as e:
            print(f"关闭管道时出错: {e}")

        # 等待线程结束，但设置较短的超时时间避免无限等待
        if hasattr(self, "pipe_thread") and self.pipe_thread.is_alive():
            print("等待管道监听线程结束...")
            self.pipe_thread.join(timeout=1.0)
            if self.pipe_thread.is_alive():
                print("警告: 管道监听线程未能在预期时间内结束")
            else:
                print("管道监听线程已结束")

    def listen_pipe_commands(self):
        """监听管道接收到的命令"""
        try:
            while self.is_running:
                if self.in_conversation:
                    time.sleep(0.5)
                    continue

                # 添加超时机制，避免ReadFile无限阻塞
                try:
                    # 使用非阻塞模式检查管道是否有数据可读
                    if win32pipe.PeekNamedPipe(self.pipe, 0)[1] > 0:
                        code, data = win32file.ReadFile(self.pipe, 4096)
                        if code == 0:  # 读取成功
                            command = data.decode("utf-8").strip()
                            if command:
                                if command in ["q", "quit"]:
                                    print("收到停止命令...")
                                    self.is_running = False
                                    break
                                elif command == "pause":
                                    self.pause_simulation.clear()
                                    print("模拟已暂停")
                                elif command == "resume":
                                    self.pause_simulation.set()
                                    print("模拟已继续")
                                elif command == "save":
                                    print("保存当前模拟状态...")
                                    last_save_record = self.save()
                                    print(f"已保存模拟记录到{last_save_record}")
                                elif command.startswith("save "):
                                    # 格式: save target_name
                                    target = command[5:].strip()
                                    last_save_record = self.save(target)
                                    print(f"已保存模拟记录到{last_save_record}")
                                else:
                                    self.command_queue.put(command)
                    else:
                        # 没有数据可读，短暂休眠后继续检查
                        time.sleep(0.1)
                except win32pipe.error as e:
                    # 如果管道已断开或其他错误，检查是否应该继续运行
                    if not self.is_running:
                        break
                    print(f"管道读取错误: {e}, 尝试重新连接...")
                    time.sleep(0.5)
                except Exception as e:
                    # 其他未预期的错误
                    print(f"管道监听时出错: {e}")
                    if not self.is_running:
                        break
                    time.sleep(0.5)

                # 定期检查是否应该退出，避免长时间不响应
                if not self.is_running:
                    print("监听线程接收到退出信号")
                    break
        except Exception as e:
            print(f"管道监听线程发生异常: {e}")
            traceback.print_exc()
        finally:
            # 确保资源释放
            print("管道监听线程正在清理资源...")
            try:
                if self.pipe and self.is_running:  # 只有在正常运行时才主动关闭
                    win32file.CloseHandle(self.pipe)
                    self.pipe = None
            except Exception as e:
                print(f"清理管道资源时出错: {e}")
            print("管道监听线程已退出")

    def start_simulation(self, steps_count):
        obj_clean = dict()

        # 如果监听线程还没启动，则启动它
        if not hasattr(self, "pipe_thread") or not self.pipe_thread.is_alive():
            if not self.start_command_listener():
                print("警告: 无法启动命令监听，将无法接收命令")

        try:
            while self.is_running and steps_count > 0:
                # 处理命令队列中的命令
                while not self.command_queue.empty():
                    command = self.command_queue.get()
                    self.process_command(command)

                # 检查是否暂停
                self.pause_simulation.wait()

                print(
                    "当前要计算的 { 时间:",
                    self.curr_time.strftime("%B %d, %Y, %H:%M:%S"),
                    "step:",
                    self.step,
                    "}",
                )

                step_start_time = time.time()  # 记录step开始时间

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
                                self.personas[
                                    persona_name
                                ].direct_mem.act_address.split(":")[-1]
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
                                        persona.direct_mem.get_curr_obj_event(),
                                        new_cell,
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

                        with ThreadPoolExecutor(
                            max_workers=len(self.personas)
                        ) as executor:
                            future_to_name = {
                                executor.submit(
                                    persona.move,
                                    self.maze,
                                    self.personas,
                                    self.curr_time,
                                    self.sec_per_step,
                                ): persona_name
                                for persona_name, persona in self.personas.items()
                            }
                            for future in future_to_name:
                                persona_name = future_to_name[future]
                                try:
                                    next_cell, desc = future.result()
                                except Exception as exc:
                                    print(f"{persona_name} 的 move() 发生异常: {exc}")
                                    traceback.print_exc()
                                    next_cell, desc = (
                                        self.personas_cell[persona_name],
                                        "",
                                    )
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
                            json.dump(
                                movements, json_file, indent=2, ensure_ascii=False
                            )

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
                            json.dump(
                                environments, json_file, indent=2, ensure_ascii=False
                            )
                        ###############################################

                        steps_count -= 1
                        print_c(f"计算完毕，剩余步数: {steps_count}")

                        # 记录该step的耗时
                        step_end_time = time.time()
                        step_duration = step_end_time - step_start_time
                        self.step_durations.append(step_duration)
        except KeyboardInterrupt:
            print("\n接收到中断信号，正在停止模拟...")
            self.is_running = False

        finally:
            print("模拟步骤已完成")
            # 注意: 不在这里关闭监听线程，由调用者决定何时关闭

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

    def save(self, target=None):
        """
        保存模拟状态
        :param target: 可选，保存的目标记录名，如果不提供则使用当前的 sim_code+已计算step
        """
        if target:
            curr_path = f"{storage_path}/{target}"
        else:
            curr_path = f"{storage_path}/{self.sim_code}-{self.step}"
        # 确保目标目录存在
        if not os.path.exists(curr_path):
            os.makedirs(curr_path, exist_ok=True)
            # 创建必要的子目录
            for subdir in ["environment", "movement", "personas"]:
                os.makedirs(f"{curr_path}/{subdir}", exist_ok=True)

            # 为每个角色创建目录，包括associative_memory子目录
            for persona_name in self.personas.keys():
                persona_dir = f"{curr_path}/personas/{persona_name}"
                os.makedirs(persona_dir, exist_ok=True)
                os.makedirs(f"{persona_dir}/associative_memory", exist_ok=True)

            # 复制当前环境和移动文件到新目录
            shutil.copy2(
                f"{self.curr_path}/environment/{self.step}.json",
                f"{curr_path}/environment/{self.step}.json",
            )
            if os.path.exists(f"{self.curr_path}/movement/{self.step-1}.json"):
                shutil.copy2(
                    f"{self.curr_path}/movement/{self.step-1}.json",
                    f"{curr_path}/movement/{self.step-1}.json",
                )

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
            os.makedirs(save_path, exist_ok=True)
            persona.save(save_path)

        # 3.保存新的maze\block\meta_info到目标文件夹
        if target:
            maze_path = f"{env_matrix}/{target}"
        else:
            maze_path = f"{env_matrix}/{self.sim_code}-{self.step}"
        self.maze.save_maze(maze_path)
        return target or f"{self.sim_code}-{self.step}"

    def run_experiment_script(self, script_path):
        """
        读取并执行实验脚本
        :param script_path: 实验脚本文件路径
        """
        try:
            # 启动命令监听线程
            if not self.start_command_listener():
                print("警告: 无法启动命令监听，将无法接收命令")

            # 读取实验脚本
            with open(script_path, "r", encoding="utf-8") as f:
                script_data = json.load(f)

            # 选择一个实验方案
            experiment_keys = list(script_data.keys())
            print("\n=== 可用实验方案 ===")
            for i, key in enumerate(experiment_keys):
                print(f"{i+1}. {key}")

            choice = int(input("请选择要执行的实验方案编号: ").strip()) - 1
            if choice < 0 or choice >= len(experiment_keys):
                print("无效的选择")
                return

            selected_experiment = script_data[experiment_keys[choice]]
            print(f"\n将执行实验: {experiment_keys[choice]}")

            # 执行实验脚本中的指令
            self.is_running = True
            for instruction in selected_experiment:
                print("当前执行指令：", instruction)
                # 跳过描述类型的指令
                if instruction["type"] == "description":
                    print(f"\n实验描述: {instruction['description']}")
                    continue

                elif instruction["type"] == "sec_per_step":
                    new_value = instruction["sec_per_step"]
                    print(f"\n更新每步时间间隔: {new_value}秒")
                    self.sec_per_step = int(new_value)
                    for persona in self.personas.values():
                        persona.direct_mem.chatting_with_buffer = dict()
                    continue

                elif instruction["type"] == "load":
                    if instruction["func"] == "whisper":
                        whisper_paths = instruction["args"]
                        for path in whisper_paths:
                            rows = read_file_to_list(
                                path, header=True, strip_trail=True
                            )[1]
                            clean_whispers = []
                            for row in rows:
                                agent_name = row[0].strip()
                                whispers = row[1].split(";")
                                whispers = [whisper.strip() for whisper in whispers]
                                for whisper in whispers:
                                    clean_whispers += [[agent_name, whisper]]
                            load_whisper_csv(self.personas, clean_whispers)
                    # TODO 其他load功能

                if instruction["type"] == "run":
                    # 运行模拟支持多种时间单位（天、小时、分钟或直接指定步数）
                    steps = 0
                    time_desc = ""

                    if "day" in instruction:
                        days = int(instruction["day"])
                        steps = days * 24 * 60 * 60 // self.sec_per_step
                        time_desc = f"{days} 天"
                    elif "hour" in instruction:
                        hours = int(instruction["hour"])
                        steps = hours * 60 * 60 // self.sec_per_step
                        time_desc = f"{hours} 小时"
                    elif "min" in instruction:
                        mins = int(instruction["min"])
                        steps = mins * 60 // self.sec_per_step
                        time_desc = f"{mins} 分钟"
                    elif "step" in instruction:
                        steps = int(instruction["step"])
                        time_desc = f"{steps} 步"
                    else:
                        print("错误：未指定有效的时间单位（day/hour/min/step）")
                        continue

                    print(f"\n开始运行模拟 {time_desc} ({steps} steps)...")
                    self.start_simulation(steps)

                elif instruction["type"] == "intervene":
                    # 执行干预操作
                    func_type = instruction["func"]
                    args = instruction["args"]
                    if func_type == "chat":
                        # chat干预
                        for target in args[0]:
                            content = args[1]
                            print(f"\n对 {target} 执行chat干预: {content}")
                            # 暂停模拟
                            self.pause_simulation.clear()
                            self.personas[target].open_convo_session("singlechat")
                            # 继续模拟
                            self.pause_simulation.set()

                    if func_type == "whisper":
                        # whisper干预
                        for target in args[0]:
                            content = args[1]
                            print(f"\n对 {target} 执行whisper干预: {content}")
                            # 暂停模拟
                            self.pause_simulation.clear()
                            # 执行whisper会话
                            self.personas[target].open_convo_session("whisper", content)
                            # 继续模拟
                            # TODO 这里要判断is_running再set()吗？
                            self.pause_simulation.set()

                    elif func_type == "order":
                        # order干预
                        for target in args[0]:
                            content = args[1]
                            expired_time = 1  # expired_time为可选参数，默认为1
                            # TODO 单位暂定为天数，因为目前只有revise_identity调用时递减这个时间
                            if len(args) > 2:
                                expired_time = int(args[2])
                            print(
                                f"\n对 {target} 执行order干预: {content}，有效期: {expired_time} 天"
                            )
                            self.personas[target].direct_mem.ordered_minds.append(
                                [
                                    self.curr_time.strftime("%A %B %d - %H:%M"),
                                    content,
                                    expired_time,
                                ]
                            )
                    elif func_type == "action":
                        for target in args[0]:
                            action_input = args[1]
                            action_dur = args[2]
                            self.personas[target].direct_mem.specify_action = [
                                action_input,
                                action_dur,
                            ]
                            print(
                                f"为 {target} 指定动作: {action_input}，持续时间: {action_dur}分钟"
                            )

                    # TODO single_chat
                    # group_chat x：用single_chat多选人实现，用户与npc对话、npc用于群体对话
                    # choose_action
                    # action √
                    # broadcast x：用whisper实现，whisper要实现重要性等级判断和响应

                elif instruction["type"] == "interview":
                    # TODO 修改为多线程
                    for target in instruction["args"][0]:
                        self.pause_simulation.clear()
                        self.in_conversation = True
                        print(f"正在与 {target} 进行interview...")
                        content_list = list(instruction["args"][1])
                        self.personas[target].open_convo_session(
                            "interview", content_list
                        )
                        self.pause_simulation.set()
                        self.in_conversation = False
                    print("interview结束，继续模拟...")

                elif instruction["type"] == "survey":
                    targets = instruction["args"][0]
                    survey_name = instruction["args"][1]
                    requirement = instruction["args"][2]
                    survey_file = instruction["args"][3]
                    print(f"\n执行调查，对象: {targets}，使用文件: {survey_file}")

                    execute_survey(targets, survey_name, requirement, survey_file)

                elif instruction["type"] == "save":
                    # 保存模拟结果
                    if "record" in instruction:
                        save_target = instruction["record"]
                        last_save_record = self.save(save_target)
                        print(f"已保存模拟记录到{last_save_record}")
                    else:
                        last_save_record = self.save()
                        print(f"已保存模拟记录到{last_save_record}")

            print("\n实验脚本执行完成!")
            self.is_running = False

        except Exception as e:
            print(f"执行实验脚本时出错: {e}")
            traceback.print_exc()
        finally:
            self.save(self.sim_code)
            self.is_running = False
            self.stop_command_listener()

    def start_server(self):
        try:
            # 启动命令监听线程
            if not self.start_command_listener():
                print("警告: 无法启动命令监听，将无法接收命令")

            while True:
                try:
                    command = input("输入指令:").strip().lower()
                    if command[:3] == "run":
                        int_steps = int(command.split()[-1])
                        self.start_simulation(int_steps)
                        print("start_simulation done")
                        self.save(self.sim_code)
                        print("save done")
                        break
                    elif "srun" in command:
                        int_secs = int(command.split()[-1])
                        self.start_simulation(int_secs // self.sec_per_step)
                        self.save(self.sim_code)
                        break
                    elif "mrun" in command:
                        int_mins = int(command.split()[-1])
                        self.start_simulation(int_mins * 60 // self.sec_per_step)
                        self.save(self.sim_code)
                        break
                    elif "hrun" in command:
                        int_hours = int(command.split()[-1])
                        self.start_simulation(int_hours * 3600 // self.sec_per_step)
                        self.save(self.sim_code)
                        break
                    elif "drun" in command:
                        int_days = int(command.split()[-1])
                        self.start_simulation(int_days * 24 * 3600 // self.sec_per_step)
                        self.save(self.sim_code)
                        break
                    elif "whisper load" in command:
                        # 批量读取whisper csv
                        # whisper load 完整路径
                        curr_file = command[len("whisper load") :].strip()
                        rows = read_file_to_list(
                            curr_file, header=True, strip_trail=True
                        )[1]
                        clean_whispers = []
                        for row in rows:
                            agent_name = row[0].strip()
                            whispers = row[1].split(";")
                            whispers = [whisper.strip() for whisper in whispers]
                            for whisper in whispers:
                                clean_whispers += [[agent_name, whisper]]

                        load_whisper_csv(self.personas, clean_whispers)
                    elif command in ["m", "maze"]:
                        print(self.maze.cells_of_addr.keys())
                        print(self.maze.cells_of_addr)
                except:
                    traceback.print_exc()
                    print("Error.")
                    pass
        finally:
            # 确保停止监听线程
            self.is_running = False
            self.stop_command_listener()


if __name__ == "__main__":
    # 创建命令行参数解析器
    parser = argparse.ArgumentParser(description="LLMComm模拟系统")
    parser.add_argument("mode", help="运行模式：script或普通模式")
    parser.add_argument("origin", help="源模拟记录名称")
    parser.add_argument("target", help="本次模拟记录名称")
    parser.add_argument(
        "script_path", nargs="?", help="脚本文件路径（仅script模式需要）"
    )
    parser.add_argument(
        "--sec_per_step",
        type=int,
        default=None,
        help="每step的游戏时间间隔（秒），默认为10",
    )

    # 解析命令行参数
    args = parser.parse_args(sys.argv[1:])
    if args.mode == "script":
        if not args.script_path:
            print("脚本模式需要提供脚本文件路径")
            sys.exit(1)
        server = SimulationServer(args.origin, args.target, args.sec_per_step)
        server.run_experiment_script(args.script_path)
    else:
        server = SimulationServer(args.origin, args.target, args.sec_per_step)
        server.start_server()
