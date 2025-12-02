"""
Hybrid Solver for Minesweeper

Cycles through layers 1-4 sequentially, restarting from layer 1 when any layer succeeds.
Tracks all actions taken and which layer recommended each action.
"""

from minesweeper import Minesweeper
from solver_layers.layer_1 import l1_step
from solver_layers.layer_2 import l2_step
from solver_layers.layer_3 import l3_step
from solver_layers.layer_4 import l4_step
from typing import List, Dict, Tuple, Optional
import copy


class ActionRecord:
    """Represents a single action taken by the solver."""
    
    def __init__(self, action_type: str, x: int, y: int, layer: int):
        """
        Initialize an action record.
        
        Args:
            action_type: Type of action - "REVEAL" or "FLAG"
            x: X coordinate of the action
            y: Y coordinate of the action
            layer: Which layer (1-4) recommended this action
        """
        self.action_type = action_type
        self.x = x
        self.y = y
        self.layer = layer
    
    def __repr__(self):
        return f"ActionRecord({self.action_type}, ({self.x}, {self.y}), Layer {self.layer})"
    
    def __str__(self):
        return f"Layer {self.layer}: {self.action_type} ({self.x}, {self.y})"


def get_board_snapshot(board: List[List]) -> Dict[Tuple[int, int], str]:
    """
    Create a snapshot of the board state as a dictionary.
    
    Args:
        board: The game board (2D list)
        
    Returns:
        Dictionary mapping (x, y) coordinates to cell values
    """
    snapshot = {}
    for y in range(len(board)):
        for x in range(len(board[y])):
            snapshot[(x, y)] = board[y][x]
    return snapshot


def find_board_changes(before: Dict[Tuple[int, int], str], 
                       after: Dict[Tuple[int, int], str]) -> List[ActionRecord]:
    """
    Compare two board snapshots and identify what changed.
    
    Args:
        before: Board snapshot before an action
        after: Board snapshot after an action
        
    Returns:
        List of ActionRecord objects representing the changes
        Note: Layer number is not set here, it should be set by the caller
    """
    changes = []
    
    for (x, y), after_value in after.items():
        before_value = before.get((x, y), None)
        
        if before_value == after_value:
            continue
        
        # Cell changed from hidden/flagged to revealed (number or 0)
        if before_value in ("_", "F") and isinstance(after_value, int):
            changes.append(ActionRecord("REVEAL", x, y, 0))  # Layer set later
        # Cell changed from hidden to flagged
        elif before_value == "_" and after_value == "F":
            changes.append(ActionRecord("FLAG", x, y, 0))  # Layer set later
    
    return changes


def solve_with_tracking(game: Minesweeper, 
                       max_iterations: int = 10000,
                       l4_use_information_gain: bool = False,
                       l4_safe_threshold: float = 0.35) -> Tuple[List[ActionRecord], bool]:
    """
    Solve a Minesweeper game using hybrid approach cycling through layers 1-4.
    
    Strategy:
    - Try Layer 1 (basic CSP rules)
    - If Layer 1 fails, try Layer 2 (pattern matching)
    - If Layer 2 fails, try Layer 3 (advanced CSP)
    - If Layer 3 fails, try Layer 4 (probabilistic)
    - When any layer succeeds, restart from Layer 1
    - Continue until game is won, lost, or no progress can be made
    
    Args:
        game: An instance of the Minesweeper class
        max_iterations: Maximum number of iteration cycles to prevent infinite loops
        l4_use_information_gain: Whether to use information gain for Layer 4
        l4_safe_threshold: Safe threshold for Layer 4 (default 0.35)
        
    Returns:
        Tuple of (action_history, solved):
        - action_history: List of ActionRecord objects in the order they were taken
        - solved: True if game was won, False if lost or unsolvable
    """
    action_history = []
    iteration_count = 0
    
    while iteration_count < max_iterations:
        iteration_count += 1
        
        # Check game status
        state = game.current_state
        if state["status"] != "Playing":
            solved = (state["status"] == "Won")
            return action_history, solved
        
        # Get board snapshot before trying any layer
        board_before = get_board_snapshot(state["board"])
        
        # Try Layer 1
        result = l1_step(game)
        state_after = game.current_state
        board_after = get_board_snapshot(state_after["board"])
        changes = find_board_changes(board_before, board_after)
        
        if result == "success" and changes:
            # Layer 1 succeeded - record actions and restart from Layer 1
            for change in changes:
                change.layer = 1
                action_history.append(change)
            continue  # Restart from Layer 1
        
        # Layer 1 failed, try Layer 2
        board_before = get_board_snapshot(state_after["board"])
        result = l2_step(game)
        state_after = game.current_state
        board_after = get_board_snapshot(state_after["board"])
        changes = find_board_changes(board_before, board_after)
        
        if result == "success" and changes:
            # Layer 2 succeeded - record actions and restart from Layer 1
            for change in changes:
                change.layer = 2
                action_history.append(change)
            continue  # Restart from Layer 1
        
        # Layer 2 failed, try Layer 3
        board_before = get_board_snapshot(state_after["board"])
        result = l3_step(game)
        state_after = game.current_state
        board_after = get_board_snapshot(state_after["board"])
        changes = find_board_changes(board_before, board_after)
        
        if result == "success" and changes:
            # Layer 3 succeeded - record actions and restart from Layer 1
            for change in changes:
                change.layer = 3
                action_history.append(change)
            continue  # Restart from Layer 1
        
        # Layer 3 failed, try Layer 4
        board_before = get_board_snapshot(state_after["board"])
        result = l4_step(game, 
                        use_information_gain=l4_use_information_gain,
                        safe_threshold=l4_safe_threshold)
        state_after = game.current_state
        board_after = get_board_snapshot(state_after["board"])
        changes = find_board_changes(board_before, board_after)
        
        if result == "success" and changes:
            # Layer 4 succeeded - record actions and restart from Layer 1
            for change in changes:
                change.layer = 4
                action_history.append(change)
            continue  # Restart from Layer 1
        
        # All layers failed - no progress can be made
        break
    
    # Final game status
    final_state = game.current_state
    solved = (final_state["status"] == "Won")
    
    return action_history, solved


def solve_minesweeper(game: Minesweeper,
                     max_iterations: int = 10000,
                     l4_use_information_gain: bool = False,
                     l4_safe_threshold: float = 0.35) -> Dict:
    """
    Main entry point for the hybrid solver.
    
    Args:
        game: An instance of the Minesweeper class
        max_iterations: Maximum number of iteration cycles
        l4_use_information_gain: Whether to use information gain for Layer 4
        l4_safe_threshold: Safe threshold for Layer 4
        
    Returns:
        Dictionary with:
        - "actions": List of ActionRecord objects
        - "solved": Boolean indicating if game was won
        - "final_status": Final game status ("Won", "Lost", or "Playing")
        - "iterations": Number of iterations performed
        - "action_summary": Dictionary summarizing actions by layer
    """
    action_history, solved = solve_with_tracking(
        game,
        max_iterations=max_iterations,
        l4_use_information_gain=l4_use_information_gain,
        l4_safe_threshold=l4_safe_threshold
    )
    
    final_state = game.current_state
    
    # Create action summary by layer
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
    
    return {
        "actions": action_history,
        "solved": solved,
        "final_status": final_state["status"],
        "iterations": len(action_history),
        "action_summary": action_summary
    }


def print_action_history(result: Dict, detailed: bool = False):
    """
    Print the action history in a readable format.
    
    Args:
        result: Result dictionary from solve_minesweeper
        detailed: If True, print every action; if False, print summary only
    """
    print(f"\n{'='*60}")
    print(f"HYBRID SOLVER RESULTS")
    print(f"{'='*60}")
    print(f"Final Status: {result['final_status']}")
    print(f"Total Actions: {result['iterations']}")
    print(f"\nAction Summary by Layer:")
    
    summary = result['action_summary']
    for layer in [1, 2, 3, 4]:
        layer_data = summary[layer]
        if layer_data["total"] > 0:
            print(f"  Layer {layer}: "
                  f"{layer_data['REVEAL']} reveals, "
                  f"{layer_data['FLAG']} flags, "
                  f"{layer_data['total']} total")
        else:
            print(f"  Layer {layer}: No actions")
    
    if detailed and result['actions']:
        print(f"\nDetailed Action Sequence:")
        print(f"{'='*60}")
        for i, action in enumerate(result['actions'], 1):
            print(f"  {i:4d}. {action}")
    
    print(f"{'='*60}\n")

