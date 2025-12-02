from minesweeper import Minesweeper
from helpers.patterns import ALL_PATTERNS, Pattern
from typing import Tuple, Optional, List, Any


def l2_step(game: Minesweeper):
    """
    Uses pattern-based reasoning to find guaranteed mines and safe cells.
    Matches geometric patterns from the pattern library and applies deductions:
    - Flags cells that must be mines
    - Reveals cells that must be safe

    game: An instance of the Minesweeper class.

    Returns "success" if an action was taken, "fail" if no safe actions found,
    should go to the next step.
    """

    state = game.current_state
    if state["status"] != "Playing":
        return "fail"

    board = state["board"]
    width = game.width
    height = game.height

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

    # Helper to match a pattern at a specific location
    def match_pattern_at(x: int, y: int, pattern: Pattern, rotation: int):
        """Try to match a pattern at board coordinate (x, y) as the pivot."""
        # Check constraints
        for (dx, dy), expected in pattern.constraints.items():
            rdx, rdy = rotate_cell(dx, dy, rotation)
            tx, ty = x + rdx, y + rdy

            # Out of bounds => no match
            if not (0 <= tx < width and 0 <= ty < height):
                return None

            cell_value = board[ty][tx]
            if not cell_matches_expected(cell_value, expected):
                return None

        # If we got here, constraints match. Compute absolute mines/safes.
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

    # Find the first pattern match that provides deductions
    for y in range(height):
        for x in range(width):
            for pattern in ALL_PATTERNS:
                for rotation in (0, 90, 180, 270):
                    match_result = match_pattern_at(x, y, pattern, rotation)
                    if match_result:
                        mines = match_result["mines"]
                        safes = match_result["safes"]

                        action_taken = False

                        # Flag all guaranteed mines (only if not already flagged/revealed)
                        for (mx, my) in mines:
                            cell_val = board[my][mx]
                            if cell_val == "_":
                                game.flag_cell(mx, my)
                                action_taken = True

                        # Reveal all guaranteed safe cells (only if not already revealed/flagged)
                        for (sx, sy) in safes:
                            cell_val = board[sy][sx]
                            if cell_val == "_":
                                game.reveal_cell(sx, sy)
                                action_taken = True

                        # Return success if any action was taken
                        if action_taken:
                            return "success"

    # No pattern found that deduces anything
    return "fail"

