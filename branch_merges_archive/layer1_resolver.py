import random
from minesweeper import Minesweeper


class MinesweeperSolver:
    def __init__(self, game: Minesweeper):
        """
        game: an already-initialized Minesweeper instance
              (start_new_game has been called, and usually at least one cell revealed)
        """
        self.game = game

    # ---------- helpers ----------

    def get_neighbors(self, x, y):
        """Return list of (nx, ny) neighbor coordinates inside the board."""
        state = self.game.current_state
        board = state["board"]
        height = len(board)
        width = len(board[0])

        neighbors = []
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                nx, ny = x + dx, y + dy
                if 0 <= nx < width and 0 <= ny < height:
                    neighbors.append((nx, ny))
        return neighbors

    # ---------- basic CSP rules (your step 1 & 2) ----------

    def _apply_rules_once(self) -> bool:
        """
        Do one full pass over the board applying the two basic rules:

        Rule A (flag mines):
          If (number - flagged_neighbors) == hidden_neighbors:
              -> all hidden neighbors are mines -> flag them.

        Rule B (reveal safe cells):
          If number == flagged_neighbors:
              -> all hidden neighbors are safe -> reveal them.

        Returns True ONLY if at least one NEW cell was flagged or revealed.
        Returns False if no actions can be taken with 100% certainty.
        """
        state = self.game.current_state
        board = state["board"]

        height = len(board)
        width = len(board[0])

        changed = False

        # We iterate over a snapshot of the board, but note:
        # board is actually the same list as game.current_board,
        # so calling reveal_cell/flag_cell updates it in-place.
        for y in range(height):
            for x in range(width):
                cell = board[y][x]

                # We only care about *revealed number* cells.
                # Hidden "_" and "F" and anything non-int are ignored.
                if not isinstance(cell, int):
                    continue

                number = cell
                neighbors = self.get_neighbors(x, y)

                hidden_neighbors = []
                flagged_neighbors = []

                for nx, ny in neighbors:
                    ncell = board[ny][nx]
                    if ncell == "_":
                        hidden_neighbors.append((nx, ny))
                    elif ncell == "F":
                        flagged_neighbors.append((nx, ny))

                if not hidden_neighbors:
                    # Nothing to do if there are no hidden cells around this number
                    continue

                mines_total = number
                flags = len(flagged_neighbors)
                hidden = len(hidden_neighbors)

                # Validation: flags should never exceed mines_total
                # If this happens, there's a bug elsewhere, but we should not flag more
                if flags > mines_total:
                    # Invalid state - more flags than mines required
                    # This should never happen with correct logic, but skip to avoid errors
                    continue

                # ---------------- Rule A: all remaining hidden must be mines ----------------
                # Mines still to place around this number:
                remaining_mines = mines_total - flags
                # Only flag if remaining_mines is positive and equals hidden count
                # This ensures 100% certainty: ALL hidden neighbors MUST be mines
                if remaining_mines == hidden and remaining_mines > 0 and hidden > 0:
                    # All hidden neighbors are mines -> flag them
                    for nx, ny in hidden_neighbors:
                        # Check if cell is still hidden before flagging
                        if board[ny][nx] != "_":
                            # Cell was already revealed/flagged by previous action, skip
                            continue
                        # flag_cell will do nothing if already revealed, but we check above
                        res = self.game.flag_cell(nx, ny)
                        if res == "FLAG":
                            changed = True
                    # after flagging, move on to next cell
                    continue

                # ---------------- Rule B: all hidden neighbors are safe ----------------
                # If all mines already accounted for by flags -> remaining hidden are safe
                # This ensures 100% certainty: ALL hidden neighbors MUST be safe
                if mines_total == flags and hidden > 0:
                    for nx, ny in hidden_neighbors:
                        # Check if cell is still hidden before revealing
                        if board[ny][nx] != "_":
                            # Cell was already revealed/flagged by previous action, skip
                            continue
                        # reveal_cell will handle recursion for 0s
                        res = self.game.reveal_cell(nx, ny)
                        if res in ("SUCCESS", "REPEAT"):
                            changed = True
                        elif res in ("DEFEAT", "VICTORY"):
                            # Game ended; still count as progress, but we can stop early
                            changed = True
                            return changed

        return changed

    def solve_deterministic(self) -> Minesweeper:
        """
        Keep applying the basic rules (1 & 2) until no more moves are possible.

        Returns the (modified) Minesweeper object.
        """
        # Repeat until a full pass finds no new flags/reveals
        while not self.game.game_over:
            did_change = self._apply_rules_once()
            if not did_change:
                break

        return self.game


# Convenience function if you prefer a functional style:
def apply_basic_csp(game: Minesweeper) -> Minesweeper:
    """
    Apply only the basic deterministic CSP rules (steps 1 & 2)
    to the given game, until no valid move is left.

    Returns the same game object after modification.
    """
    solver = MinesweeperSolver(game)
    return solver.solve_deterministic()
