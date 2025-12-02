"""
Test script for the final Minesweeper solver.

This script:
1. Creates a random Minesweeper game
2. Logs each step's decision making
3. Prints the board after every action taken
4. Captures all solver logs
5. Saves console output to a .txt file
"""

import sys
import os
import re
import random
from datetime import datetime
from io import StringIO

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from minesweeper import Minesweeper
from final_solver import solve_minesweeper


class TeeOutput:
    """Class to duplicate output to both console and a string buffer."""
    
    def __init__(self, *files):
        self.files = files
    
    def write(self, obj):
        for f in self.files:
            f.write(obj)
            f.flush()
    
    def flush(self):
        for f in self.files:
            f.flush()


class GameActionTracker:
    """Wrapper around Minesweeper that tracks all actions and board states."""
    
    def __init__(self, game):
        self.game = game
        self.actions = []  # List of (action_type, x, y, description, board_snapshot)
        self._original_reveal = game.reveal_cell
        self._original_flag = game.flag_cell
        self._reveal_depth = 0  # Track call depth to identify recursive reveals
        
        # Wrap the methods to track actions
        self._wrap_methods()
    
    def _wrap_methods(self):
        """Wrap reveal_cell and flag_cell to track actions."""
        def tracked_reveal(x, y):
            # Track call depth to distinguish direct from recursive reveals
            self._reveal_depth += 1
            is_direct_call = (self._reveal_depth == 1)
            
            # Call original reveal
            result = self._original_reveal(x, y)
            
            # Only track board state for direct reveals (not recursive ones)
            if is_direct_call:
                snapshot = self._get_board_snapshot()
                self.actions.append(
                    ("reveal", x, y, f"Reveal ({x}, {y})", snapshot))
            
            # Decrement depth after processing
            self._reveal_depth -= 1
            return result
        
        def tracked_flag(x, y):
            result = self._original_flag(x, y)
            # Flags are always direct calls, so always track them
            if result == "FLAG":  # Only track successful flags
                snapshot = self._get_board_snapshot()
                self.actions.append(
                    ("flag", x, y, f"Flag ({x}, {y})", snapshot))
            return result
        
        self.game.reveal_cell = tracked_reveal
        self.game.flag_cell = tracked_flag
    
    def _get_board_snapshot(self):
        """Get a deep copy of the current board state."""
        board = self.game.current_state["board"]
        return [row[:] for row in board]
    
    def get_unique_actions(self):
        """Get unique action descriptions with their board states, removing duplicates."""
        seen = set()
        unique_actions = []
        for action_type, x, y, desc, snapshot in self.actions:
            # Create a key based on action type and coordinates
            key = (action_type, x, y)
            if key not in seen:
                seen.add(key)
                unique_actions.append((desc, snapshot))
        return unique_actions


def format_board(board):
    """Format board for display."""
    lines = []
    for row in board:
        line = " ".join(str(cell).rjust(2) for cell in row)
        lines.append(line)
    return "\n".join(lines)


def extract_action_summaries(history, tracker):
    """
    Extract action summaries by grouping tracked actions based on solver stages.
    
    Args:
        history: List of log strings from the solver
        tracker: GameActionTracker instance
    
    Returns:
        List of (action_description, board_snapshot) tuples in chronological order
    """
    summaries = []
    tracked_actions = tracker.actions  # Get all tracked actions (type, x, y, desc, snapshot)
    
    if not tracked_actions:
        return summaries
    
    # Parse history to identify stage boundaries and correlate with tracked actions
    tracked_idx = 0
    
    for entry in history:
        # Stage 4 reveals - these are individual actions
        if "Stage 4: Revealed cell" in entry:
            match = re.search(r'Revealed cell \((\d+), (\d+)\)', entry)
            if match:
                x, y = int(match.group(1)), int(match.group(2))
                # Find this action in tracked actions
                while tracked_idx < len(tracked_actions):
                    action_type, ax, ay, desc, snapshot = tracked_actions[tracked_idx]
                    if action_type == "reveal" and ax == x and ay == y:
                        summaries.append((f"Stage 4: {desc}", snapshot))
                        tracked_idx += 1
                        break
                    tracked_idx += 1
        
        # Stage 2 patterns - group flags and reveals
        elif "Stage 2: Found pattern" in entry:
            # Match pattern with flexible whitespace handling
            # The message format is: "Stage 2: Found pattern 'ID', flagged X mines, revealed Y safe cells"
            match = re.search(
                r'Found pattern \'([^\']+)\',\s*flagged\s+(\d+)\s+mines,\s*revealed\s+(\d+)\s+safe cells',
                entry)
            if match:
                pattern_id, flags_str, reveals_str = match.groups()
                flags = int(flags_str)
                reveals = int(reveals_str)

                if flags > 0 or reveals > 0:
                    # Collect flags and reveals for this pattern
                    pattern_actions = []
                    collected_flags = 0
                    collected_reveals = 0

                    while (tracked_idx < len(tracked_actions) and
                           (collected_flags < flags or
                            collected_reveals < reveals)):
                        action_type, ax, ay, desc, snapshot = (
                            tracked_actions[tracked_idx])
                        if action_type == "flag" and collected_flags < flags:
                            pattern_actions.append((desc, snapshot))
                            collected_flags += 1
                            tracked_idx += 1
                        elif (action_type == "reveal" and
                              collected_reveals < reveals):
                            pattern_actions.append((desc, snapshot))
                            collected_reveals += 1
                            tracked_idx += 1
                        else:
                            # Skip non-matching actions
                            tracked_idx += 1

                    if pattern_actions:
                        # Use the last snapshot from this pattern
                        last_snapshot = pattern_actions[-1][1]
                        msg = (f"Stage 2: Pattern '{pattern_id}' - "
                               f"Flagged {flags} mine(s), "
                               f"Revealed {reveals} safe cell(s)")
                        summaries.append((msg, last_snapshot))
        
        # Stage 1 CSP - collect batches of actions
        elif "Stage 1: Applied basic CSP rules" in entry:
            # Collect actions that occurred from Stage 1
            # Since history entries are processed sequentially, we collect
            # actions until we've processed all Stage 1 actions or hit limit
            csp_actions = []

            # Collect up to 50 actions (reasonable limit for CSP batch)
            # These should all be Stage 1 actions since we process history
            # entries in order and Stage 1 actions happen before other stages
            while (tracked_idx < len(tracked_actions) and
                   len(csp_actions) < 50):
                action_type, ax, ay, desc, snapshot = (
                    tracked_actions[tracked_idx])
                if action_type in ("flag", "reveal"):
                    csp_actions.append((desc, snapshot))
                tracked_idx += 1

            if csp_actions:
                # Use the last snapshot
                last_snapshot = csp_actions[-1][1]
                msg = (f"Stage 1: Applied basic CSP rules "
                       f"({len(csp_actions)} actions)")
                summaries.append((msg, last_snapshot))
    
    return summaries


def count_cells(board):
    """Count different cell types on the board."""
    counts = {
        "hidden": 0,
        "revealed": 0,
        "flagged": 0,
        "mines": 0
    }
    
    for row in board:
        for cell in row:
            if cell == "_":
                counts["hidden"] += 1
            elif cell == "F":
                counts["flagged"] += 1
            elif cell == "M":
                counts["mines"] += 1
            elif isinstance(cell, int):
                counts["revealed"] += 1
    
    return counts


def run_test(width=10, height=10, mines=10, seed=None, 
             use_information_gain=False, safe_threshold=0.35):
    """
    Run a single test of the Minesweeper solver.
    
    Args:
        width: Board width
        height: Board height
        mines: Number of mines
        seed: Random seed (None for random)
        use_information_gain: Use information gain heuristic
        safe_threshold: Safe threshold for Stage 4
    
    Returns:
        Tuple of (success: bool, output: str)
    """
    # Generate random seed if not provided
    if seed is None:
        seed = random.randint(1, 1000000)
    
    # Create output buffer
    output_buffer = StringIO()
    
    # Create TeeOutput to capture both console and buffer
    original_stdout = sys.stdout
    tee = TeeOutput(original_stdout, output_buffer)
    sys.stdout = tee
    
    try:
        # Print header
        print("=" * 80)
        print("MINESWEEPER SOLVER TEST")
        print("=" * 80)
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Board size: {width}x{height}")
        print(f"Number of mines: {mines}")
        print(f"Random seed: {seed}")
        print(f"Use information gain: {use_information_gain}")
        print(f"Safe threshold: {safe_threshold}")
        print("=" * 80)
        print()
        
        # Create and initialize game
        print("Creating new game...")
        game = Minesweeper()
        game.start_new_game(width=width, height=height, mines=mines, seed=seed)
        
        # Wrap game to track actions
        tracker = GameActionTracker(game)
        
        # Make initial click (center of board)
        init_x = width // 2
        init_y = height // 2
        print(f"Making initial click at ({init_x}, {init_y})...")
        result = game.reveal_cell(init_x, init_y)
        print(f"Initial click result: {result}")
        print(f"(Note: Initial click may reveal multiple cells via recursion)")
        print()
        
        # Capture initial board state
        initial_board = game.current_state["board"]
        
        # Print initial board state
        print("=" * 80)
        init_msg = (f"INITIAL BOARD STATE "
                    f"(After first click at ({init_x}, {init_y}))")
        print(init_msg)
        print("=" * 80)
        print(format_board(initial_board))
        print()
        
        # Count initial cells
        initial_counts = count_cells(initial_board)
        print("Initial cell counts:")
        print(f"  Hidden: {initial_counts['hidden']}")
        print(f"  Revealed: {initial_counts['revealed']}")
        print(f"  Flagged: {initial_counts['flagged']}")
        print(f"  Mines (hit): {initial_counts['mines']}")
        print()
        
        # Run solver with custom logging to track actions
        print("=" * 80)
        print("STARTING SOLVER")
        print("=" * 80)
        print()
        
        # Run solver (output suppressed)
        success, history = solve_minesweeper(
            game,
            max_iterations=1000,
            use_information_gain=use_information_gain,
            safe_threshold=safe_threshold,
            verbose=False  # Suppress verbose output
        )
        
        # Get all individual actions sequentially
        tracked_actions = tracker.actions  # List of (action_type, x, y, desc, snapshot)
        
        # Create a mapping of actions to stages by correlating with history
        action_to_stage = {}
        tracked_idx = 0
        
        for entry in history:
            # Stage 1 actions
            if "Stage 1: Applied basic CSP rules" in entry:
                # Collect all actions until next stage marker
                start_idx = tracked_idx
                while (tracked_idx < len(tracked_actions) and
                       tracked_idx < start_idx + 100):  # Safety limit
                    if tracked_idx not in action_to_stage:
                        action_to_stage[tracked_idx] = "Stage 1"
                    # Check if we've hit a stage boundary
                    if tracked_idx + 1 < len(tracked_actions):
                        tracked_idx += 1
                    else:
                        break
            
            # Stage 2 actions
            elif "Stage 2: Found pattern" in entry:
                match = re.search(
                    r'Found pattern \'([^\']+)\',\s*flagged\s+(\d+)\s+mines,\s*revealed\s+(\d+)\s+safe cells',
                    entry)
                if match:
                    flags = int(match.group(2))
                    reveals = int(match.group(3))
                    collected = 0
                    while (tracked_idx < len(tracked_actions) and
                           collected < flags + reveals):
                        if tracked_idx not in action_to_stage:
                            action_to_stage[tracked_idx] = "Stage 2"
                        tracked_idx += 1
                        collected += 1
            
            # Stage 4 actions
            elif "Stage 4: Revealed cell" in entry:
                match = re.search(r'Revealed cell \((\d+), (\d+)\)', entry)
                if match:
                    while tracked_idx < len(tracked_actions):
                        action_type, ax, ay, _, _ = tracked_actions[tracked_idx]
                        if (action_type == "reveal" and
                            ax == int(match.group(1)) and
                            ay == int(match.group(2))):
                            action_to_stage[tracked_idx] = "Stage 4"
                            tracked_idx += 1
                            break
                        tracked_idx += 1
        
        # Print each individual action with board state
        if tracked_actions:
            print("=" * 80)
            print("SOLVING ACTIONS WITH BOARD STATES (EACH ACTION)")
            print("=" * 80)
            print()
            
            for i, (action_type, x, y, desc, board_after) in enumerate(
                tracked_actions, 1):
                # Get stage label if available
                stage_label = action_to_stage.get(i - 1, "Unknown Stage")
                
                print(f"Action {i}: {stage_label} - {desc}")
                print()
                print(format_board(board_after))
                
                # Count cells
                counts = count_cells(board_after)
                print(f"  Hidden: {counts['hidden']}, "
                      f"Revealed: {counts['revealed']}, "
                      f"Flagged: {counts['flagged']}, "
                      f"Mines: {counts['mines']}")
                print()
        else:
            print("No actions were tracked.")
            print("(Solver may have made no progress or actions were not logged)")
            print()
        
        # Print final board state
        print("=" * 80)
        print("FINAL BOARD STATE")
        print("=" * 80)
        final_board = game.current_state["board"]
        print(format_board(final_board))
        print()
        
        # Count final cells
        final_counts = count_cells(final_board)
        print("Final cell counts:")
        print(f"  Hidden: {final_counts['hidden']}")
        print(f"  Revealed: {final_counts['revealed']}")
        print(f"  Flagged: {final_counts['flagged']}")
        print(f"  Mines (hit): {final_counts['mines']}")
        print()
        
        # Print summary
        print("=" * 80)
        print("SOLVING SUMMARY")
        print("=" * 80)
        print(f"Game status: {game.current_state['status']}")
        print(f"Solver success: {success}")
        print(f"Total actions taken: {len(tracked_actions)}")
        print(f"Total solver log entries: {len(history)}")
        print(f"Time elapsed: {game.current_state['time']:.2f} seconds")
        print()
        
        print("=" * 80)
        print("TEST COMPLETE")
        print("=" * 80)
        
    finally:
        # Restore original stdout
        sys.stdout = original_stdout
    
    # Get output string
    output = output_buffer.getvalue()
    return success, output


def main():
    """Main function to run the test."""
    # Test parameters - Expert Minesweeper configuration (16x30, 99 mines)
    width = 9
    height = 9
    mines = 10
    seed = None  # Random seed
    use_information_gain = False
    safe_threshold = 0.35
    
    # Run the test
    print("Running Minesweeper solver test...")
    print()
    
    success, output = run_test(
        width=width,
        height=height,
        mines=mines,
        seed=seed,
        use_information_gain=use_information_gain,
        safe_threshold=safe_threshold
    )

    # Save output to file
    script_dir = os.path.dirname(os.path.abspath(__file__))
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = os.path.join(script_dir, f"solver_test_{timestamp}.txt")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(output)
    
    print()
    print(f"Output saved to: {output_file}")
    print(f"Test {'PASSED' if success else 'FAILED'}")
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
