# COMP30024 Artificial Intelligence, Semester 1 2026
# Project Part A: Single Player Cascade
import heapq
from itertools import count

from .core import CellState, Coord, Direction, Action, MoveAction, EatAction, CascadeAction, BOARD_N, PlayerColor
from .utils import render_board

RED = PlayerColor.RED
BLUE = PlayerColor.BLUE

EMPTY = 0
RED_C = 1
BLUE_C = 2

DIRS = [(d, d.r, d.c) for d in Direction]

RC_TABLE = [divmod(i, BOARD_N) for i in range(BOARD_N * BOARD_N)]
COORD_TABLE = [Coord(r, c) for r, c in RC_TABLE]

def encode(board: dict):
    state = [EMPTY] * (BOARD_N * BOARD_N)
    blue_count = 0
    
    for coord, cell in board.items():
        if cell.is_empty:
            continue
            
        idx = coord.r * BOARD_N + coord.c
        
        if cell.color == BLUE:
            state[idx] = (BLUE_C, cell.height)
            blue_count += 1
        else:
            state[idx] = (RED_C, cell.height)
            
    return tuple(state), blue_count

def decode(state: tuple):
    board = {}
    for i, cell in enumerate(state):
        if cell == EMPTY:
            continue
        
        color_int, height = cell
        coord = COORD_TABLE[i]

        board[coord] = CellState(RED if color_int == RED_C else BLUE, height)
    return board

def apply_cascade(state: tuple, i: int, r: int, c: int, dr: int, dc: int, height: int):
    new = list(state)
    new[i] = EMPTY
    blue_delta = 0

    for step in range(1, height + 1):
        cr, cc = r + dr * step, c + dc * step
        if not (0 <= cr < BOARD_N and 0 <= cc < BOARD_N):
            continue
 
        idx = cr * BOARD_N + cc

        if new[idx] != EMPTY:
            er, ec = cr, cc
            while 0 <= er + dr < BOARD_N and 0 <= ec + dc < BOARD_N and \
                  new[(er + dr) * BOARD_N + (ec + dc)] != EMPTY:
                er += dr
                ec += dc

            curr_r, curr_c = er, ec
            while True:
                curr_idx = curr_r * BOARD_N + curr_c
                next_r, next_c = curr_r + dr, curr_c + dc
                
                if 0 <= next_r < BOARD_N and 0 <= next_c < BOARD_N:
                    new[next_r * BOARD_N + next_c] = new[curr_idx]
                else:
                    if new[curr_idx][0] == BLUE_C:
                        blue_delta -= 1
                
                if (curr_r, curr_c) == (cr, cc):
                    break
                curr_r, curr_c = curr_r - dr, curr_c - dc

        elif state[idx] != EMPTY and state[idx][0] == BLUE_C:
             blue_delta -= 1
             
        new[idx] = (RED_C, 1)
 
    return tuple(new), blue_delta

def heuristic(state: tuple, blue_count: int):
    if blue_count == 0:
        return 0

    red_pts = [COORD_TABLE[i] for i, cell in enumerate(state) if cell != EMPTY and cell[0] == RED_C]
    if not red_pts: 
        return 999 

    blue_gen = (COORD_TABLE[i] for i, cell in enumerate(state) if cell != EMPTY and cell[0] == BLUE_C)

    max_min_dist = 0
    for b in blue_gen:
        d = min(abs(b.r - r.r) + abs(b.c - r.c) for r in red_pts)
        if d > max_min_dist:
            max_min_dist = d

    return max(blue_count, max_min_dist)
    
 
def get_moves(state: tuple, blues: int):
    results = []
    for i, cell in enumerate(state):
        if cell == EMPTY or cell[0] != RED_C:
            continue

        _, height = cell
        coord = COORD_TABLE[i]

        for direction, dr, dc in DIRS:
            nr, nc = coord.r + dr, coord.c + dc

            if 0 <= nr < BOARD_N and 0 <= nc < BOARD_N:
                idx = nr * BOARD_N + nc
                target = state[idx]

                if target == EMPTY or target[0] == RED_C:
                    new = list(state)
                    new[i] = EMPTY
                    new[idx] = (RED_C, height + (target[1] if target != EMPTY else 0))
                    results.append((MoveAction(coord, direction), tuple(new), blues))

                elif height >= target[1]: 
                    new = list(state)
                    new[i] = EMPTY
                    new[idx] = (RED_C, height)
                    results.append((EatAction(coord, direction), tuple(new), blues - 1))

            if height >= 2:
                new_state, b_delta = apply_cascade(state, i, coord.r, coord.c, dr, dc, height)
                results.append((CascadeAction(coord, direction), new_state, blues + b_delta))
                
    return results

def search(board: dict[Coord, CellState]) -> list[Action] | None:
    print(render_board(board, ansi=True))
    tie = count()
 
    initial_state, initial_blues = encode(board)
 
    g_best = {initial_state: 0}
    parent: dict[tuple, tuple | None] = {initial_state: None}
 
    h0   = heuristic(initial_state, initial_blues)
    heap = [(h0, 0, next(tie), initial_state, initial_blues)]
 
    while heap:
        f, g, _, state, blues = heapq.heappop(heap)
 
        if g > g_best.get(state, 10 ** 9):
            continue

        if blues == 0:
            path = []
            cur  = state
            while parent[cur] is not None:
                prev, action = parent[cur]
                path.append(action)
                cur = prev
            path.reverse()
            return path
 
        for action, next_state, new_blues in get_moves(state, blues):
            new_g = g + 1
            if new_g >= g_best.get(next_state, 10 ** 9):
                continue
            g_best[next_state] = new_g
            parent[next_state] = (state, action)
            new_f = new_g + heuristic(next_state, new_blues)
            heapq.heappush(heap, (new_f, new_g, next(tie), next_state, new_blues))
 
    return None