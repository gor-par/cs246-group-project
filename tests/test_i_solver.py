"""
Iterative test script for the hybrid Minesweeper solver.

Runs the solver test multiple times (i iterations) with incrementing seeds,
piling up all reports in a timestamped folder.
"""

import os
import sys
from datetime import datetime
from typing import Tuple

# Add parent directory to path to import from project root
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Add tests directory to path to import from same directory
tests_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, tests_dir)

from minesweeper import Minesweeper
from test_solver import solve_with_board_tracking, format_board_for_file


def run_single_test(width: int,
                    height: int,
                    mines: int,
                    seed: int,
                    output_dir: str,
                    test_number: int,
                    l4_use_information_gain: bool = False,
                    l4_safe_threshold: float = 0.35) -> Tuple[str, dict]:
    """
    Run a single test with given parameters and save to file.
    
    Returns:
        Tuple of (filepath, summary_dict):
        - filepath: Path to the saved test file
        - summary_dict: Dictionary with test summary statistics
    """
    # Initialize game
    game = Minesweeper()
    game.start_new_game(width, height, mines, seed)
    
    # Make initial click to start the game
    initial_x, initial_y = width // 2, height // 2
    result = game.reveal_cell(initial_x, initial_y)
    
    # If the initial click hits a mine, try different seeds
    if result == "DEFEAT":
        attempts = 0
        max_attempts = 10
        original_seed = seed
        while result == "DEFEAT" and attempts < max_attempts:
            seed = original_seed + attempts + 1
            attempts += 1
            game = Minesweeper()
            game.start_new_game(width, height, mines, seed)
            result = game.reveal_cell(initial_x, initial_y)
    
    # Run the solver with board tracking
    action_history, board_states, solved = solve_with_board_tracking(
        game,
        max_iterations=10000,
        l4_use_information_gain=l4_use_information_gain,
        l4_safe_threshold=l4_safe_threshold
    )
    
    # Create filename
    filename = f"test_{test_number:03d}_seed_{seed}.txt"
    filepath = os.path.join(output_dir, filename)
    
    # Write test results to file
    with open(filepath, 'w', encoding='utf-8') as f:
        # Write header
        f.write("=" * 80 + "\n")
        f.write("MINESWEEPER SOLVER TEST RESULTS\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Test Number: {test_number}\n")
        f.write(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Game Configuration:\n")
        f.write(f"  Width: {width}\n")
        f.write(f"  Height: {height}\n")
        f.write(f"  Mines: {mines}\n")
        f.write(f"  Seed: {seed}\n")
        f.write(f"  Initial Click: ({initial_x}, {initial_y})\n")
        f.write(f"\nSolver Configuration:\n")
        f.write(f"  Max Iterations: 10000\n")
        f.write(f"  L4 Information Gain: {l4_use_information_gain}\n")
        f.write(f"  L4 Safe Threshold: {l4_safe_threshold}\n")
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
        last_recorded_action_idx = -1
        for i, state_info in enumerate(board_states[1:], 1):
            action_index = state_info['action_index']
            
            if action_index >= 0 and action_index < len(action_history):
                # Find all actions that were executed since last board state
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
    
    # Create summary dictionary
    summary = {
        "test_number": test_number,
        "seed": seed,
        "solved": solved,
        "total_actions": len(action_history),
        "final_status": board_states[-1]['status'],
        "final_time": board_states[-1]['time'],
        "action_summary": action_summary
    }
    
    return filepath, summary


def run_iterative_tests(i: int = 10,
                        width: int = 16,
                        height: int = 16,
                        mines: int = 40,
                        base_seed: int = 42,
                        l4_use_information_gain: bool = False,
                        l4_safe_threshold: float = 0.35):
    """
    Run the solver test i times with incrementing seeds.
    
    Args:
        i: Number of iterations to run (default: 10)
        width: Game board width
        height: Game board height
        mines: Number of mines
        base_seed: Starting seed value (will be incremented by +1 for each test)
        l4_use_information_gain: Whether to use information gain for Layer 4
        l4_safe_threshold: Safe threshold for Layer 4
    """
    print(f"Starting iterative test suite: {i} iterations")
    print(f"Game configuration: {width}x{height}, {mines} mines")
    print(f"Base seed: {base_seed}\n")
    
    # Create output directory with timestamp
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = os.path.join(project_root, "tests", "multiple", f"test_{i}_{timestamp}")
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"Output directory: {output_dir}\n")
    
    # Store all summaries
    all_summaries = []
    
    # Run tests
    for test_num in range(1, i + 1):
        seed = base_seed + (test_num - 1)  # Increment seed by 1 for each test
        print(f"Running test {test_num}/{i} (seed: {seed})...", end=" ", flush=True)
        
        try:
            filepath, summary = run_single_test(
                width=width,
                height=height,
                mines=mines,
                seed=seed,
                output_dir=output_dir,
                test_number=test_num,
                l4_use_information_gain=l4_use_information_gain,
                l4_safe_threshold=l4_safe_threshold
            )
            
            all_summaries.append(summary)
            status_emoji = "✓" if summary["solved"] else "✗"
            print(f"{status_emoji} {summary['final_status']} ({summary['total_actions']} actions, {summary['final_time']:.2f}s)")
            
        except Exception as e:
            print(f"ERROR: {e}")
            all_summaries.append({
                "test_number": test_num,
                "seed": seed,
                "error": str(e),
                "solved": False
            })
    
    # Create summary report
    summary_filepath = os.path.join(output_dir, "summary.txt")
    with open(summary_filepath, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("ITERATIVE TEST SUITE SUMMARY\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total Iterations: {i}\n")
        f.write(f"Game Configuration:\n")
        f.write(f"  Width: {width}\n")
        f.write(f"  Height: {height}\n")
        f.write(f"  Mines: {mines}\n")
        f.write(f"  Base Seed: {base_seed}\n")
        f.write(f"  Seed Range: {base_seed} to {base_seed + i - 1}\n")
        f.write(f"\nSolver Configuration:\n")
        f.write(f"  Max Iterations: 10000\n")
        f.write(f"  L4 Information Gain: {l4_use_information_gain}\n")
        f.write(f"  L4 Safe Threshold: {l4_safe_threshold}\n")
        f.write("\n" + "=" * 80 + "\n")
        f.write("RESULTS SUMMARY\n")
        f.write("=" * 80 + "\n\n")
        
        # Calculate statistics
        won_count = sum(1 for s in all_summaries if s.get("solved", False))
        lost_count = sum(1 for s in all_summaries if s.get("final_status") == "Lost")
        unsolved_count = i - won_count - lost_count
        error_count = sum(1 for s in all_summaries if "error" in s)
        
        total_actions = [s.get("total_actions", 0) for s in all_summaries if "error" not in s]
        total_times = [s.get("final_time", 0) for s in all_summaries if "error" not in s]
        
        f.write(f"Won: {won_count}/{i} ({won_count/i*100:.1f}%)\n")
        f.write(f"Lost: {lost_count}/{i} ({lost_count/i*100:.1f}%)\n")
        f.write(f"Unsolved: {unsolved_count}/{i} ({unsolved_count/i*100:.1f}%)\n")
        if error_count > 0:
            f.write(f"Errors: {error_count}/{i}\n")
        
        if total_actions:
            f.write(f"\nAverage Actions: {sum(total_actions)/len(total_actions):.1f}\n")
            f.write(f"Min Actions: {min(total_actions)}\n")
            f.write(f"Max Actions: {max(total_actions)}\n")
        
        if total_times:
            f.write(f"\nAverage Time: {sum(total_times)/len(total_times):.2f}s\n")
            f.write(f"Min Time: {min(total_times):.2f}s\n")
            f.write(f"Max Time: {max(total_times):.2f}s\n")
        
        # Layer statistics
        f.write("\n" + "=" * 80 + "\n")
        f.write("LAYER STATISTICS (Average across all tests)\n")
        f.write("=" * 80 + "\n\n")
        
        layer_stats = {1: {"REVEAL": 0, "FLAG": 0, "total": 0},
                       2: {"REVEAL": 0, "FLAG": 0, "total": 0},
                       3: {"REVEAL": 0, "FLAG": 0, "total": 0},
                       4: {"REVEAL": 0, "FLAG": 0, "total": 0}}
        
        valid_tests = [s for s in all_summaries if "error" not in s and "action_summary" in s]
        
        if valid_tests:
            for summary in valid_tests:
                for layer in [1, 2, 3, 4]:
                    if "action_summary" in summary:
                        layer_stats[layer]["REVEAL"] += summary["action_summary"][layer]["REVEAL"]
                        layer_stats[layer]["FLAG"] += summary["action_summary"][layer]["FLAG"]
                        layer_stats[layer]["total"] += summary["action_summary"][layer]["total"]
            
            for layer in [1, 2, 3, 4]:
                count = len(valid_tests)
                if count > 0:
                    avg_reveal = layer_stats[layer]["REVEAL"] / count
                    avg_flag = layer_stats[layer]["FLAG"] / count
                    avg_total = layer_stats[layer]["total"] / count
                    if avg_total > 0:
                        f.write(f"Layer {layer}: {avg_reveal:.1f} reveals, {avg_flag:.1f} flags, {avg_total:.1f} total (average)\n")
        
        # Individual test results
        f.write("\n" + "=" * 80 + "\n")
        f.write("INDIVIDUAL TEST RESULTS\n")
        f.write("=" * 80 + "\n\n")
        
        for summary in all_summaries:
            test_num = summary.get("test_number", "?")
            seed = summary.get("seed", "?")
            
            if "error" in summary:
                f.write(f"Test {test_num:03d} (seed {seed}): ERROR - {summary['error']}\n")
            else:
                status = "Won" if summary.get("solved", False) else summary.get("final_status", "Unknown")
                actions = summary.get("total_actions", 0)
                time = summary.get("final_time", 0)
                f.write(f"Test {test_num:03d} (seed {seed}): {status} - {actions} actions, {time:.2f}s\n")
    
    print(f"\n{'='*60}")
    print(f"All tests completed!")
    print(f"Results saved to: {output_dir}")
    print(f"Summary: {won_count}/{i} won ({won_count/i*100:.1f}%)")
    print(f"{'='*60}\n")
    
    return output_dir, all_summaries


def main():
    """
    Main function with default parameters.
    Modify these to customize the test suite.
    """
    # ============================================
    # CONFIGURATION - MODIFY AS NEEDED
    # ============================================
    
    # Number of iterations
    i = 10
    
    # Game configuration
    width = 9
    height = 9
    mines = 10
    base_seed = 42  # Starting seed (will be incremented by +1 for each test)
    
    # Solver configuration
    l4_use_information_gain = False
    l4_safe_threshold = 0.35
    
    # ============================================
    # RUN ITERATIVE TESTS
    # ============================================
    
    run_iterative_tests(
        i=i,
        width=width,
        height=height,
        mines=mines,
        base_seed=base_seed,
        l4_use_information_gain=l4_use_information_gain,
        l4_safe_threshold=l4_safe_threshold
    )


if __name__ == "__main__":
    main()

