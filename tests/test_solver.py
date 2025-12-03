"""
Test script for the hybrid Minesweeper solver.

Manually creates a game case, runs the hybrid solver, and documents
the board state after each action (excluding recursive reveals of 0 numbered tiles).
"""

import os
import sys
from datetime import datetime
from typing import List, Tuple

# Add parent directory to path to import from project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from minesweeper import Minesweeper
from hybrid_solver import ActionRecord


def format_board_for_file(board):
    """
    Formats the Minesweeper board for file output.
    Similar to format_board but simpler for text file storage.
    """
    if not board:
        return "Board is empty."
    
    height = len(board)
    width = len(board[0])
    
    # Create column indices header
    header = "    " + " ".join(f"{i:2}" for i in range(width)) + "\n"
    header += "   " + "-" * (width * 3 + 1) + "\n"
    
    # Format each row with row indices
    formatted_rows = []
    for i in range(height):
        row_str = f"{i:2} | " + " ".join(f"{str(cell):2}" for cell in board[i])
        formatted_rows.append(row_str)
    
    return header + "\n".join(formatted_rows)


def solve_with_board_tracking(game: Minesweeper,
                              max_iterations: int = 10000,
                              l4_use_information_gain: bool = False,
                              l4_safe_threshold: float = 0.35) -> Tuple[List[ActionRecord], 
                                                                        List[dict], 
                                                                        bool]:
    """
    Solve a Minesweeper game and track board states after each action.
    
    This is a modified version that captures the board state after each
    intentional action (excluding recursive reveals from 0-valued cells).
    
    Returns:
        Tuple of (action_history, board_states, solved):
        - action_history: List of ActionRecord objects
        - board_states: List of board states after each action
        - solved: True if game was won
    """
    from hybrid_solver import get_board_snapshot, find_board_changes
    from solver_layers.layer_1 import l1_step
    from solver_layers.layer_2 import l2_step
    from solver_layers.layer_3 import l3_step
    from solver_layers.layer_4 import l4_step
    
    action_history = []
    board_states = []
    iteration_count = 0
    
    # Capture initial board state
    initial_state = game.current_state
    board_states.append({
        "action_index": -1,
        "board": [row[:] for row in initial_state["board"]],  # Deep copy
        "action": None,
        "status": initial_state["status"],
        "time": initial_state["time"]
    })
    
    while iteration_count < max_iterations:
        iteration_count += 1
        
        # Check game status
        state = game.current_state
        if state["status"] != "Playing":
            solved = (state["status"] == "Won")
            return action_history, board_states, solved
        
        # Get board snapshot before trying any layer
        board_before = get_board_snapshot(state["board"])
        
        # Try Layer 1
        result = l1_step(game)
        state_after = game.current_state
        board_after = get_board_snapshot(state_after["board"])
        changes = find_board_changes(board_before, board_after)
        
        if result == "success" and changes:
            # Layer 1 succeeded - record actions and capture board state
            for change in changes:
                change.layer = 1
                action_history.append(change)
            
            # Capture board state after all changes from this layer
            # (includes recursive reveals from 0-valued cells, which is correct)
            current_state = game.current_state
            board_states.append({
                "action_index": len(action_history) - 1,
                "board": [row[:] for row in current_state["board"]],
                "action": action_history[-1] if action_history else None,
                "status": current_state["status"],
                "time": current_state["time"]
            })
            continue
        
        # Layer 1 failed, try Layer 2
        board_before = get_board_snapshot(state_after["board"])
        result = l2_step(game)
        state_after = game.current_state
        board_after = get_board_snapshot(state_after["board"])
        changes = find_board_changes(board_before, board_after)
        
        if result == "success" and changes:
            for change in changes:
                change.layer = 2
                action_history.append(change)
            
            current_state = game.current_state
            board_states.append({
                "action_index": len(action_history) - 1,
                "board": [row[:] for row in current_state["board"]],
                "action": action_history[-1] if action_history else None,
                "status": current_state["status"],
                "time": current_state["time"]
            })
            continue
        
        # Layer 2 failed, try Layer 3
        board_before = get_board_snapshot(state_after["board"])
        result = l3_step(game)
        state_after = game.current_state
        board_after = get_board_snapshot(state_after["board"])
        changes = find_board_changes(board_before, board_after)
        
        if result == "success" and changes:
            for change in changes:
                change.layer = 3
                action_history.append(change)
            
            current_state = game.current_state
            board_states.append({
                "action_index": len(action_history) - 1,
                "board": [row[:] for row in current_state["board"]],
                "action": action_history[-1] if action_history else None,
                "status": current_state["status"],
                "time": current_state["time"]
            })
            continue
        
        # Layer 3 failed, try Layer 4
        board_before = get_board_snapshot(state_after["board"])
        result = l4_step(game, 
                        use_information_gain=l4_use_information_gain,
                        safe_threshold=l4_safe_threshold)
        state_after = game.current_state
        board_after = get_board_snapshot(state_after["board"])
        changes = find_board_changes(board_before, board_after)
        
        if result == "success" and changes:
            for change in changes:
                change.layer = 4
                action_history.append(change)
            
            current_state = game.current_state
            board_states.append({
                "action_index": len(action_history) - 1,
                "board": [row[:] for row in current_state["board"]],
                "action": action_history[-1] if action_history else None,
                "status": current_state["status"],
                "time": current_state["time"]
            })
            continue
        
        # All layers failed - no progress can be made
        break
    
    # Final game status
    final_state = game.current_state
    solved = (final_state["status"] == "Won")
    
    # Capture final board state if game ended
    last_recorded_idx = board_states[-1]["action_index"] if board_states else -2
    if final_state["status"] != "Playing" and last_recorded_idx < len(action_history):
        board_states.append({
            "action_index": len(action_history),
            "board": [row[:] for row in final_state["board"]],
            "action": None,
            "status": final_state["status"],
            "time": final_state["time"]
        })
    
    return action_history, board_states, solved


def run_test():
    """
    Main test function.
    Manually create a game case and run the solver, documenting board states.
    """
    # ============================================
    # MANUALLY CREATE YOUR GAME CASE HERE
    # ============================================

    # Example game configuration
    # Modify these parameters as needed for your test case
    width = 16
    height = 16
    mines = 40
    seed = 42  # For reproducibility

    print(f"Creating test game: {width}x{height}, {mines} mines, seed={seed}")

    # Initialize game
    game = Minesweeper()
    game.start_new_game(width, height, mines, seed)

    # Make initial click to start the game
    # (The first click is required to generate the board)
    initial_x, initial_y = width // 2, height // 2
    print(f"Making initial click at ({initial_x}, {initial_y})")
    result = game.reveal_cell(initial_x, initial_y)
    print(f"Initial click result: {result}")

    # If the initial click hits a mine, try different seeds
    if result == "DEFEAT":
        print("Game ended on first click (mine hit). Trying different seed...")
        attempts = 0
        max_attempts = 10
        original_seed = seed
        while result == "DEFEAT" and attempts < max_attempts:
            seed = original_seed + attempts + 1
            attempts += 1
            game = Minesweeper()
            game.start_new_game(width, height, mines, seed)
            result = game.reveal_cell(initial_x, initial_y)
            print(f"Attempt {attempts}: Seed {seed}, result: {result}")

        if result == "DEFEAT":
            print(f"Warning: Still hitting mines after {max_attempts} attempts. Using seed {seed} anyway...")

    # ============================================
    # RUN THE SOLVER WITH BOARD TRACKING
    # ============================================

    print("\nRunning hybrid solver...")
    action_history, board_states, solved = solve_with_board_tracking(
        game,
        max_iterations=10000,
        l4_use_information_gain=False,
        l4_safe_threshold=0.35
    )
    
    print(f"Solver completed. Total actions: {len(action_history)}")
    print(f"Game status: {'Won' if solved else 'Lost/Unsolved'}")
    
    # ============================================
    # DOCUMENT RESULTS TO FILE
    # ============================================
    
    # Create output directory (relative to tests folder)
    # Since script is in tests/, we go one level up then into tests/single
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    output_dir = os.path.join(project_root, "tests", "single")
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"test_{timestamp}.txt"
    filepath = os.path.join(output_dir, filename)
    
    print(f"\nWriting results to: {filepath}")
    
    # Write test results to file
    with open(filepath, 'w', encoding='utf-8') as f:
        # Write header
        f.write("=" * 80 + "\n")
        f.write("MINESWEEPER SOLVER TEST RESULTS\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Game Configuration:\n")
        f.write(f"  Width: {width}\n")
        f.write(f"  Height: {height}\n")
        f.write(f"  Mines: {mines}\n")
        f.write(f"  Seed: {seed}\n")
        f.write(f"  Initial Click: ({initial_x}, {initial_y})\n")
        f.write(f"\nSolver Configuration:\n")
        f.write(f"  Max Iterations: 10000\n")
        f.write(f"  L4 Information Gain: False\n")
        f.write(f"  L4 Safe Threshold: 0.35\n")
        f.write(f"\nResults:\n")
        f.write(f"  Total Actions: {len(action_history)}\n")
        f.write(f"  Final Status: {'Won' if solved else board_states[-1]['status']}\n")
        f.write(f"  Final Time: {board_states[-1]['time']:.2f}s\n")
        
        # Action summary by layer
        action_summary = {
            1: {"REVEAL": 0, "FLAG": 0, "total": 0},
            2: {"REVEAL": 0, "FLAG": 0, "total": 0},
            3: {"REVEAL": 0, "FLAG": 0, "total": 0},
            4: {"REVEAL": 0, "FLAG": 0, "total": 0}
        }
        
        for action in action_history:
            layer = action.layer
            action_type = action.action_type
            action_summary[layer][action_type] += 1
            action_summary[layer]["total"] += 1
        
        f.write(f"\nAction Summary by Layer:\n")
        for layer in [1, 2, 3, 4]:
            layer_data = action_summary[layer]
            if layer_data["total"] > 0:
                f.write(f"  Layer {layer}: {layer_data['REVEAL']} reveals, "
                       f"{layer_data['FLAG']} flags, {layer_data['total']} total\n")
        
        f.write("\n" + "=" * 80 + "\n")
        f.write("BOARD STATES AFTER EACH ACTION\n")
        f.write("=" * 80 + "\n\n")
        
        # Document initial board state
        initial_state = board_states[0]
        f.write(f"INITIAL BOARD STATE (Before any solver actions)\n")
        f.write(f"Status: {initial_state['status']}\n")
        f.write(f"Time: {initial_state['time']:.2f}s\n")
        f.write("-" * 80 + "\n")
        f.write(format_board_for_file(initial_state['board']))
        f.write("\n\n")
        
        # Document board state after each action
        # Note: Each board state shows the board AFTER the action(s) executed by a layer.
        # Recursive reveals from 0-valued cells are included in the board state but
        # are not counted as separate actions (only the intentional action is recorded).
        
        last_recorded_action_idx = -1
        for i, state_info in enumerate(board_states[1:], 1):
            action_index = state_info['action_index']
            
            if action_index >= 0 and action_index < len(action_history):
                # Find all actions that were executed since last board state
                # (may be multiple if a layer executed multiple actions at once)
                actions_since_last = []
                for idx in range(last_recorded_action_idx + 1, action_index + 1):
                    if idx < len(action_history):
                        actions_since_last.append((idx, action_history[idx]))
                
                if len(actions_since_last) == 1:
                    act_idx, action = actions_since_last[0]
                    f.write(f"AFTER ACTION #{act_idx + 1}: Layer {action.layer} - {action.action_type} ({action.x}, {action.y})\n")
                elif len(actions_since_last) > 1:
                    f.write(f"AFTER ACTIONS #{actions_since_last[0][0] + 1} to #{actions_since_last[-1][0] + 1}:\n")
                    for act_idx, action in actions_since_last:
                        f.write(f"  - Action #{act_idx + 1}: Layer {action.layer} - {action.action_type} ({action.x}, {action.y})\n")
                
                last_recorded_action_idx = action_index
            else:
                f.write(f"FINAL STATE (After all actions)\n")
            
            f.write(f"Status: {state_info['status']}\n")
            f.write(f"Time: {state_info['time']:.2f}s\n")
            f.write("-" * 80 + "\n")
            f.write(format_board_for_file(state_info['board']))
            f.write("\n\n")
            
            # Stop if game is over
            if state_info['status'] in ["Won", "Lost"]:
                break
        
        # Write action sequence at the end
        f.write("=" * 80 + "\n")
        f.write("DETAILED ACTION SEQUENCE\n")
        f.write("=" * 80 + "\n\n")
        
        for idx, action in enumerate(action_history, 1):
            f.write(f"{idx:4d}. Layer {action.layer}: {action.action_type} ({action.x}, {action.y})\n")
    
    print(f"Test results saved to: {filepath}")
    print(f"Total board states documented: {len(board_states)}")
    
    return filepath


if __name__ == "__main__":
    run_test()

