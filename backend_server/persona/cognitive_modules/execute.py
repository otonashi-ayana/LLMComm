"""
Author: Joon Sung Park (joonspk@stanford.edu)

File: execute.py
Description: This defines the "Act" module for generative agents. 
"""

import sys
import random

sys.path.append("../../")

from global_methods import *
from path_finder import *
from utils import *


def execute(persona, maze, personas, plan):
    """
    Given a plan (action's string address), we execute the plan (actually
    outputs the cell coordinate path and the next coordinate for the
    persona).

    INPUT:
      persona: Current <Persona> instance.
      maze: An instance of current <Maze>.
      personas: A dictionary of all personas in the world.
      plan: This is a string address of the action we need to execute.
         It comes in the form of "{world}:{sector}:{arena}:{game_objects}".
         It is important that you access this without doing negative
         indexing (e.g., [-1]) because the latter address elements may not be
         present in some cases.
         e.g., "dolores double studio:double studio:bedroom 1:bed"

    OUTPUT:
      execution
    """
    if "<random>" in plan and persona.direct_mem.planned_path == []:
        persona.direct_mem.act_path_set = False

    # <act_path_set> is set to True if the path is set for the current action.
    # It is False otherwise, and means we need to construct a new path.
    if not persona.direct_mem.act_path_set:
        # <target_cells> is a list of cell coordinates where the persona may go
        # to execute the current action. The goal is to pick one of them.
        target_cells = None

        print("<execute> - plan:", plan)

        if "<persona>" in plan:
            # Executing persona-persona interaction.
            target_p_cell = personas[
                plan.split("<persona>")[-1].strip()
            ].direct_mem.curr_cell
            potential_path = path_finder(
                maze.collision_2d,
                persona.direct_mem.curr_cell,
                target_p_cell,
                collision_block_id,
            )
            if len(potential_path) <= 2:
                target_cells = [potential_path[0]]
            else:
                potential_1 = path_finder(
                    maze.collision_2d,
                    persona.direct_mem.curr_cell,
                    potential_path[int(len(potential_path) / 2)],
                    collision_block_id,
                )
                potential_2 = path_finder(
                    maze.collision_2d,
                    persona.direct_mem.curr_cell,
                    potential_path[int(len(potential_path) / 2) + 1],
                    collision_block_id,
                )
                if len(potential_1) <= len(potential_2):
                    target_cells = [potential_path[int(len(potential_path) / 2)]]
                else:
                    target_cells = [potential_path[int(len(potential_path) / 2 + 1)]]

        elif "<等待>" in plan:
            # Executing interaction where the persona has decided to wait before
            # executing their action.
            x = int(plan.split()[1])
            y = int(plan.split()[2])
            target_cells = [[x, y]]

        elif "<random>" in plan:
            # Executing a random location action.
            plan = ":".join(plan.split(":")[:-1])
            target_cells = maze.cells_of_addr[plan]
            target_cells = random.sample(list(target_cells), 1)

        else:
            # This is our default execution. We simply take the persona to the
            # location where the current action is taking place.
            # Retrieve the target addresses. Again, plan is an action address in its
            # string form. <maze.cells_of_addr> takes this and returns candidate
            # coordinates.
            if plan not in maze.cells_of_addr:
                print("<execute> - plan not in maze.cells_of_addr", plan)
                print("<execute> - maze.cells_of_addr:", maze.cells_of_addr.keys())
                # raise Exception("<execute>: Plan not in maze.cells_of_addr")
                target_cells = maze.cells_of_addr[
                    "幸福苑小区:社区公园:社区公园:公园空地"
                ]
            else:
                target_cells = maze.cells_of_addr[plan]
                # print("target_cells:", target_cells)

        # There are sometimes more than one cell returned from this (e.g., a tabe
        # may stretch many coordinates). So, we sample a few here. And from that
        # random sample, we will take the closest ones.
        if len(target_cells) < 4:
            target_cells = random.sample(list(target_cells), len(target_cells))
        else:
            target_cells = random.sample(list(target_cells), 4)
        # If possible, we want personas to occupy different cells when they are
        # headed to the same location on the maze. It is ok if they end up on the
        # same time, but we try to lower that probability.
        # We take care of that overlap here.
        persona_name_set = set(personas.keys())
        new_target_cells = []
        for i in target_cells:
            curr_event_set = maze.access_cell(i)["events"]
            pass_curr_cell = False
            for j in curr_event_set:
                if j[0] in persona_name_set:
                    pass_curr_cell = True
            if not pass_curr_cell:
                new_target_cells += [i]
        if len(new_target_cells) == 0:
            new_target_cells = target_cells
        target_cells = new_target_cells

        # Now that we've identified the target cell, we find the shortest path to
        # one of the target cells.
        curr_cell = persona.direct_mem.curr_cell
        closest_target_cell = None
        path = None
        for i in target_cells:
            # path_finder takes a collision_mze and the curr_cell coordinate as
            # an input, and returns a list of coordinate tuples that becomes the
            # path.
            # e.g., [(0, 1), (1, 1), (1, 2), (1, 3), (1, 4)...]
            curr_path = path_finder(maze.collision_2d, curr_cell, i, collision_block_id)
            if not closest_target_cell:
                closest_target_cell = i
                path = curr_path
            elif len(curr_path) < len(path):
                closest_target_cell = i
                path = curr_path

        # Actually setting the <planned_path> and <act_path_set>. We cut the
        # first element in the planned_path because it includes the curr_cell.
        persona.direct_mem.planned_path = path[1:]
        persona.direct_mem.act_path_set = True

    # Setting up the next immediate step. We stay at our curr_cell if there is
    # no <planned_path> left, but otherwise, we go to the next cell in the path.
    ret = persona.direct_mem.curr_cell
    if persona.direct_mem.planned_path:
        ret = persona.direct_mem.planned_path[0]
        persona.direct_mem.planned_path = persona.direct_mem.planned_path[1:]

    description = (
        f"在 {persona.direct_mem.act_address}，{persona.direct_mem.act_description}"
    )

    execution = ret, description  # persona.direct_mem.act_pronunciatio,
    return execution


if __name__ == "__main__":
    pass
