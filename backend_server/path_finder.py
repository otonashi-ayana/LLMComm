"""
Author: Joon Sung Park (joonspk@stanford.edu)

File: path_finder.py
Description: Implements various path finding functions for generative agents.
Some of the functions are defunct.
"""

import numpy as np
import random
from global_methods import *


def print_maze(maze):
    for row in maze:
        for item in row:
            print(item, end="")
        print()


def path_finder_v1(maze, start, end, collision_block_char, verbose=False):
    def prepare_maze(maze, start, end):
        maze[start[0]][start[1]] = "S"
        maze[end[0]][end[1]] = "E"
        return maze

    def find_start(maze):
        for row in range(len(maze)):
            for col in range(len(maze[0])):
                if maze[row][col] == "S":
                    return row, col

    def is_valid_position(maze, pos_r, pos_c):
        if pos_r < 0 or pos_c < 0:
            return False
        if pos_r >= len(maze) or pos_c >= len(maze[0]):
            return False
        if maze[pos_r][pos_c] in " E":
            return True
        return False

    def solve_maze(maze, start, verbose=False):
        path = []
        # We use a Python list as a stack - then we have push operations as
        # append, and pop as pop.
        stack = []
        # Add the entry point (as a tuple)
        stack.append(start)
        # Go through the stack as long as there are elements
        while len(stack) > 0:
            pos_r, pos_c = stack.pop()
            if verbose:
                print("Current position", pos_r, pos_c)
            if maze[pos_r][pos_c] == "E":
                path += [(pos_r, pos_c)]
                return path
            if maze[pos_r][pos_c] == "X":
                # Already visited
                continue
            # Mark position as visited
            maze[pos_r][pos_c] = "X"
            path += [(pos_r, pos_c)]
            # Check for all possible positions and add if possible
            if is_valid_position(maze, pos_r - 1, pos_c):
                stack.append((pos_r - 1, pos_c))
            if is_valid_position(maze, pos_r + 1, pos_c):
                stack.append((pos_r + 1, pos_c))
            if is_valid_position(maze, pos_r, pos_c - 1):
                stack.append((pos_r, pos_c - 1))
            if is_valid_position(maze, pos_r, pos_c + 1):
                stack.append((pos_r, pos_c + 1))

            # To follow the maze
            if verbose:
                print("Stack:", stack)
                print_maze(maze)

        # We didn't find a path, hence we do not need to return the path
        return False

    # clean maze
    new_maze = []
    for row in maze:
        new_row = []
        for j in row:
            if j == collision_block_char:
                new_row += ["#"]
            else:
                new_row += [" "]
        new_maze += [new_row]

    maze = new_maze

    maze = prepare_maze(maze, start, end)
    start = find_start(maze)
    path = solve_maze(maze, start, verbose)
    return path


def path_finder_v2(a, start, end, collision_block_char, verbose=False):
    def make_step(m, k):
        for i in range(len(m)):
            for j in range(len(m[i])):
                if m[i][j] == k:
                    if i > 0 and m[i - 1][j] == 0 and a[i - 1][j] == 0:
                        m[i - 1][j] = k + 1
                    if j > 0 and m[i][j - 1] == 0 and a[i][j - 1] == 0:
                        m[i][j - 1] = k + 1
                    if i < len(m) - 1 and m[i + 1][j] == 0 and a[i + 1][j] == 0:
                        m[i + 1][j] = k + 1
                    if j < len(m[i]) - 1 and m[i][j + 1] == 0 and a[i][j + 1] == 0:
                        m[i][j + 1] = k + 1

    new_maze = []
    for row in a:
        new_row = []
        for j in row:
            if j == collision_block_char:
                new_row += [1]
            else:
                new_row += [0]
        new_maze += [new_row]
    a = new_maze

    m = []
    for i in range(len(a)):
        m.append([])
        for j in range(len(a[i])):
            m[-1].append(0)
    i, j = start
    m[i][j] = 1

    k = 0
    except_handle = 150
    while m[end[0]][end[1]] == 0:
        k += 1
        make_step(m, k)

        if except_handle == 0:
            break
        except_handle -= 1

    i, j = end
    k = m[i][j]
    the_path = [(i, j)]
    while k > 1:
        if i > 0 and m[i - 1][j] == k - 1:
            i, j = i - 1, j
            the_path.append((i, j))
            k -= 1
        elif j > 0 and m[i][j - 1] == k - 1:
            i, j = i, j - 1
            the_path.append((i, j))
            k -= 1
        elif i < len(m) - 1 and m[i + 1][j] == k - 1:
            i, j = i + 1, j
            the_path.append((i, j))
            k -= 1
        elif j < len(m[i]) - 1 and m[i][j + 1] == k - 1:
            i, j = i, j + 1
            the_path.append((i, j))
            k -= 1

    the_path.reverse()
    return the_path


def generate_walk_around_path(
    maze, start, collision_block_char, max_steps=15, min_steps=5
):
    """
    生成一个随机散步路径，可能是来回踱步、环形或其他自然走动模式

    参数:
        maze: 2D地图数组
        start: 起点坐标 (x, y)
        collision_block_char: 碰撞检测使用的字符
        max_steps: 最大步数
        min_steps: 最小步数

    返回:
        随机散步路径坐标列表，包括起点
    """
    # 获取地图尺寸
    height = len(maze)
    width = len(maze[0]) if height > 0 else 0

    # 定义方向: 上、右、下、左
    directions = [(0, -1), (1, 0), (0, 1), (-1, 0)]

    # 初始化路径，包含起点
    path = [start]
    current = start

    # 随机决定步数，在min_steps和max_steps之间
    steps = random.randint(min_steps, max_steps)

    # 随机选择路径类型: 0=来回踱步, 1=环形, 2=随机走动
    path_type = random.randint(0, 2)

    # 为环形路径存储方向历史
    direction_history = []

    for _ in range(steps):
        valid_moves = []

        # 根据不同的路径类型生成下一步
        if path_type == 0:  # 来回踱步
            # 主要在两个方向上来回走动
            main_dirs = random.sample(directions, 2)
            for dx, dy in main_dirs:
                nx, ny = current[0] + dx, current[1] + dy
                # 检查新位置是否有效
                if (
                    0 <= nx < width
                    and 0 <= ny < height
                    and maze[ny][nx] != collision_block_char
                ):
                    valid_moves.append((nx, ny))

        elif path_type == 1:  # 环形路径
            if not direction_history:
                # 第一步，随机选择方向
                dir_idx = random.randint(0, 3)
                direction_history.append(dir_idx)
            else:
                # 尝试保持相同或邻近方向，形成环形
                last_dir = direction_history[-1]
                # 更倾向于选择相同或相邻方向
                dir_options = [(last_dir - 1) % 4, last_dir, (last_dir + 1) % 4]
                weights = [0.2, 0.6, 0.2]
                dir_idx = random.choices(dir_options, weights=weights)[0]
                direction_history.append(dir_idx)

            dx, dy = directions[dir_idx]
            nx, ny = current[0] + dx, current[1] + dy

            # 如果这个方向不可行，尝试其他方向
            if (
                0 <= nx < width
                and 0 <= ny < height
                and maze[ny][nx] != collision_block_char
            ):
                valid_moves.append((nx, ny))
            else:
                # 所有方向都试一遍
                for dx, dy in directions:
                    nx, ny = current[0] + dx, current[1] + dy
                    if (
                        0 <= nx < width
                        and 0 <= ny < height
                        and maze[ny][nx] != collision_block_char
                    ):
                        valid_moves.append((nx, ny))

        else:  # 随机走动
            # 尝试所有四个方向
            for dx, dy in directions:
                nx, ny = current[0] + dx, current[1] + dy
                if (
                    0 <= nx < width
                    and 0 <= ny < height
                    and maze[ny][nx] != collision_block_char
                ):
                    valid_moves.append((nx, ny))

        # 如果没有有效的移动，结束路径
        if not valid_moves:
            break

        # 随机选择下一个位置
        next_pos = random.choice(valid_moves)
        path.append(next_pos)
        current = next_pos

    # 确保路径结束后回到起点附近或可以回到起点
    if len(path) > 1 and random.random() > 0.3:  # 70%的概率尝试回到起点附近
        # 尝试找到从当前位置到起点的路径
        try:
            return_path = path_finder_v2(maze, current, start, collision_block_char)
            if return_path and len(return_path) > 1:
                # 移除重复的当前位置
                path.extend(return_path[1:])
        except:
            # 如果寻路失败，就不添加返回路径
            pass

    return path


def path_finder(
    maze, start, end, collision_block_char, verbose=False, walk_around=False
):
    """
    寻找从起点到终点的路径，或生成随机散步路径

    参数:
        maze: 2D地图数组
        start: 起点坐标 (x, y)
        end: 终点坐标 (x, y)
        collision_block_char: 碰撞检测使用的字符
        verbose: 是否打印详细信息
        walk_around: 是否生成随机散步路径

    返回:
        路径坐标列表
    """
    # 如果是随处走动模式
    if walk_around:
        return generate_walk_around_path(maze, start, collision_block_char)

    # EMERGENCY PATCH
    start = (start[1], start[0])
    end = (end[1], end[0])
    # END EMERGENCY PATCH

    path = path_finder_v2(maze, start, end, collision_block_char, verbose)

    new_path = []
    for i in path:
        new_path += [(i[1], i[0])]
    path = new_path

    return path


def closest_coordinate(curr_coordinate, target_coordinates):
    min_dist = None
    closest_coordinate = None
    for coordinate in target_coordinates:
        a = np.array(coordinate)
        b = np.array(curr_coordinate)
        dist = abs(np.linalg.norm(a - b))
        if not closest_coordinate:
            min_dist = dist
            closest_coordinate = coordinate
        else:
            if min_dist > dist:
                min_dist = dist
                closest_coordinate = coordinate

    return closest_coordinate


def path_finder_2(maze, start, end, collision_block_char, verbose=False):
    # start => persona_a
    # end => persona_b
    start = list(start)
    end = list(end)

    t_top = (end[0], end[1] + 1)
    t_bottom = (end[0], end[1] - 1)
    t_left = (end[0] - 1, end[1])
    t_right = (end[0] + 1, end[1])
    pot_target_coordinates = [t_top, t_bottom, t_left, t_right]

    maze_width = len(maze[0])
    maze_height = len(maze)
    target_coordinates = []
    for coordinate in pot_target_coordinates:
        if (
            coordinate[0] >= 0
            and coordinate[0] < maze_width
            and coordinate[1] >= 0
            and coordinate[1] < maze_height
        ):
            target_coordinates += [coordinate]

    target_coordinate = closest_coordinate(start, target_coordinates)

    path = path_finder(
        maze, start, target_coordinate, collision_block_char, verbose=False
    )
    return path


def path_finder_3(maze, start, end, collision_block_char, verbose=False):
    # start => persona_a
    # end => persona_b

    curr_path = path_finder(maze, start, end, collision_block_char, verbose=False)
    if len(curr_path) <= 2:
        return []
    else:
        a_path = curr_path[: int(len(curr_path) / 2)]
        b_path = curr_path[int(len(curr_path) / 2) - 1 :]

    b_path.reverse()

    print(a_path)
    print(b_path)
    return a_path, b_path
