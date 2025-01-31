from global_methods import *
from utils import *
import json


class Maze:
    def __init__(self):
        meta_info = json.load(
            open(f"{env_matrix}/maze_meta_info.json", encoding="utf-8")
        )
        self.world_name = meta_info["world_name"]
        self.maze_width = int(meta_info["maze_width"])
        self.maze_height = int(meta_info["maze_height"])
        # self.sq_cell_size = int(meta_info["sq_cell_size"])

        blocks_path = f"{env_matrix}/blocks"
        sb_rows = read_file_to_list(blocks_path + "/sector_blocks.csv", header=False)
        sb_dict = dict()
        for i in sb_rows:
            sb_dict[i[0]] = i[-1]

        ab_rows = read_file_to_list(blocks_path + "/area_blocks.csv", header=False)
        ab_dict = dict()
        for i in ab_rows:
            ab_dict[i[0]] = i[-1]

        ob_rows = read_file_to_list(blocks_path + "/object_blocks.csv", header=False)
        ob_dict = dict()
        for i in ob_rows:
            ob_dict[i[0]] = i[-1]

        # slb_rows = read_file_to_list(blocks_path + "/spawning_location_blocks.csv")
        # slb_dict = dict()
        # for i in slb_rows:
        #     slb_dict[i[0]] = i[-1]

        maze_path = f"{env_matrix}/maze"

        collision_2d = []
        sector_2d = []
        area_2d = []
        object_2d = []
        # spawning_location_2d = []

        _cm = maze_path + "/collision_maze.csv"
        collision_2d = read_2d_csv_to_list(_cm)
        _sm = maze_path + "/sector_maze.csv"
        sector_2d = read_2d_csv_to_list(_sm)
        _am = maze_path + "/area_maze.csv"
        area_2d = read_2d_csv_to_list(_am)
        _om = maze_path + "/object_maze.csv"
        object_2d = read_2d_csv_to_list(_om)
        # _slm = maze_path + "/spawning_location_maze.csv"
        # spawning_location_2d = read_2d_csv_to_list(_slm)

        # 将位置信息与碰撞信息录入cells中，并初始化cells的event信息
        self.cells = []
        for i in range(self.maze_height):
            row = []
            for j in range(self.maze_width):
                cell_info = dict()
                cell_info["world"] = self.world_name
                cell_info["sector"] = ""
                if sector_2d[i][j] in sb_dict:
                    cell_info["sector"] = sb_dict[sector_2d[i][j]]
                cell_info["area"] = ""
                if area_2d[i][j] in ab_dict:
                    cell_info["area"] = ab_dict[area_2d[i][j]]
                cell_info["object"] = ""
                if object_2d[i][j] in ob_dict:
                    cell_info["object"] = ob_dict[object_2d[i][j]]
                cell_info["spawning_location"] = ""
                # if spawning_location_2d[i][j] in slb_dict:
                #     cell_info["spawning_location"] = slb_dict[
                #         spawning_location_2d[i][j]
                #     ]
                if collision_2d[i][j] != "0":
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
                # if self.cells[i][j]["spawning_location"]:
                #     add = f'<spawn_loc>{self.cells[i][j]["spawning_location"]}'
                #     addresses += [add]

                for add in addresses:
                    if add in self.cells_of_addr:
                        self.cells_of_addr[add].add((j, i))
                    else:
                        self.cells_of_addr[add] = set([(j, i)])
        print("<Maze.init> done")

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
        curr_cell_ev_cp = self.cells[cell[1]][cell[0]]["events"].copy()
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
