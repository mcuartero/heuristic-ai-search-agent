# COMP30024 Artificial Intelligence, Semester 1 2026
# Project Part A: Single Player Cascade
import heapq
from itertools import count

from .core import CellState, Coord, Direction, Action, MoveAction, EatAction, CascadeAction, BOARD_N, PlayerColor
from .utils import render_board

RED = PlayerColor.RED.value, 
BLUE = PlayerColor.BLUE.value

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

def blue_count(enc: tuple):
    return sum(1 for _, _, col, _ in enc if col == BLUE)

def apply_move(board: dict, src: Coord, dir: Direction):
    dest = src + dir

    # Add if we decide that we want to allow moves that push tokens off the board, but for now just ignore them
    # if not in_bounds(dest.r, dest.c):
    #     print(f"Invalid move: {src} + {dir} = {dest} is out of bounds")
    #     return board

    new_board = dict(board)
    
    if dest in new_board:
        target = new_board.get(dest)

        if target.color == PlayerColor.BLUE:
            print(f"Invalid move: {dest} is occupied by a Blue stack")
            return board 
        
        elif target.color == PlayerColor.RED:
            moving_stack = new_board.pop(src)
            new_board[dest] = CellState(PlayerColor.RED, moving_stack.height + target.height)
            return new_board
    
    moving_stack = new_board.pop(src)
    new_board[dest] = moving_stack
    return new_board

def apply_eat(board: dict, src: Coord, dir: Direction):
    """Capture enemy stack and moves there."""
    dest = src + dir

    if src not in board or not in_bounds(dest.r, dest.c):
        print(f"Invalid eat: {src} or {dest} is not occupied")
        return board
    
    attacker = board.get(src)
    target = board.get(dest)

    if target is None or target.color != PlayerColor.BLUE:
        print(f"Invalid eat: {dest} is not occupied by a Blue stack")
        return board
    
    if attacker.height < target.height:
        print(f"Invalid eat: Attacker height {attacker.height} is less than target height {target.height}")
        return board

    new_board = dict(board)
    new_board.pop(src)
    new_board[dest] = CellState(PlayerColor.RED, attacker.height)
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
    """Return a list of (action, resulting_board) for every legal red move."""
    results = []

    for coord, cell in list(board.items()):
        if cell.color != PlayerColor.RED:
            continue

        r, c, h = coord.r, coord.c, cell.height

        for direction, dr, dc in DIRS:
            nr, nc = r + dr, c + dc

            if in_bounds(nr, nc):
                dest_cell = board.get(Coord(nr, nc))

                # MOVE: to empty cell or onto a friendly stack
                if dest_cell is None or dest_cell.color == PlayerColor.RED:
                    nb = apply_move(board, coord, direction)
                    results.append((MoveAction(coord, direction), nb))

                # EAT: capture an adjacent enemy if tall enough
                if (dest_cell is not None
                        and dest_cell.color == PlayerColor.BLUE
                        and h >= dest_cell.height):
                    nb = apply_eat(board, coord, direction)
                    results.append((EatAction(coord, direction), nb))

            # CASCADE: only for stacks of height >= 2
            if h >= 2:
                nb = apply_cascade(board, coord, direction)
                results.append((CascadeAction(coord, direction), nb))

    return results

def search(board: dict[Coord, CellState]) -> list[Action] | None:
    print(render_board(board, ansi=True))
    tie = count()

    if not is_solvable(board):
        return None
    
    initial = encode(board)
    node_queue = []
    visited = set()
    parent: dict[tuple, tuple | None] = {initial: None}

    ## adding initial state to queue with f = heuristic, g = 0 and empty path
    heapq.heappush(node_queue, (heuristic(board), 0, next(tie), initial, [])) ## item (f, g, tie, state, path)

    while node_queue:
        f, g, t, enc, path = heapq.heappop(node_queue)

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
            if new_enc in visited or new_enc in parent:
                continue

            parent[new_enc] = (enc, action)
            new_g = g + 1
            new_f = new_g + heuristic(new_board)
            new_path = path + [action]
            heapq.heappush(node_queue, (new_f, new_g, next(tie), new_enc, new_path))
    return None

if __name__ == "__main__":
    # Create a dummy board
    dummy_board = {} 
    search(dummy_board)