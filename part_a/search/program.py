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
    state = [EMPTY] * 64
    blue_count = 0
    for coord, cell in board.items():
        if cell.color == BLUE:
            state[coord.r * BOARD_N + coord.c] = (BLUE_C, cell.height)
            blue_count += 1
        else:
            state[coord.r * BOARD_N + coord.c] = (RED_C, cell.height)
    return tuple(state), blue_count

def decode(state: tuple):
    board = {}
    for i, cell in enumerate(state):
        if cell == EMPTY:
            continue
        color_int, height = cell
        r, c = RC_TABLE[i]
        board[Coord(r, c)] = CellState(RED if color_int == RED_C else BLUE, height)
    return board

def in_bounds(r: int, c: int):
    return 0 <= r < BOARD_N and 0 <= c < BOARD_N

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
            chain = []
            pr, pc = cr, cc
            while 0 <= pr < BOARD_N and 0 <= pc < BOARD_N and new[pr * BOARD_N + pc] != EMPTY:
                chain.append(pr * BOARD_N + pc)
                pr += dr
                pc += dc
            for cidx in reversed(chain):
                pr2, pc2 = RC_TABLE[cidx]
                npr, npc = pr2 + dr, pc2 + dc
                if 0 <= npr < BOARD_N and 0 <= npc < BOARD_N:
                    new[npr * BOARD_N + npc] = new[cidx]
                else:
                    # Stack pushed off the board — update blue count if it was blue
                    if new[cidx][0] == BLUE_C:
                        blue_delta -= 1
                new[cidx] = EMPTY
 
        new[idx] = (RED_C, 1)
 
    return tuple(new), blue_delta

def is_solvable(board: dict) -> bool:
    total_red_tokens = sum(cs.height for cs in board.values() if cs.color == RED)
    for coord, cs in board.items():
        if cs.color != BLUE:
            continue
        can_eat        = total_red_tokens >= cs.height
        dist_to_edge_r = min(coord.r, BOARD_N - 1 - coord.r)
        dist_to_edge_c = min(coord.c, BOARD_N - 1 - coord.c)
        can_push_off   = (total_red_tokens >= dist_to_edge_r or
                          total_red_tokens >= dist_to_edge_c)
        if not can_eat and not can_push_off:
            return False
    return True

_heuristic_cache: dict[tuple, int] = {}

def heuristic(state: tuple, blue_count: int):
    if blue_count == 0:
        return 0
    
    cached = _heuristic_cache.get(state)
    if cached is not None:
        return cached
    
    blue_positions = []
    red_positions = []

    for i, cell in enumerate(state):
        if cell == EMPTY:
            continue
        if cell[0] == BLUE_C:
            blue_positions.append(RC_TABLE[i])
        else:
            red_positions.append(RC_TABLE[i])
    
    if not red_positions:
        return 10 ** 9
    
    available_reds = list(red_positions)
    total_cost = 0

    blue_with_dist = sorted(
    ((min(abs(br - rr) + abs(bc - rc) for rr, rc in available_reds), br, bc)
     for br, bc in blue_positions),
    reverse=True
)

    for _, br, bc in blue_with_dist:
        best_idx = min(range(len(available_reds)),
                       key=lambda k: abs(br - available_reds[k][0]) + abs(bc - available_reds[k][1])
                       )
        rr, rc = available_reds[best_idx]
        dist = max(abs(br - rr) + abs(bc - rc), 1)
        total_cost += dist

        if len(available_reds) > 1:
            available_reds.pop(best_idx)

    result = max(blue_count, total_cost)
    _heuristic_cache[state] = result
    return result
    
 
def get_moves(state: tuple, blues: int):
    results = []
 
    for i, cell in enumerate(state):
        if cell == EMPTY or cell[0] == BLUE_C:
            continue
 
        _, height = cell
        r, c  = RC_TABLE[i]
        coord = COORD_TABLE[i]
 
        for direction, dr, dc in DIRS:
            nr, nc = r + dr, c + dc
 
            if 0 <= nr < BOARD_N and 0 <= nc < BOARD_N:
                j           = nr * BOARD_N + nc
                target_cell = state[j]

                if target_cell == EMPTY or target_cell[0] == RED_C:
                    new = list(state)
                    new[i] = EMPTY
                    new[j] = (RED_C, height + (target_cell[1] if target_cell != EMPTY else 0))
                    results.append((MoveAction(coord, direction), tuple(new), blues))

                elif target_cell[0] == BLUE_C and height >= target_cell[1]:
                    new = list(state)
                    new[i] = EMPTY
                    new[j] = (RED_C, height)
                    results.append((EatAction(coord, direction), tuple(new), blues - 1))

            if height >= 2:
                new_state, blue_delta = apply_cascade(state, i, r, c, dr, dc, height)
                results.append((CascadeAction(coord, direction), new_state, blues + blue_delta))
 
    return results

def search(board: dict[Coord, CellState]) -> list[Action] | None:
    print(render_board(board, ansi=True))
    tie = count()
 
    if not is_solvable(board):
        return None
 
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