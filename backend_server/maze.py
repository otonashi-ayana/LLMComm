from global_methods import *
from utils import *
import json
import os
import csv
import shutil


class Maze:
    def __init__(self, fork_sim_code, sim_code):
        self.fork_sim_code = fork_sim_code
        self.sim_code = sim_code
        meta_info = json.load(
            open(
                f"{env_matrix}/{self.fork_sim_code}/maze_meta_info.json",
                encoding="utf-8",
            )
        )
        self.world_name = meta_info["world_name"]
        self.maze_width = int(meta_info["maze_width"])
        self.maze_height = int(meta_info["maze_height"])

        # 添加对象变更记录列表
        self.object_changes = []

        blocks_path = f"{env_matrix}/{self.fork_sim_code}/blocks"
        sb_rows = read_file_to_list(blocks_path + "/sector_blocks.csv", header=False)
        sb_dict = dict()
        for i in sb_rows:
            sb_dict[i[0]] = i[-1]

        ab_rows = read_file_to_list(blocks_path + "/area_blocks.csv", header=False)
        ab_dict = dict()
        for i in ab_rows:
            ab_dict[i[0]] = i[-1]

        # 将object_blocks相关变量保存为类成员变量
        self.ob_rows = read_file_to_list(
            blocks_path + "/object_blocks.csv", header=False
        )
        self.ob_dict = dict()
        # 创建反向映射字典
        self.ob_reverse_dict = dict()
        for i in self.ob_rows:
            self.ob_dict[i[0]] = i[-1]
            self.ob_reverse_dict[i[-1]] = i[0]

        maze_path = f"{env_matrix}/{self.fork_sim_code}/maze"

        self.collision_2d = []
        self.sector_2d = []
        self.area_2d = []
        self.object_2d = []

        _cm = maze_path + "/collision_maze.csv"
        self.collision_2d = read_2d_csv_to_list(_cm)
        _sm = maze_path + "/sector_maze.csv"
        self.sector_2d = read_2d_csv_to_list(_sm)
        _am = maze_path + "/area_maze.csv"
        self.area_2d = read_2d_csv_to_list(_am)
        _om = maze_path + "/object_maze.csv"
        self.object_2d = read_2d_csv_to_list(_om)

        # 将位置信息与碰撞信息录入cells中，并初始化cells的event信息
        self.cells = []
        for i in range(self.maze_height):
            row = []
            for j in range(self.maze_width):
                cell_info = dict()
                cell_info["world"] = self.world_name
                cell_info["sector"] = ""
                if self.sector_2d[i][j] in sb_dict:
                    cell_info["sector"] = sb_dict[self.sector_2d[i][j]]
                cell_info["area"] = ""
                if self.area_2d[i][j] in ab_dict:
                    cell_info["area"] = ab_dict[self.area_2d[i][j]]
                cell_info["object"] = ""
                if self.object_2d[i][j] in self.ob_dict:
                    cell_info["object"] = self.ob_dict[self.object_2d[i][j]]
                if self.collision_2d[i][j] != "0":
                    cell_info["collision"] = True
                else:
                    cell_info["collision"] = False

                cell_info["events"] = set()
                row += [cell_info]
            self.cells += [row]

        for i in range(self.maze_height):
            for j in range(self.maze_width):
                if self.cells[i][j]["object"]:
                    object_name = ":".join(
                        [
                            self.cells[i][j]["world"],
                            self.cells[i][j]["sector"],
                            self.cells[i][j]["area"],
                            self.cells[i][j]["object"],
                        ]
                    )
                    object_event = (object_name, None, None, None)
                    self.cells[i][j]["events"].add(object_event)

        self.cells_of_addr = dict()
        for i in range(self.maze_height):
            for j in range(self.maze_width):
                addresses = []
                if self.cells[i][j]["sector"]:
                    add = f'{self.cells[i][j]["world"]}:'
                    add += f'{self.cells[i][j]["sector"]}'
                    addresses += [add]
                if self.cells[i][j]["area"]:
                    add = f'{self.cells[i][j]["world"]}:'
                    add += f'{self.cells[i][j]["sector"]}:'
                    add += f'{self.cells[i][j]["area"]}'
                    addresses += [add]
                if self.cells[i][j]["object"]:
                    add = f'{self.cells[i][j]["world"]}:'
                    add += f'{self.cells[i][j]["sector"]}:'
                    add += f'{self.cells[i][j]["area"]}:'
                    add += f'{self.cells[i][j]["object"]}'
                    addresses += [add]

                for add in addresses:
                    if add in self.cells_of_addr:
                        self.cells_of_addr[add].add((j, i))
                    else:
                        self.cells_of_addr[add] = set([(j, i)])
        print("<Maze.init> done")

    def export_map_structure(self, output_path=None):
        """
        将地图层级结构导出为JSON文件，结构与spatial_memory.json类似
        """
        if output_path is None:
            output_path = f"{storage_path}/map_structure.json"

        # 构建层级结构
        structure = {}

        # 遍历所有地址
        for addr in self.cells_of_addr.keys():
            parts = addr.split(":")

            # 跳过无效地址
            if len(parts) < 2 or not all(parts):
                continue

            world = parts[0]
            sector = parts[1] if len(parts) > 1 else ""
            area = parts[2] if len(parts) > 2 else ""
            obj = parts[3] if len(parts) > 3 else ""

            if sector == "小区大门":
                continue

            # 构建嵌套结构
            if world not in structure:
                structure[world] = {}

            if sector and sector != "":
                if sector not in structure[world]:
                    structure[world][sector] = {}

                if area and area != "":
                    if area not in structure[world][sector]:
                        structure[world][sector][area] = []

                    if obj and obj != "" and obj not in structure[world][sector][area]:
                        structure[world][sector][area].append(obj)

        # 写入JSON文件
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(structure, f, indent=4, ensure_ascii=False)

        print(f"<Maze.export_map_structure> 地图结构已导出到: {output_path}")
        return structure

    def access_cell(self, cell):
        x = cell[0]
        y = cell[1]
        return self.cells[y][x]

    def get_cell_path(self, cell, level):
        """
        获得cell对应的地址信息
        """
        x = cell[0]
        y = cell[1]
        cell = self.cells[y][x]

        path = f"{cell['world']}"
        if level == "world":
            return path
        else:
            path += f":{cell['sector']}"

        if level == "sector":
            return path
        else:
            path += f":{cell['area']}"

        if level == "area":
            return path
        else:
            path += f":{cell['object']}"

        return path

    def get_nearby_cells(self, cell, vision_r):
        """
        x x x x x
        x x x x x
        x x P x x
        x x x x x
        x x x x x
        """
        left_end = 0
        if cell[0] - vision_r > left_end:
            left_end = cell[0] - vision_r

        right_end = self.maze_width - 1
        if cell[0] + vision_r + 1 < right_end:
            right_end = cell[0] + vision_r + 1

        bottom_end = self.maze_height - 1
        if cell[1] + vision_r + 1 < bottom_end:
            bottom_end = cell[1] + vision_r + 1

        top_end = 0
        if cell[1] - vision_r > top_end:
            top_end = cell[1] - vision_r

        nearby_cells = []
        for i in range(left_end, right_end):
            for j in range(top_end, bottom_end):
                nearby_cells += [(i, j)]
        return nearby_cells

    def add_event_to_cell(self, event, cell):
        self.cells[cell[1]][cell[0]]["events"].add(event)

    def remove_event_from_cell(self, event, cell):
        curr_cell_ev_cp = self.cells[cell[1]][cell[0]]["events"].copy()
        for curr_event in curr_cell_ev_cp:
            if event == curr_event:
                self.cells[cell[1]][cell[0]]["events"].remove(curr_event)

    def remove_subject_event_from_cell(self, subject, cell):
        try:
            curr_cell_ev_cp = self.cells[cell[1]][cell[0]]["events"].copy()
        except:
            print("<remove_subject_event_from_cell> cell:", cell)
        # print("subject:", subject, "curr_cell_ev_cp:", curr_cell_ev_cp)
        for event in curr_cell_ev_cp:
            # print("event:", event)
            if event[0] == subject:
                self.cells[cell[1]][cell[0]]["events"].remove(event)

    # 将cell的event设置为idle(None, None, None)
    def turn_event_idle_from_cell(self, curr_event, cell):
        curr_cell_ev_cp = self.cells[cell[1]][cell[0]]["events"].copy()
        for event in curr_cell_ev_cp:
            if event == curr_event:
                self.cells[cell[1]][cell[0]]["events"].remove(event)
                new_event = (event[0], None, None, None)
                self.cells[cell[1]][cell[0]]["events"].add(new_event)

    def place_object(self, x, y, object_name):
        """
        在指定坐标(x, y)处放置一个object
        如果该位置已有object，则覆盖它

        参数:
            x, y: 坐标
            object_name: 物体名称

        返回:
            bool: 是否成功放置
        """
        # 检查坐标是否有效
        if not (0 <= x < self.maze_width and 0 <= y < self.maze_height):
            print(f"<Maze.place_object> 无效坐标: ({x}, {y})")
            return False

        # 获取cell
        cell = self.cells[y][x]

        # 记录旧的object地址（如果有的话）
        old_object = cell["object"]
        old_address = None
        if old_object:
            old_address = (
                f'{cell["world"]}:{cell["sector"]}:{cell["area"]}:{old_object}'
            )

        # 更新object字段
        cell["object"] = object_name

        # 构建新地址
        new_address = f'{cell["world"]}:{cell["sector"]}:{cell["area"]}:{object_name}'

        # 从cells_of_addr中移除旧地址（如果有的话）
        if old_address and old_address in self.cells_of_addr:
            self.cells_of_addr[old_address].remove((x, y))
            if not self.cells_of_addr[old_address]:  # 如果集合为空，删除键
                del self.cells_of_addr[old_address]

        # 向cells_of_addr添加新地址
        if new_address in self.cells_of_addr:
            self.cells_of_addr[new_address].add((x, y))
        else:
            self.cells_of_addr[new_address] = set([(x, y)])

        # 更新cell的events
        if old_object:
            for event in cell["events"]:
                event = (new_address, event[1], event[2], event[3])
        else:
            object_event = (new_address, None, None, None)
            cell["events"].add(object_event)

        # 更新object_2d数组 - 修改为使用正确的ID映射
        if old_object and old_object in self.ob_reverse_dict:
            # 如果object已在映射中，使用现有ID
            object_id = self.ob_reverse_dict[old_object]
            for i in self.ob_rows:
                if i[0] == object_id:
                    i[1] = object_name
            # 将读取的ob_blocks数组中的object_name更新为新的object_name
        else:
            # 如果object是新的，创建新ID
            last_id = int(self.ob_rows[-1][0])
            # 获取最后一个ID并加1
            new_id = str(last_id + 1)

            # 添加新映射
            self.ob_rows.append([new_id, object_name])
            self.ob_dict[new_id] = object_name
            self.ob_reverse_dict[object_name] = new_id
            object_id = new_id

            # 可选：更新CSV文件以持久化新映射
            with open(
                f"{env_matrix}/blocks/object_blocks.csv",
                "a",
                newline="",
                encoding="utf-8",
            ) as f:
                writer = csv.writer(f)
                writer.writerow([new_id, object_name])

        self.object_2d[y][x] = object_id

        # 记录物体变更
        change_record = {
            "position": [x, y],
            "old_object": old_object,
            "new_object": object_name,
            "old_address": old_address,
            "new_address": new_address,
        }
        self.object_changes.append(change_record)

        print(
            f"<Maze.place_object> 在 ({x}, {y}) 处放置了物体: {object_name} (ID: {object_id})"
        )
        return True

    def save_maze(self, output_dir):
        """
        保存当前迷宫状态到指定目录

        参数:
            output_dir: 输出目录，默认为 {maze_assets_loc}/Comm/matrix/{sim_code}

        返回:
            bool: 是否成功保存
        """
        # 确保目录存在
        os.makedirs(output_dir, exist_ok=True)

        try:
            source_dir = f"{env_matrix}/{self.fork_sim_code}"

            maze_source = f"{source_dir}/maze"
            maze_files_to_copy = ["sector_maze.csv", "area_maze.csv","collision_maze.csv"]
            maze_dest = f"{output_dir}/maze"
            os.makedirs(maze_dest, exist_ok=True)
            for file in maze_files_to_copy:
                source_file = f"{maze_source}/{file}"
                dest_file = f"{maze_dest}/{file}"
                if os.path.exists(source_file) and not os.path.exists(dest_file):
                    shutil.copy2(source_file, dest_file)

            with open(f"{maze_dest}/object_maze.csv", "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                for row in self.object_2d:
                    writer.writerow(row)

            blocks_source = f"{source_dir}/blocks"
            block_files_to_copy = ["sector_blocks.csv", "area_blocks.csv"]
            blocks_dest = f"{output_dir}/blocks"
            os.makedirs(blocks_dest, exist_ok=True)
            for file in block_files_to_copy:
                source_file = f"{source_dir}/{file}"
                dest_file = f"{output_dir}/{file}"
                if os.path.exists(source_file) and not os.path.exists(dest_file):
                    shutil.copy2(source_file, dest_file)

            with open(f"{blocks_dest}/object_blocks.csv", "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                for row in self.ob_rows:
                    writer.writerow(row)

            for file in block_files_to_copy:
                source_file = f"{blocks_source}/{file}"
                dest_file = f"{blocks_dest}/{file}"
                if os.path.exists(source_file) and not os.path.exists(dest_file):
                    shutil.copy2(source_file, dest_file)


            source_meta_path = f"{env_matrix}/{self.fork_sim_code}/maze_meta_info.json"
            with open(source_meta_path, "r", encoding="utf-8") as f:
                meta_info = json.load(f)

            meta_info["object_changes"] = self.object_changes

            meta_info_path = f"{output_dir}/maze_meta_info.json"
            with open(meta_info_path, "w", encoding="utf-8") as f:
                json.dump(meta_info, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"<Maze.save_maze> 保存迷宫时出错: {e}")
            return False
