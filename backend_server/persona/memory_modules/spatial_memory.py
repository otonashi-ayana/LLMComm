import sys

sys.path.append("../../")
import json
from global_methods import *


class MemoryTree:
    def __init__(self, f_saved):
        self.tree = {}
        if check_if_file_exists(f_saved):
            self.tree = json.load(open(f_saved, encoding="utf-8"))

    def print_tree(self):
        def _print_tree(tree, depth):
            dash = " >" * depth
            if type(tree) == type(list()):
                if tree:
                    print(dash, tree)
                return

            for key, val in tree.items():
                if key:
                    print(dash, key)
                _print_tree(val, depth + 1)

        _print_tree(self.tree, 0)

    def save(self, out_json):
        with open(out_json, "w", encoding="utf-8") as outfile:
            json.dump(self.tree, outfile, indent=2, ensure_ascii=False)

    def get_str_accessible_sectors(self, curr_world):
        x = ", ".join(list(self.tree[curr_world].keys()))
        return x

    def get_str_accessible_sector_areas(self, sector):
        curr_world, curr_sector = sector.split(":")
        if not curr_sector:
            return ""
        x = ", ".join(list(self.tree[curr_world][curr_sector].keys()))
        return x

    def get_str_accessible_area_objects(self, area):
        curr_world, curr_sector, curr_area = area.split(":")

        if not curr_area:
            return ""
        x = ", ".join(list(self.tree[curr_world][curr_sector][curr_area]))
        return x
