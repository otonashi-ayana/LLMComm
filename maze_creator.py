#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import messagebox, filedialog, simpledialog
import json
import csv
import os

# -------------------------------
#  1. 编号分配器
# -------------------------------
WORLD_ID = 11000
SECTOR_BASE = 11001
SECTOR_COUNT = 40
SECTOR_SIZE = 50
OBJECT_BASE = 13001
COLLISION_ID = 10000


class MapIDAllocator:
    def __init__(self):
        self._area_counts = [0] * SECTOR_COUNT
        self._object_count = 0

    def get_world_id(self):
        return WORLD_ID

    def get_sector_id(self, sector_index):
        if not (1 <= sector_index <= SECTOR_COUNT):
            raise ValueError("Sector index超出范围")
        return SECTOR_BASE + (sector_index - 1) * SECTOR_SIZE

    def get_next_area_id(self, sector_index):
        if not (1 <= sector_index <= SECTOR_COUNT):
            raise ValueError("Sector index超出范围")
        base = self.get_sector_id(sector_index)
        used = self._area_counts[sector_index - 1]
        if used >= (SECTOR_SIZE - 1):
            raise ValueError("该Sector的Area已分配完")
        area_id = base + 1 + used
        self._area_counts[sector_index - 1] += 1
        return area_id

    def get_next_object_id(self):
        oid = OBJECT_BASE + self._object_count
        self._object_count += 1
        return oid

    def set_state(self, area_counts, object_count):
        if len(area_counts) == SECTOR_COUNT:
            self._area_counts = area_counts
        self._object_count = object_count

    def get_state(self):
        return {"area_counts": self._area_counts, "object_count": self._object_count}


# -------------------------------
#  2. Region 数据类
# -------------------------------
class Region:
    """
    type: 'sector'/'area'/'object'
    id: 唯一编号
    name: 名称(全局唯一若为object)
    parent_id: 父级id
    cells: set((r,c), ...)
    """

    def __init__(self, rtype, rid, name, pid, cells):
        self.type = rtype
        self.id = rid
        self.name = name
        self.parent_id = pid
        self.cells = set(cells)

    def to_dict(self):
        return {
            "type": self.type,
            "id": self.id,
            "name": self.name,
            "parent_id": self.parent_id,
            "cells": list(self.cells),
        }

    @staticmethod
    def from_dict(d):
        return Region(
            d["type"],
            d["id"],
            d["name"],
            d["parent_id"],
            set(tuple(x) for x in d["cells"]),
        )


# -------------------------------
#  3. 地图编辑器
# -------------------------------
def center_window(win, parent=None):
    """将窗口在 parent 或屏幕中心居中。"""
    win.update_idletasks()
    w = win.winfo_reqwidth()
    h = win.winfo_reqheight()

    if parent:
        px = parent.winfo_rootx()
        py = parent.winfo_rooty()
        pw = parent.winfo_width()
        ph = parent.winfo_height()
        x = px + (pw - w) // 2
        y = py + (ph - h) // 2
    else:
        sw = win.winfo_screenwidth()
        sh = win.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2

    win.geometry(f"+{x}+{y}")


class MapEditorUI(tk.Tk):
    def __init__(self, rows=10, cols=10, cell_size=40):
        super().__init__()
        self.title("地图编辑器")
        self.resizable(False, False)

        self.rows = rows
        self.cols = cols
        self.cell_size = cell_size

        # 新增：用于存储 world 的名称(从新建项目或加载项目获得)
        self.world_name = None

        # 分配器 & 区域
        self.id_allocator = MapIDAllocator()
        self.regions = []

        # cell_info
        self.cell_info = [
            [
                {"sector": None, "area": None, "object": None, "collision": False}
                for _ in range(cols)
            ]
            for _ in range(rows)
        ]

        # 标记是否碰撞模式
        self.collision_mode = tk.BooleanVar(value=False)

        # 拖拽辅助
        self.lbutton_drag_start = None
        self.lbutton_drag_rect = None
        self.rbutton_drag_start = None
        self.rbutton_drag_rect = None

        # 在构造函数里先让用户选择 "新建项目" 或 "加载项目"
        self.project_startup_dialog()

    # -------------------------------
    #  3.1 项目启动对话
    # -------------------------------
    def project_startup_dialog(self):
        """
        弹出一个对话框，让用户选择“新建项目” or “加载项目”。
        """
        dlg = tk.Toplevel(self)
        dlg.title("选择项目")
        center_window(dlg, self)

        lbl = tk.Label(dlg, text="请选择操作：")
        lbl.pack(pady=10)

        btn_frame = tk.Frame(dlg)
        btn_frame.pack(pady=10)

        def new_project():
            dlg.destroy()
            self.new_project_dialog()

        def load_project():
            dlg.destroy()
            self.load_map()  # 直接进入加载

        tk.Button(btn_frame, text="新建项目", command=new_project).pack(
            side="left", padx=10
        )
        tk.Button(btn_frame, text="加载项目", command=load_project).pack(
            side="left", padx=10
        )

        # 阻塞主窗口，直到该对话框被关闭
        self.wait_window(dlg)

        # 如果依然没有 world_name，则用户可能取消或从 load_map 里没成功加载
        if not self.world_name:
            # 若仍为空，可以再给一次新建项目机会
            if messagebox.askyesno(
                "提示", "尚未成功创建或加载项目。要新建项目吗？", parent=self
            ):
                self.new_project_dialog()
            else:
                # 用户选择否，则退出
                self.quit()
                return

        # 如果已经有了 world_name，就继续初始化界面
        self.create_widgets()
        self.create_menu()
        self.bind_events()
        self.redraw_all_cells()

    def new_project_dialog(self):
        """
        弹出对话框让用户输入 world 名称
        """
        dlg = tk.Toplevel(self)
        dlg.title("新建项目")
        center_window(dlg, self)

        lbl = tk.Label(dlg, text="请输入 World 名称：")
        lbl.pack(pady=5)

        var_name = tk.StringVar()
        ent = tk.Entry(dlg, textvariable=var_name)
        ent.pack(pady=5)

        def on_ok():
            wname = var_name.get().strip()
            if not wname:
                messagebox.showerror("错误", "World 名称不能为空", parent=dlg)
                return
            self.world_name = wname
            messagebox.showinfo("成功", f"已创建新项目，World名称={wname}", parent=dlg)
            dlg.destroy()

        tk.Button(dlg, text="确定", command=on_ok).pack(pady=10)

        self.wait_window(dlg)

    # -------------------------------
    #  3.2 创建UI等(在 project_startup_dialog 之后)
    # -------------------------------
    def create_widgets(self):
        main_frame = tk.Frame(self)
        main_frame.pack(padx=10, pady=10)

        # 画布
        self.canvas = tk.Canvas(
            main_frame,
            width=self.cols * self.cell_size,
            height=self.rows * self.cell_size,
            bg="white",
        )
        self.canvas.grid(row=0, column=0, padx=5, pady=5)

        # 网格线
        for r in range(self.rows + 1):
            y = r * self.cell_size
            self.canvas.create_line(0, y, self.cols * self.cell_size, y, fill="#ccc")
        for c in range(self.cols + 1):
            x = c * self.cell_size
            self.canvas.create_line(x, 0, x, self.rows * self.cell_size, fill="#ccc")

        # 右侧面板
        right_frame = tk.Frame(main_frame)
        right_frame.grid(row=0, column=1, sticky="ns")

        lbl_world = tk.Label(
            right_frame, text=f"World ID={self.id_allocator.get_world_id()}"
        )
        lbl_world.pack(pady=5)

        lbl_wname = tk.Label(right_frame, text=f"World 名称={self.world_name}")
        lbl_wname.pack(pady=5)

        cb_collision = tk.Checkbutton(
            right_frame, text="碰撞模式", variable=self.collision_mode
        )
        cb_collision.pack(pady=5)

        hint_label = tk.Label(
            right_frame,
            text="碰撞模式：\n  左键拖拽=设置碰撞, 右键拖拽=取消碰撞\n\n"
            "普通模式：\n  左键拖拽=创建层级\n  右键单击=修改/删除",
        )
        hint_label.pack(pady=5)

    def create_menu(self):
        menu_bar = tk.Menu(self)
        file_menu = tk.Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="保存", command=self.save_map)
        file_menu.add_command(label="读取", command=self.load_map)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.quit)
        menu_bar.add_cascade(label="文件", menu=file_menu)

        export_menu = tk.Menu(menu_bar, tearoff=0)
        export_menu.add_command(label="导出CSV", command=self.export_csv_files)
        menu_bar.add_cascade(label="导出", menu=export_menu)

        self.config(menu=menu_bar)

    def bind_events(self):
        self.canvas.bind("<Button-1>", self.on_lbutton_down)
        self.canvas.bind("<B1-Motion>", self.on_lbutton_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_lbutton_up)

        self.canvas.bind("<Button-3>", self.on_rbutton_down)
        self.canvas.bind("<B3-Motion>", self.on_rbutton_drag)
        self.canvas.bind("<ButtonRelease-3>", self.on_rbutton_up)

        self.canvas.bind("<Motion>", self.on_mouse_move)

    # -------------------------------
    #  3.3 拖拽等事件
    # -------------------------------
    def on_lbutton_down(self, event):
        r, c = self.coord_to_cell(event.x, event.y)
        if r is None or c is None:
            return
        self.lbutton_drag_start = (r, c)

    def on_lbutton_drag(self, event):
        if not self.lbutton_drag_start:
            return
        r, c = self.coord_to_cell(event.x, event.y)
        if r is None or c is None:
            return
        if self.lbutton_drag_rect:
            self.canvas.delete(self.lbutton_drag_rect)
            self.lbutton_drag_rect = None

        r1, c1 = self.lbutton_drag_start
        top, bottom = sorted([r1, r])
        left, right = sorted([c1, c])

        x1 = left * self.cell_size
        y1 = top * self.cell_size
        x2 = (right + 1) * self.cell_size
        y2 = (bottom + 1) * self.cell_size

        self.lbutton_drag_rect = self.canvas.create_rectangle(
            x1, y1, x2, y2, fill="blue", stipple="gray25", outline="blue"
        )

    def on_lbutton_up(self, event):
        if not self.lbutton_drag_start:
            return
        if self.lbutton_drag_rect:
            self.canvas.delete(self.lbutton_drag_rect)
            self.lbutton_drag_rect = None

        start_r, start_c = self.lbutton_drag_start
        end_r_c = self.coord_to_cell(event.x, event.y) or (start_r, start_c)
        end_r, end_c = end_r_c
        self.lbutton_drag_start = None

        top, bottom = sorted([start_r, end_r])
        left, right = sorted([start_c, end_c])

        if self.collision_mode.get():
            # 碰撞模式 => 左键拖拽设置碰撞
            for rr in range(top, bottom + 1):
                for cc in range(left, right + 1):
                    self.cell_info[rr][cc]["collision"] = True
            self.redraw_all_cells()
        else:
            # 普通模式 => 创建层级
            cells = [
                (r, c) for r in range(top, bottom + 1) for c in range(left, right + 1)
            ]
            self.popup_create_region(cells)

    def on_rbutton_down(self, event):
        r, c = self.coord_to_cell(event.x, event.y)
        if r is None or c is None:
            return
        self.rbutton_drag_start = (r, c)

    def on_rbutton_drag(self, event):
        if not self.rbutton_drag_start:
            return
        r, c = self.coord_to_cell(event.x, event.y)
        if r is None or c is None:
            return
        if self.rbutton_drag_rect:
            self.canvas.delete(self.rbutton_drag_rect)
            self.rbutton_drag_rect = None

        r1, c1 = self.rbutton_drag_start
        top, bottom = sorted([r1, r])
        left, right = sorted([c1, c])

        x1 = left * self.cell_size
        y1 = top * self.cell_size
        x2 = (right + 1) * self.cell_size
        y2 = (bottom + 1) * self.cell_size

        self.rbutton_drag_rect = self.canvas.create_rectangle(
            x1, y1, x2, y2, fill="red", stipple="gray25", outline="red"
        )

    def on_rbutton_up(self, event):
        if not self.rbutton_drag_start:
            return
        if self.rbutton_drag_rect:
            self.canvas.delete(self.rbutton_drag_rect)
            self.rbutton_drag_rect = None

        start_r, start_c = self.rbutton_drag_start
        end_r_c = self.coord_to_cell(event.x, event.y) or (start_r, start_c)
        end_r, end_c = end_r_c
        self.rbutton_drag_start = None

        top, bottom = sorted([start_r, end_r])
        left, right = sorted([start_c, end_c])

        if self.collision_mode.get():
            # 碰撞模式 => 右键拖拽取消碰撞
            for rr in range(top, bottom + 1):
                for cc in range(left, right + 1):
                    self.cell_info[rr][cc]["collision"] = False
            self.redraw_all_cells()
        else:
            # 非碰撞模式 => 若是单格 => 修改/删除
            if top == bottom and left == right:
                reg = self.get_lowest_region_for_cell(top, left)
                self.popup_modify_region(top, left, reg)
            # 否则忽略(可以自行扩展更多功能)

    # -------------------------------
    #  3.4 创建Region (Object不重名)
    # -------------------------------
    def popup_create_region(self, cells):
        top = tk.Toplevel(self)
        top.title("创建新区域")
        center_window(top, self)

        tk.Label(top, text="类型：").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        var_type = tk.StringVar(value="sector")
        opt_type = tk.OptionMenu(top, var_type, "sector", "area", "object")
        opt_type.grid(row=0, column=1, sticky="w", padx=5, pady=5)

        tk.Label(top, text="名称：").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        var_name = tk.StringVar()
        ent_name = tk.Entry(top, textvariable=var_name)
        ent_name.grid(row=1, column=1, sticky="w", padx=5, pady=5)

        def on_ok():
            rtype = var_type.get()
            rname = var_name.get().strip()
            if rtype != "object" and not rname:
                messagebox.showerror("错误", "名称不能为空", parent=top)
                return
            try:
                reg = self.define_region(rtype, rname, cells)
            except ValueError as e:
                messagebox.showerror("错误", str(e), parent=top)
                return
            messagebox.showinfo(
                "成功", f"创建 {rtype}\n名称={reg.name}\nID={reg.id}", parent=top
            )
            top.destroy()

        btn_ok = tk.Button(top, text="确定", command=on_ok)
        btn_ok.grid(row=2, column=0, columnspan=2, pady=10)

    def define_region(self, rtype, rname, cells):
        cset = set(cells)
        if rtype == "sector":
            # ...
            for r, c in cset:
                if self.cell_info[r][c]["sector"]:
                    raise ValueError("选区内已有Sector")
            found_idx = None
            for idx in range(1, SECTOR_COUNT + 1):
                sid = self.id_allocator.get_sector_id(idx)
                if not self.find_region_by_id(sid):
                    found_idx = idx
                    break
            if found_idx is None:
                raise ValueError("无可用 Sector index")
            sec_id = self.id_allocator.get_sector_id(found_idx)
            reg = Region("sector", sec_id, rname, None, cset)
            self.regions.append(reg)
            for r, c in cset:
                self.cell_info[r][c]["sector"] = {"id": sec_id, "name": rname}

        elif rtype == "area":
            # ...
            s_id = None
            for r, c in cset:
                s = self.cell_info[r][c]["sector"]
                if not s:
                    raise ValueError("选区内有格子不在Sector中")
                if s_id is None:
                    s_id = s["id"]
                elif s["id"] != s_id:
                    raise ValueError("选区跨越多个Sector")
                if self.cell_info[r][c]["area"]:
                    raise ValueError("选区内已有Area")
            idx = self.sector_id_to_index(s_id)
            a_id = self.id_allocator.get_next_area_id(idx)
            reg = Region("area", a_id, rname, s_id, cset)
            self.regions.append(reg)
            for r, c in cset:
                self.cell_info[r][c]["area"] = {"id": a_id, "name": rname}

        elif rtype == "object":
            reg = self.popup_select_or_new_object(cset)

        else:
            raise ValueError("未知区域类型")

        self.redraw_all_cells()
        return reg

    def popup_select_or_new_object(self, cells_set):
        """
        弹窗：下拉列表中列出所有已有object名称 + 一项“(新建Object)”
        用户可选已有object => 复用ID并把选区网格并入
        或选“(新建Object)”，再填入新名称 => 分配新ID
        """
        dlg = tk.Toplevel(self)
        dlg.title("选择或新建 Object")
        center_window(dlg, self)

        # 收集所有 Object Region
        object_regions = [rg for rg in self.regions if rg.type == "object"]
        object_names = sorted([rg.name for rg in object_regions])
        # 下拉内容： (新建Object) + 其他名称
        choices = ["(新建Object)"] + object_names

        tk.Label(dlg, text="选择已有 Object 或新建：").grid(
            row=0, column=0, padx=5, pady=5, sticky="e"
        )
        var_choice = tk.StringVar(value=choices[0])
        opt_obj = tk.OptionMenu(dlg, var_choice, *choices)
        opt_obj.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        tk.Label(dlg, text="新名称(仅当选择新建时生效)：").grid(
            row=1, column=0, padx=5, pady=5, sticky="e"
        )
        var_newname = tk.StringVar()
        ent_new = tk.Entry(dlg, textvariable=var_newname)
        ent_new.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        # 用于存储创建好的/或复用的 region
        result_region = [None]  # 用列表包装，以便内部函数写入

        def do_ok():
            choice = var_choice.get()
            new_name = var_newname.get().strip()
            try:
                if choice == "(新建Object)":
                    # 新建 => new_name 必须非空 & 不重复
                    if not new_name:
                        raise ValueError("请填写新Object名称")
                    if self.find_object_by_name(new_name):
                        raise ValueError(f"Object名称'{new_name}'已存在")
                    # 校验选区位于同一个area
                    region_obj = self._create_new_object(new_name, cells_set)
                    result_region[0] = region_obj
                else:
                    # 复用 => choice 是已有 object 名
                    exist_obj_reg = self.find_object_by_name(choice)
                    if not exist_obj_reg:
                        raise ValueError(f"未找到Object '{choice}'(逻辑错误)")
                    # 校验选区网格都在 exist_obj_reg.parent_id(area)
                    self._reuse_object(exist_obj_reg, cells_set)
                    result_region[0] = exist_obj_reg
            except ValueError as e:
                messagebox.showerror("错误", str(e), parent=dlg)
                return
            messagebox.showinfo(
                "成功",
                f"已创建/复用 Object: {result_region[0].name}(ID={result_region[0].id})",
                parent=dlg,
            )
            dlg.destroy()

        tk.Button(dlg, text="确定", command=do_ok).grid(
            row=2, column=0, columnspan=2, pady=10
        )

        self.wait_window(dlg)
        if result_region[0]:
            self.redraw_all_cells()
            return result_region[0]
        else:
            raise ValueError("用户取消或未成功创建 Object")

    def _create_new_object(self, obj_name, cells_set):
        """
        创建一个新的 Object Region 并分配新 ID
        """
        # 检查选区都在同一个area
        a_id = None
        for r, c in cells_set:
            a = self.cell_info[r][c]["area"]
            if not a:
                raise ValueError("选区有格子不在任何Area中，无法创建Object")
            if a_id is None:
                a_id = a["id"]
            elif a["id"] != a_id:
                raise ValueError("选区跨多个Area，无法创建同一个Object")
            if self.cell_info[r][c]["object"]:
                raise ValueError("选区内已有Object，无法重复定义")

        obj_id = self.id_allocator.get_next_object_id()
        new_reg = Region("object", obj_id, obj_name, a_id, cells_set)
        self.regions.append(new_reg)
        # 更新 cell_info
        for r, c in cells_set:
            self.cell_info[r][c]["object"] = {"id": obj_id, "name": obj_name}
        return new_reg

    def _reuse_object(self, obj_reg, cells_set):
        """
        将选区网格并入已有 object(obj_reg)。
        前提：所有选区网格都在 obj_reg 的同一父级Area 下，否则报错。
        如果某格子已经有其他Object，报错(不可覆盖)。
        """
        # 先检查选区
        area_id = obj_reg.parent_id  # 该object的父级Area
        for r, c in cells_set:
            a = self.cell_info[r][c]["area"]
            if not a or a["id"] != area_id:
                raise ValueError("选区中有格子不在此Object的父级Area内，无法复用")
            if self.cell_info[r][c]["object"]:
                raise ValueError("选区中部分格子已有Object，无法覆盖复用")
        # 合并 cells
        for r, c in cells_set:
            obj_reg.cells.add((r, c))
            self.cell_info[r][c]["object"] = {"id": obj_reg.id, "name": obj_reg.name}

    def find_object_by_name(self, name):
        for rg in self.regions:
            if rg.type == "object" and rg.name == name:
                return rg
        return None

    # -------------------------------
    #  3.5 修改/删除 Region (Object 不重名)
    # -------------------------------
    def popup_modify_region(self, r, c, region):
        top = tk.Toplevel(self)
        top.title("修改/删除")
        center_window(top, self)

        if region:
            text = f"最低层级: {region.type} (ID={region.id}, name={region.name})"
        else:
            text = "该格子暂无层级"
        text += "\n碰撞: " + ("是" if self.cell_info[r][c]["collision"] else "否")
        lbl_info = tk.Label(top, text=text)
        lbl_info.pack(pady=5)

        btn_frame = tk.Frame(top)
        btn_frame.pack(pady=10)

        if region:
            tk.Button(
                btn_frame,
                text="重命名",
                command=lambda: self.rename_region_popup(region, top),
            ).grid(row=0, column=0, padx=5)
            tk.Button(
                btn_frame,
                text="删除",
                command=lambda: self.delete_region_confirm(region, top),
            ).grid(row=0, column=1, padx=5)

    def rename_region_popup(self, region, parent_window):
        top = tk.Toplevel(parent_window)
        top.title("重命名")
        center_window(top, parent_window)

        tk.Label(top, text="新名称：").pack(side="left", padx=5, pady=5)
        var_name = tk.StringVar(value=region.name)
        ent = tk.Entry(top, textvariable=var_name)
        ent.pack(side="left", padx=5, pady=5)

        def do_rename():
            new_name = var_name.get().strip()
            if not new_name:
                messagebox.showerror("错误", "名称不能为空", parent=top)
                return

            # 如果是object，需要检查重名
            if region.type == "object" and new_name != region.name:
                # 检查是否已存在
                if self.find_object_by_name(new_name):
                    messagebox.showerror(
                        "错误", f"Object名称 '{new_name}' 已存在", parent=top
                    )
                    return

            self.rename_region(region, new_name)
            messagebox.showinfo("成功", f"已重命名为 {new_name}", parent=top)
            top.destroy()

        tk.Button(top, text="确定", command=do_rename).pack(side="left", padx=5, pady=5)

    def delete_region_confirm(self, region, parent_window):
        yesno = messagebox.askyesno(
            "确认", f"确定删除 {region.type}(ID={region.id})？", parent=parent_window
        )
        if yesno:
            self.delete_region(region)
            messagebox.showinfo("删除", "已删除成功", parent=parent_window)
            parent_window.destroy()

    def rename_region(self, region, new_name):
        region.name = new_name
        for r, c in region.cells:
            if region.type == "sector" and self.cell_info[r][c]["sector"]:
                self.cell_info[r][c]["sector"]["name"] = new_name
            elif region.type == "area" and self.cell_info[r][c]["area"]:
                self.cell_info[r][c]["area"]["name"] = new_name
            elif region.type == "object" and self.cell_info[r][c]["object"]:
                self.cell_info[r][c]["object"]["name"] = new_name

        self.redraw_all_cells()

    def delete_region(self, region):
        to_remove = set()
        self.collect_sub_regions(region, to_remove)
        for rg in to_remove:
            if rg in self.regions:
                self.regions.remove(rg)
            for r, c in rg.cells:
                if rg.type == "object":
                    self.cell_info[r][c]["object"] = None
                elif rg.type == "area":
                    self.cell_info[r][c]["area"] = None
                elif rg.type == "sector":
                    self.cell_info[r][c]["sector"] = None
        self.redraw_all_cells()

    def collect_sub_regions(self, region, container):
        if region in container:
            return
        container.add(region)
        if region.type == "sector":
            for rg in self.regions:
                if (
                    rg not in container
                    and rg.type == "area"
                    and rg.parent_id == region.id
                ):
                    self.collect_sub_regions(rg, container)
        elif region.type == "area":
            for rg in self.regions:
                if (
                    rg not in container
                    and rg.type == "object"
                    and rg.parent_id == region.id
                ):
                    self.collect_sub_regions(rg, container)
        # object无下级

    # -------------------------------
    #  3.6 绘制 & 鼠标提示
    # -------------------------------
    def redraw_all_cells(self):
        self.canvas.delete("cell_fill", "collision_star")
        for r in range(self.rows):
            for c in range(self.cols):
                info = self.cell_info[r][c]
                color = "white"
                if info["object"]:
                    color = "#FF6666"
                elif info["area"]:
                    color = "#00994C"
                elif info["sector"]:
                    color = "#006666"

                x1 = c * self.cell_size
                y1 = r * self.cell_size
                x2 = x1 + self.cell_size
                y2 = y1 + self.cell_size
                self.canvas.create_rectangle(
                    x1, y1, x2, y2, fill=color, outline="", tags="cell_fill"
                )
                if info["collision"]:
                    cx = x1 + self.cell_size // 2
                    cy = y1 + self.cell_size // 2
                    self.canvas.create_text(
                        cx,
                        cy,
                        text="*",
                        fill="black",
                        font=("Arial", 14, "bold"),
                        tags="collision_star",
                    )

        # 重新画网格线
        for rr in range(self.rows + 1):
            y = rr * self.cell_size
            self.canvas.create_line(0, y, self.cols * self.cell_size, y, fill="#ccc")
        for cc in range(self.cols + 1):
            x = cc * self.cell_size
            self.canvas.create_line(x, 0, x, self.rows * self.cell_size, fill="#ccc")

    def on_mouse_move(self, event):
        r, c = self.coord_to_cell(event.x, event.y)
        if r is None or c is None:
            self.title("地图编辑器")
            return
        s = self.cell_info[r][c]["sector"]
        a = self.cell_info[r][c]["area"]
        o = self.cell_info[r][c]["object"]
        col = self.cell_info[r][c]["collision"]
        s_str = f"{s['name']}({s['id']})" if s else "无"
        a_str = f"{a['name']}({a['id']})" if a else "无"
        o_str = f"{o['name']}({o['id']})" if o else "无"
        c_str = "碰撞[*]" if col else "无碰撞"
        self.title(
            f"{self.world_name} |({r},{c})|Sector={s_str}|Area={a_str}|Object={o_str}|{c_str}"
        )

    def coord_to_cell(self, x, y):
        col = x // self.cell_size
        row = y // self.cell_size
        if 0 <= row < self.rows and 0 <= col < self.cols:
            return (row, col)
        return (None, None)

    def get_lowest_region_for_cell(self, r, c):
        info = self.cell_info[r][c]
        if info["object"]:
            return self.find_region_by_id(info["object"]["id"])
        elif info["area"]:
            return self.find_region_by_id(info["area"]["id"])
        elif info["sector"]:
            return self.find_region_by_id(info["sector"]["id"])
        else:
            return None

    def find_region_by_id(self, rid):
        for rg in self.regions:
            if rg.id == rid:
                return rg
        return None

    def sector_id_to_index(self, sid):
        if not (SECTOR_BASE <= sid <= 13000):
            raise ValueError("非法Sector ID")
        return (sid - SECTOR_BASE) // SECTOR_SIZE + 1

    # -------------------------------
    #  4. 保存 / 读取
    # -------------------------------
    def save_map(self):
        data = {
            "world_name": self.world_name,  # 将 world_name 也保存
            "allocator": self.id_allocator.get_state(),
            "regions": [rg.to_dict() for rg in self.regions],
            "collision": [
                [self.cell_info[r][c]["collision"] for c in range(self.cols)]
                for r in range(self.rows)
            ],
            "rows": self.rows,
            "cols": self.cols,
        }
        fpath = filedialog.asksaveasfilename(
            title="保存",
            defaultextension=".json",
            filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")],
        )
        if not fpath:
            return
        try:
            with open(fpath, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            messagebox.showinfo("保存成功", f"项目已保存到:\n{fpath}", parent=self)
        except Exception as e:
            messagebox.showerror("错误", f"保存失败:{e}", parent=self)

    def load_map(self):
        fpath = filedialog.askopenfilename(
            title="读取", filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")]
        )
        if not fpath or not os.path.exists(fpath):
            return
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            messagebox.showerror("错误", f"读取失败:{e}", parent=self)
            return

        # 还原
        self.regions.clear()
        self.world_name = data.get("world_name", "UnnamedWorld")
        alloc_state = data.get("allocator", {})
        self.id_allocator.set_state(
            alloc_state.get("area_counts", [0] * SECTOR_COUNT),
            alloc_state.get("object_count", 0),
        )

        # 还原region
        reg_list = data.get("regions", [])
        for rd in reg_list:
            rg = Region.from_dict(rd)
            self.regions.append(rg)

        # 重置 cell_info
        self.cell_info = [
            [
                {"sector": None, "area": None, "object": None, "collision": False}
                for _ in range(self.cols)
            ]
            for _ in range(self.rows)
        ]
        # 根据 region 重构
        for rg in self.regions:
            for r, c in rg.cells:
                if rg.type == "sector":
                    self.cell_info[r][c]["sector"] = {"id": rg.id, "name": rg.name}
                elif rg.type == "area":
                    self.cell_info[r][c]["area"] = {"id": rg.id, "name": rg.name}
                elif rg.type == "object":
                    self.cell_info[r][c]["object"] = {"id": rg.id, "name": rg.name}
        # 还原 collision
        coll_data = data.get("collision", [])
        for r in range(self.rows):
            for c in range(self.cols):
                if r < len(coll_data) and c < len(coll_data[r]):
                    self.cell_info[r][c]["collision"] = coll_data[r][c]

        self.redraw_all_cells()
        messagebox.showinfo(
            "读取成功",
            f"已加载项目，World名称={self.world_name}\n文件={os.path.basename(fpath)}",
            parent=self,
        )

    # -------------------------------
    #  5. 导出CSV (使用 world_name)
    # -------------------------------
    def export_csv_files(self):
        """
        导出 sector_maze.csv/area_maze.csv/object_maze.csv/collision_maze.csv
        以及 sector_blocks.csv/area_blocks.csv/object_blocks.csv
        不再重复输出(blocks根据region一次输出一行)
        """
        dir_path = filedialog.askdirectory(title="选择导出CSV的文件夹", parent=self)
        if not dir_path:
            return
        try:
            self.export_maze_csv(os.path.join(dir_path, "sector_maze.csv"), "sector")
            self.export_maze_csv(os.path.join(dir_path, "area_maze.csv"), "area")
            self.export_maze_csv(os.path.join(dir_path, "object_maze.csv"), "object")
            self.export_maze_csv(
                os.path.join(dir_path, "collision_maze.csv"), "collision"
            )

            self.export_blocks_csv(
                os.path.join(dir_path, "sector_blocks.csv"), "sector"
            )
            self.export_blocks_csv(os.path.join(dir_path, "area_blocks.csv"), "area")
            self.export_blocks_csv(
                os.path.join(dir_path, "object_blocks.csv"), "object"
            )

            messagebox.showinfo("导出成功", f"CSV已输出到:\n{dir_path}", parent=self)
        except Exception as e:
            messagebox.showerror("错误", f"导出失败:{e}", parent=self)

    def export_maze_csv(self, filepath, layer):
        import csv

        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            for r in range(self.rows):
                row_data = []
                for c in range(self.cols):
                    if layer == "collision":
                        val = COLLISION_ID if self.cell_info[r][c]["collision"] else 0
                    else:
                        info = self.cell_info[r][c][layer]
                        val = info["id"] if info else 0
                    row_data.append(val)
                writer.writerow(row_data)

    def export_blocks_csv(self, filepath, layer):
        """
        对某种类型的 region，每个 region 输出一行 => 避免重复
        格式:
          sector => [id, worldName, sectorName]
          area   => [id, worldName, sectorName, areaName]
          object => [id, worldName, sectorName, areaName, objectName]
        """
        import csv

        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            all_r = sorted(self.regions, key=lambda x: x.id)
            for rg in all_r:
                if rg.type == layer:
                    row_data = self.build_hierarchy_row(rg)
                    writer.writerow(row_data)

    def build_hierarchy_row(self, region):
        """
        sector => [id, worldName, sectorName]
        area   => [id, worldName, sectorName, areaName]
        object => [id, worldName, sectorName, areaName, objectName]
        """
        # worldName 用 self.world_name
        if region.type == "sector":
            return [region.id, self.world_name, region.name]
        elif region.type == "area":
            sec_reg = self.find_region_by_id(region.parent_id)
            sec_name = sec_reg.name if sec_reg else "未知Sector"
            return [region.id, self.world_name, sec_name, region.name]
        elif region.type == "object":
            area_reg = self.find_region_by_id(region.parent_id)
            area_name = area_reg.name if area_reg else "未知Area"
            sec_id = area_reg.parent_id if area_reg else None
            sec_reg = self.find_region_by_id(sec_id) if sec_id else None
            sec_name = sec_reg.name if sec_reg else "未知Sector"
            return [region.id, self.world_name, sec_name, area_name, region.name]
        else:
            return [region.id, self.world_name, "???"]


# -------------------------------
#  启动
# -------------------------------
if __name__ == "__main__":
    app = MapEditorUI(rows=60, cols=80, cell_size=15)
    app.mainloop()
