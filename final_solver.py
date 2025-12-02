"""
Final Solver for Minesweeper

This module combines all solver stages into a unified iterative solver:
- Stage 1: Basic CSP rules (layer1_resolver)
- Stage 2: Pattern-based solving (pattern_solver)
- Stage 3: [NOT IMPLEMENTED - placeholder for future advanced CSP solver]
- Stage 4: Probabilistic solver (phase_4_solver)

The solver iteratively tries each stage in order until:
- The game is won or lost
- No stage can make any progress
"""

from typing import Tuple, List
from minesweeper import Minesweeper
from layer1_resolver import apply_basic_csp
from pattern_solver import apply_one_pattern_step_to_game
from phase_4_solver import solve_phase_4


def get_board_snapshot(game: Minesweeper) -> List[List]:
    """Get a deep copy of the current board state for comparison."""
    board = game.current_state["board"]
    return [row[:] for row in board]


def boards_differ(board1: List[List], board2: List[List]) -> bool:
    """Check if two board states are different."""
    if len(board1) != len(board2):
        return True
    for y in range(len(board1)):
        if len(board1[y]) != len(board2[y]):
            return True
        for x in range(len(board1[y])):
            if board1[y][x] != board2[y][x]:
                return True
    return False


def try_stage_1(game: Minesweeper, log_callback=None) -> Tuple[bool, dict]:
    """
    Try Stage 1: Basic CSP rules (layer1_resolver).
    
    Args:
        game: The Minesweeper game instance
        log_callback: Optional function to call with logging info
    
    Returns:
        Tuple of (progress: bool, details: dict)
        - progress: True if any progress was made, False otherwise
        - details: Dictionary with details about what happened
    """
    if game.game_over:
        return False, {"reason": "Game already over"}
    
    board_before = get_board_snapshot(game)
    apply_basic_csp(game)
    board_after = get_board_snapshot(game)
    
    # Check if board changed or game ended
    progress = boards_differ(board_before, board_after) or game.game_over
    
    details = {
        "progress": progress,
        "board_changed": boards_differ(board_before, board_after),
        "game_ended": game.game_over
    }
    
    if log_callback and progress:
        msg = (f"Stage 1: Applied basic CSP rules, "
               f"board changed: {details['board_changed']}")
        log_callback(msg)
    
    return progress, details


def try_stage_2(game: Minesweeper, log_callback=None) -> Tuple[bool, dict]:
    """
    Try Stage 2: Pattern-based solving (pattern_solver).
    
    Args:
        game: The Minesweeper game instance
        log_callback: Optional function to call with logging info
    
    Returns:
        Tuple of (progress: bool, details: dict)
        - progress: True if any progress was made, False otherwise
        - details: Dictionary with details about what happened
    """
    if game.game_over:
        return False, {"reason": "Game already over"}
    
    board_before = get_board_snapshot(game)
    step_result = apply_one_pattern_step_to_game(game)
    board_after = get_board_snapshot(game)
    
    # Progress ONLY if pattern was found and moves were made
    # Don't report progress just because board changed - that could be from
    # recursive reveals or other side effects, not from pattern matching
    progress = (
        (step_result.pattern is not None and (step_result.mines or step_result.safes)) or
        game.game_over
    )
    
    pattern_id = step_result.pattern.pattern.short_id if step_result.pattern else None
    details = {
        "progress": progress,
        "pattern_found": step_result.pattern is not None,
        "pattern_id": pattern_id,
        "mines_flagged": len(step_result.mines),
        "safes_revealed": len(step_result.safes),
        "board_changed": boards_differ(board_before, board_after),
        "game_ended": game.game_over
    }
    
    if log_callback and progress:
        if step_result.pattern:
            msg = (f"Stage 2: Found pattern '{pattern_id}', "
                   f"flagged {len(step_result.mines)} mines, "
                   f"revealed {len(step_result.safes)} safe cells")
            log_callback(msg)
        else:
            msg = (f"Stage 2: No pattern found, but board changed: "
                   f"{details['board_changed']}")
            log_callback(msg)
    
    return progress, details


def try_stage_3(game: Minesweeper, log_callback=None) -> Tuple[bool, dict]:
    """
    Try Stage 3: Advanced CSP solver.
    
    NOTE: This stage is NOT YET IMPLEMENTED.
    It is a placeholder for future advanced constraint satisfaction solving.
    
    Args:
        game: The Minesweeper game instance
        log_callback: Optional function to call with logging info
    
    Returns:
        Tuple of (progress: bool, details: dict)
        - progress: False (no progress since not implemented)
        - details: Dictionary with details about what happened
    """
    if game.game_over:
        return False, {"reason": "Game already over"}
    
    # TODO: Implement Stage 3 - Advanced CSP solver
    # This would be a more sophisticated constraint satisfaction solver
    # that handles complex multi-cell constraint relationships
    
    details = {
        "progress": False,
        "reason": "Not implemented"
    }
    
    if log_callback:
        log_callback("Stage 3: Advanced CSP - NOT IMPLEMENTED, skipping")
    
    return False, details


def try_stage_4(game: Minesweeper, 
                use_information_gain: bool = False,
                safe_threshold: float = 0.35,
                log_callback=None) -> Tuple[bool, dict]:
    """
    Try Stage 4: Probabilistic solver (phase_4_solver).
    
    This stage uses probability calculations to make guesses when
    deterministic methods cannot find a solution.
    
    Args:
        game: The Minesweeper game instance
        use_information_gain: If True, uses information gain heuristic
        safe_threshold: Maximum acceptable mine probability (default 0.35)
        log_callback: Optional function to call with logging info
    
    Returns:
        Tuple of (progress: bool, details: dict)
        - progress: True if an action was taken and executed, False otherwise
        - details: Dictionary with details about what happened
    """
    if game.game_over:
        return False, {"reason": "Game already over"}
    
    state = game.current_state
    board = state["board"]
    
    # Get board dimensions and total mines
    height = len(board)
    width = len(board[0]) if board else 0
    total_mines = game.mines
    
    # Collect flagged cells
    flagged_cells = set()
    for y in range(height):
        for x in range(width):
            if board[y][x] == "F":
                flagged_cells.add((x, y))
    
    # Get action from phase 4 solver
    action, coordinates = solve_phase_4(
        board=board,
        width=width,
        height=height,
        total_mines=total_mines,
        flagged_cells=flagged_cells,
        use_information_gain=use_information_gain,
        safe_threshold=safe_threshold
    )
    
    details = {
        "action": action,
        "coordinates": coordinates,
        "progress": False
    }
    
    # Execute the action if one was provided
    if action == "REVEAL" and coordinates is not None:
        x, y = coordinates
        result = game.reveal_cell(x, y)
        details["progress"] = result in ("SUCCESS", "REPEAT", "DEFEAT", "VICTORY")
        details["result"] = result
        
        if log_callback:
            log_callback(f"Stage 4: Revealed cell ({x}, {y}), "
                        f"result: {result}")
    else:
        if log_callback:
            msg = (f"Stage 4: No action available "
                   f"(action={action}, coordinates={coordinates})")
            log_callback(msg)
    
    return details["progress"], details


def solve_minesweeper(game: Minesweeper,
                      max_iterations: int = 1000,
                      use_information_gain: bool = False,
                      safe_threshold: float = 0.35,
                      verbose: bool = False,
                      log_callback=None) -> Tuple[bool, List[str]]:
    """
    Main solver function that combines all stages in a sequential, iterative loop.
    
    The solver tries each stage in order until one makes progress:
    1. Stage 1: Basic CSP rules
    2. Stage 2: Pattern-based solving (only if Stage 1 fails)
    3. Stage 3: Advanced CSP solver (only if Stage 2 fails, NOT IMPLEMENTED - skipped)
    4. Stage 4: Probabilistic solver (only if all previous stages fail)
    
    If any stage makes progress, the loop restarts from Stage 1.
    If no stage makes progress, the solver stops.
    
    Args:
        game: The Minesweeper game instance (should have at least one cell revealed)
        max_iterations: Maximum number of iterations to prevent infinite loops
        use_information_gain: If True, Stage 4 uses information gain heuristic
        safe_threshold: Maximum acceptable mine probability for Stage 4 (default 0.35)
        verbose: If True, print progress information
        log_callback: Optional function to call with logging info (takes a string)
    
    Returns:
        Tuple of (success: bool, history: List[str])
        - success: True if game was won, False if lost or unsolvable
        - history: List of strings describing the solving process
    """
    history = []
    iteration = 0
    
    def log(msg):
        if verbose:
            print(msg)
        history.append(msg)
        if log_callback:
            log_callback(msg)
    
    log("=" * 60)
    log("Starting Minesweeper solver...")
    log(f"Board: {game.width}x{game.height}, Mines: {game.mines}")
    log("=" * 60)
    
    while not game.game_over and iteration < max_iterations:
        iteration += 1
        
        log(f"\n--- Iteration {iteration} ---")
        
        # Try Stage 1: Basic CSP
        log("Trying Stage 1 (Basic CSP)...")
        progress, details = try_stage_1(game, log_callback=log)
        if progress:
            log("  -> Stage 1 made progress, restarting from Stage 1")
            continue  # Restart from Stage 1
        
        # Stage 1 failed, try Stage 2: Pattern-based
        log("Trying Stage 2 (Pattern-based)...")
        progress, details = try_stage_2(game, log_callback=log)
        if progress:
            log("  -> Stage 2 made progress, restarting from Stage 1")
            continue  # Restart from Stage 1
        
        # Stage 2 failed, try Stage 3: Advanced CSP (NOT IMPLEMENTED)
        log("Trying Stage 3 (Advanced CSP)...")
        progress, details = try_stage_3(game, log_callback=log)
        if progress:
            log("  -> Stage 3 made progress, restarting from Stage 1")
            continue  # Restart from Stage 1
        
        # Stage 3 failed (or not implemented), try Stage 4: Probabilistic
        log("Trying Stage 4 (Probabilistic)...")
        progress, details = try_stage_4(game, 
                                        use_information_gain=use_information_gain, 
                                        safe_threshold=safe_threshold,
                                        log_callback=log)
        if progress:
            log("  -> Stage 4 made progress, restarting from Stage 1")
            continue  # Restart from Stage 1
        
        # All stages failed - no progress made
        log(f"\nNo progress made by any stage in iteration {iteration}")
        break
    
    # Determine final status
    log("\n" + "=" * 60)
    if game.game_over:
        state = game.current_state
        if state["status"] == "Won":
            success = True
            log("SOLVED: Game won!")
        else:
            success = False
            log("FAILED: Game lost!")
    else:
        success = False
        log(f"STUCK: Could not solve after {iteration} iterations")
    log("=" * 60)
    
    return success, history


# Convenience function for simple usage
def solve(game: Minesweeper, verbose: bool = False) -> bool:
    """
    Simple solver interface.
    
    Args:
        game: The Minesweeper game instance
        verbose: If True, print progress information
    
    Returns:
        True if game was won, False otherwise
    """
    success, _ = solve_minesweeper(game, verbose=verbose)
    return success


# Example usage
if __name__ == "__main__":
    # Example: Create and solve a game
    m = Minesweeper()
    m.start_new_game(width=10, height=10, mines=10, seed=1)
    
    # Make an initial click to generate the board
    m.reveal_cell(3, 3)
    
    print("Initial board state:")
    for row in m.current_state["board"]:
        print(row)
    print()
    
    # Solve the game
    success, history = solve_minesweeper(m, verbose=True)
    
    print("\nFinal board state:")
    for row in m.current_state["board"]:
        print(row)
    print()
    
    print(f"\nGame status: {m.current_state['status']}")
    print(f"Success: {success}")
    print(f"\nSolving history:")
    for entry in history:
        print(f"  {entry}")

