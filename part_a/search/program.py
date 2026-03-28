# COMP30024 Artificial Intelligence, Semester 1 2026
# Project Part A: Single Player Cascade
import heapq
from operator import __add__

from .core import CellState, Coord, Direction, Action, MoveAction, EatAction, CascadeAction, BOARD_N, PlayerColor
from .utils import render_board

RED, BLUE = PlayerColor.RED.value, PlayerColor.BLUE.value

DIRS: list[tuple[Direction, int, int]] = [
    (d, d.value.r, d.value.c) for d in Direction
]

def encode(board: dict):
    return tuple(sorted(
        (coord.r, coord.c, cell.color.value, cell.height)
        for coord, cell in board.items()
    ))

def decode(enc: tuple):
    return {
        Coord(r, c): CellState(
            PlayerColor.RED if col == RED else PlayerColor.BLUE, h
        )
        for r, c, col, h in enc
    }

def in_bounds(r: int, c: int):
    return 0 <= r < BOARD_N and 0 <= c < BOARD_N

def blue_count(enc: tuple):
    return sum(1 for _, _, col, _ in enc if col == BLUE)

def apply_move(board: dict, src: Coord, dir: Direction):
    dest = src + dir
    new_board = dict(board)
    moving_stack = new_board.pop(src)
    if dest in new_board:
        target = new_board[dest]
        if target.color == PlayerColor.RED:
            new_board[dest] = CellState(PlayerColor.RED, moving_stack.height + target.height)
        else:
            new_board[dest] = moving_stack
    else:
        new_board[dest] = moving_stack
    return new_board

def push_stack(board: dict, coord: Coord, dr: int, dc: int):
    """Push a stack in the given direction, moving it one cell and pushing any stacks in the way."""
    stack = board.get(coord)
    if stack is None:
        return
    nr, nc = coord.r + dr, coord.c + dc
    if not in_bounds(nr, nc):
        del board[coord]
        return
    next_coord = Coord(nr, nc)
    push_stack(board, next_coord, dr, dc)
    del board[coord]
    board[next_coord] = stack

def apply_cascade(board: dict, src: Coord, direction: Direction):
    new_board = dict(board)
    h = new_board.pop(src).height
    dr, dc = direction.value.r, direction.value.c
 
    for i in range(1, h + 1):
        pr, pc = src.r + dr * i, src.c + dc * i
        if not in_bounds(pr, pc):
            continue
        place = Coord(pr, pc)
        push_stack(new_board, place, dr, dc)
        new_board[place] = CellState(PlayerColor.RED, 1)
 
    return new_board

def blue_is_pushable_off_board(blue_coord: Coord, board: dict, total_red_tokens: int) -> bool:
    # checks if height is enough to cascade the blue token off the board
    blue_dist_row = min(blue_coord.r, abs(BOARD_N - 1 - blue_coord.r))
    blue_dist_col = min(blue_coord.c, abs(BOARD_N - 1 - blue_coord.c))
    if total_red_tokens >= blue_dist_row or total_red_tokens >= blue_dist_col:
        return True
    return False


def is_solvable(board: dict):
    """Check if board is solvable either by eating or cascading"""
    total_red_tokens = sum(cs.height for cs in board.values() if cs.color == PlayerColor.RED)

    for coord, cs in board.items():
        if cs.color != PlayerColor.BLUE:
            continue
        can_eat = total_red_tokens >= cs.height
        can_push = blue_is_pushable_off_board(coord, board, total_red_tokens)
        if not can_eat and not can_push:
            return False

    return True

def heuristic(board: dict):
    blue_coords = []
    red_coords = []

    for coord, cs in board.items():
        if cs.color == PlayerColor.BLUE:
            blue_coords.append(coord)
        else:
            red_coords.append(coord)

    n = len(blue_coords)
    if n == 0:
        return 0
    if not red_coords:
        return 10 ** 9

    max_dist_cost = 0
    for bc in blue_coords:
        min_d = min(
            abs(bc.r - rc.r) + abs(bc.c - rc.c) for rc in red_coords
        )
        cost = max(min_d, 1)
        max_dist_cost = max(max_dist_cost, cost)

    return max(n, max_dist_cost)
 
def possible_actions(board: dict):
    return 

def search(board: dict[Coord, CellState]) -> list[Action] | None:
    print(render_board(board, ansi=True))

    if not is_solvable(board):
        return None
    
    node_queue = []
    visited = set()

    ## adding all red tokens to create starting queue
    for coord,cs in board.items():
        if cs.color == PlayerColor.RED:
            heapq.heappush(node_queue, (heuristic(board), 0, encode(board), [])) ## item (f, g, state, path)
            continue

    while node_queue:
        f, g, enc, path = heapq.heappop(node_queue)

        if enc in visited:
            continue
        visited.add(enc)

        ## no blue counters left, return path
        if blue_count(enc) == 0:
            return path
        
        ## check all possible actions for current board state and add to queue
        for action, new_board in possible_actions(decode(enc)):
            new_enc = encode(new_board)
            ## check if new state has already been visited or is a duplicate
            if new_enc in visited or new_enc==enc:
                continue

            new_g = g + 1
            new_f = new_g + heuristic(decode(new_enc))
            new_path = path + [action]
            heapq.heappush(node_queue, (new_f, new_g, new_enc, new_path))

    

if __name__ == "__main__":
    # Create a dummy board
    dummy_board = {} 
    search(dummy_board)