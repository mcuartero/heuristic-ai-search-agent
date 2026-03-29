from search.core import CellState, Coord, PlayerColor, BOARD_N
from search.utils import render_board
from search.program import search, encode, decode, get_moves

def parse_input(csv_data: str) -> dict[Coord, CellState]:
    """Converts the CSV string into the board dictionary format."""
    board = {}
    lines = csv_data.strip().split('\n')
    for r, line in enumerate(lines):
        cells = [c.strip() for c in line.split(',')]
        for c, cell_str in enumerate(cells):
            if not cell_str:
                continue
            color = PlayerColor.RED if cell_str.startswith('R') else PlayerColor.BLUE
            height = int(cell_str[1:])
            board[Coord(r, c)] = CellState(color, height)
    return board

def run_test_and_visualize(csv_data: str):

    board = parse_input(csv_data)
    print("### INITIAL BOARD")
    print(render_board(board, ansi=True))

    solution_actions = search(board)
    
    if not solution_actions:
        print("\n[!] No solution found by the AI.")
        return

    print(f"\n### SOLUTION FOUND: {len(solution_actions)} STEPS")
    print("-" * 40)
    
    current_board = board
    for i, action in enumerate(solution_actions, 1):

        state_tuple, blue_cnt = encode(current_board)
        possible_moves = get_moves(state_tuple, blue_cnt)
        
        next_state = None
        for act, nxt_s, _ in possible_moves:
            if act == action:
                next_state = nxt_s
                break
        
        if next_state is None:
            print(f"Error: Action {action} not found in legal moves!")
            break

        current_board = decode(next_state)
        print(f"\nSTEP {i}: {action}")
        print(render_board(current_board, ansi=True))

    print("\n### TEST COMPLETE")

test_case = """
 , , , , , , , 
 ,R1, , , , , , 
 , , , , , , , 
 , ,B3, , , , , 
 , , , , , , , 
 , , , , , ,R2, 
 , , , , , , , 
 , , , , , ,B1, 
 """
    
run_test_and_visualize(test_case)