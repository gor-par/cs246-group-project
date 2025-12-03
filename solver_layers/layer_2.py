from minesweeper import Minesweeper
from helpers.patterns import ALL_PATTERNS, Pattern
from typing import Tuple, Optional, List, Any, Set


def l2_step(game: Minesweeper):
    """
    Uses pattern-based reasoning to find guaranteed mines and safe cells.
    Matches geometric patterns from the pattern library and validates that
    the actual mine counts match the pattern logic before applying deductions.
    
    Only acts when it can reveal safe tiles (100% certain). If it can only
    flag mines, returns "fail" to let layer 3 try.

    game: An instance of the Minesweeper class.

    Returns "success" if a safe tile was revealed, "fail" if no safe actions found.
    """

    state = game.current_state
    if state["status"] != "Playing":
        return "fail"

    board = state["board"]
    width = game.width
    height = game.height

    # Helper to get valid neighbors
    def get_neighbors(x: int, y: int) -> List[Tuple[int, int]]:
        """Get all valid neighbors of a cell."""
        neighbors = []
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                nx, ny = x + dx, y + dy
                if 0 <= nx < width and 0 <= ny < height:
                    neighbors.append((nx, ny))
        return neighbors

    # Helper to count flags and hidden cells around a number
    def count_neighbors(x: int, y: int) -> Tuple[int, int, List[Tuple[int, int]]]:
        """
        Count flagged and hidden neighbors of a cell.
        Returns: (flag_count, hidden_count, hidden_list)
        """
        flags = 0
        hidden = []
        for nx, ny in get_neighbors(x, y):
            cell_val = board[ny][nx]
            if cell_val == "F":
                flags += 1
            elif cell_val == "_":
                hidden.append((nx, ny))
        return flags, len(hidden), hidden

    # Helper to rotate a relative coordinate
    def rotate_cell(dx: int, dy: int, rotation: int) -> Tuple[int, int]:
        """Rotate a relative coordinate (dx, dy) around (0,0) by rotation degrees."""
        if rotation == 0:
            return dx, dy
        elif rotation == 90:
            return -dy, dx
        elif rotation == 180:
            return -dx, -dy
        elif rotation == 270:
            return dy, -dx
        else:
            raise ValueError(f"Unsupported rotation: {rotation}")

    # Helper to check if a board cell matches expected pattern value
    def cell_matches_expected(board_cell: Any, expected: Any) -> bool:
        """Check if a board cell matches the expected symbol used in constraints."""
        if expected == "?":
            return True
        if expected == "U":
            return board_cell in ("_", "F")
        if expected == "F":
            return board_cell == "F"
        if isinstance(expected, int):
            return board_cell == expected
        return board_cell == expected

    # Helper to validate that a pattern's logic actually holds
    def validate_pattern_logic(x: int, y: int, pattern: Pattern, rotation: int) -> bool:
        """
        Validate that the pattern's logic is actually correct given the board state.
        This ensures that:
        1. All numbers in the pattern have the correct remaining mine counts
        2. The pattern's unopened cells are the ONLY unopened neighbors of relevant numbers
           (or at least account for the required mines)
        """
        # Get all number cells from constraints
        number_cells = []
        for (dx, dy), expected in pattern.constraints.items():
            if isinstance(expected, int):
                rdx, rdy = rotate_cell(dx, dy, rotation)
                tx, ty = x + rdx, y + rdy
                if 0 <= tx < width and 0 <= ty < height:
                    number_cells.append((tx, ty, expected))
        
        # Get all unopened cells that the pattern expects
        pattern_hidden = set()
        for (dx, dy), expected in pattern.constraints.items():
            if expected == "U":  # Unopened cell
                rdx, rdy = rotate_cell(dx, dy, rotation)
                tx, ty = x + rdx, y + rdy
                if 0 <= tx < width and 0 <= ty < height:
                    pattern_hidden.add((tx, ty))
        
        # For each number cell, verify the pattern logic holds
        for nx, ny, expected_number in number_cells:
            if not isinstance(board[ny][nx], int):
                return False
            
            actual_number = board[ny][nx]
            if actual_number != expected_number:
                return False
            
            # Count flags and hidden neighbors
            flag_count, hidden_count, hidden_list = count_neighbors(nx, ny)
            remaining_mines = actual_number - flag_count
            
            if remaining_mines < 0:
                return False
            
            # Get the pattern's unopened cells that are neighbors of this number
            number_neighbors = set(get_neighbors(nx, ny))
            pattern_neighbors = pattern_hidden.intersection(number_neighbors)
            
            # Critical validation: For patterns to be valid, the pattern's unopened cells
            # must be the ONLY unopened neighbors of the numbers involved.
            # This ensures the pattern logic is actually applicable.
            if set(hidden_list) != pattern_neighbors:
                # There are other unopened neighbors not accounted for by the pattern
                return False
            
            # Verify remaining_mines is consistent
            if remaining_mines > len(pattern_neighbors):
                return False
        
        return True

    # Helper to match and validate a pattern at a specific location
    def match_and_validate_pattern(x: int, y: int, pattern: Pattern, rotation: int):
        """
        Try to match a pattern at board coordinate (x, y) as the pivot.
        Returns None if pattern doesn't match or logic doesn't validate.
        """
        # First check geometric constraints
        for (dx, dy), expected in pattern.constraints.items():
            rdx, rdy = rotate_cell(dx, dy, rotation)
            tx, ty = x + rdx, y + rdy

            # Out of bounds => no match
            if not (0 <= tx < width and 0 <= ty < height):
                return None

            cell_value = board[ty][tx]
            if not cell_matches_expected(cell_value, expected):
                return None

        # If geometric match, validate the logic
        if not validate_pattern_logic(x, y, pattern, rotation):
            return None

        # If we got here, pattern matches and logic validates. Compute absolute mines/safes.
        mines_abs = []
        safes_abs = []

        for (dx, dy) in pattern.mines:
            rdx, rdy = rotate_cell(dx, dy, rotation)
            tx, ty = x + rdx, y + rdy
            if 0 <= tx < width and 0 <= ty < height:
                mines_abs.append((tx, ty))

        for (dx, dy) in pattern.safes:
            rdx, rdy = rotate_cell(dx, dy, rotation)
            tx, ty = x + rdx, y + rdy
            if 0 <= tx < width and 0 <= ty < height:
                safes_abs.append((tx, ty))

        if not mines_abs and not safes_abs:
            return None

        return {"mines": mines_abs, "safes": safes_abs}

    # Look for patterns that can reveal safe tiles (100% certain)
    # This is the priority - we want to reveal safe tiles when possible
    for y in range(height):
        for x in range(width):
            for pattern in ALL_PATTERNS:
                for rotation in (0, 90, 180, 270):
                    match_result = match_and_validate_pattern(x, y, pattern, rotation)
                    if match_result:
                        safes = match_result["safes"]

                        # Check if we can reveal any safe cells
                        safe_action_taken = False
                        for (sx, sy) in safes:
                            cell_val = board[sy][sx]
                            if cell_val == "_":
                                game.reveal_cell(sx, sy)
                                safe_action_taken = True

                        # If we revealed any safe cells, also flag any mines from this pattern
                        if safe_action_taken:
                            mines = match_result["mines"]
                            for (mx, my) in mines:
                                cell_val = board[my][mx]
                                if cell_val == "_":
                                    game.flag_cell(mx, my)
                            return "success"

    # No pattern found that can reveal safe tiles
    # Return "fail" to let layer 3 try, even if there are mines that could be flagged
    return "fail"
