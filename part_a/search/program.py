# COMP30024 Artificial Intelligence, Semester 1 2026
# Project Part A: Single Player Cascade
import heapq

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

def apply_move(board: dict, coord: Coord, dest: Coord):
    """Move a Red stack to destination. If destination is empy, move there. If destination is same colour, merge."""
    cell = board[coord]
    dest_cell = board.get(dest)
    nb = dict(board)
    del nb[coord]
    if dest_cell is None:
        nb[dest] = cell
    else:
        nb[dest] = CellState(PlayerColor.RED, cell.height + dest_cell.height)
    return nb

def apply_eat(board: dict, coord: Coord, dest: Coord):
    """Remove the eaten stack and move the eater there."""
    cell = board[coord]
    nb = dict(board)
    del nb[coord]
    nb[dest] = cell
    return nb

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



def search(
    board: dict[Coord, CellState]
) -> list[Action] | None:
    """
    This is the entry point for your submission. You should modify this
    function to solve the search problem discussed in the Part A specification.
    See `core.py` for information on the types being used here.

    Parameters:
        `board`: a dictionary representing the initial board state, mapping
            coordinates to `CellState` instances (each with a `.color` and
            `.height` attribute).

    Returns:
        A list of actions (MoveAction, EatAction, or CascadeAction), or `None`
        if no solution is possible.
    """

    # The render_board() function is handy for debugging. It will print out a
    # board state in a human-readable format. If your terminal supports ANSI
    # codes, set the `ansi` flag to True to print a colour-coded version!
    print(render_board(board, ansi=True))

    # Do some impressive AI stuff here to find the solution...
    # ...
    # ... (your solution goes here!)
    # ...

    # Here we're returning "hardcoded" actions as an example of the expected
    # output format. Of course, you should instead return the result of your
    # search algorithm. Remember: if no solution is possible for a given input,
    # return `None` instead of a list.
    return [
        MoveAction(Coord(3, 3), Direction.Down),
        EatAction(Coord(4, 3), Direction.Down)
    ]
