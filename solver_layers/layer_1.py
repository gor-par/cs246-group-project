from minesweeper import Minesweeper


def l1_step(game: Minesweeper):
    """
    Applies basic Constraint Satisfaction Problem (CSP) rules.
    Rule A: If (number - flagged_neighbors) == hidden_neighbors,
            all hidden neighbors are mines -> flag them.
    Rule B: If number == flagged_neighbors,
            all hidden neighbors are safe -> reveal them.

    game: An instance of the Minesweeper class.

    Returns "success" if an action was taken, "fail" if no safe actions found,
    should go to the next step.
    """

    state = game.current_state
    board = state["board"]
    width = game.width
    height = game.height

    # Helper to get valid neighbors
    def get_neighbors(x, y):
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                nx, ny = x + dx, y + dy
                if 0 <= nx < width and 0 <= ny < height:
                    yield nx, ny

    for y in range(height):
        for x in range(width):
            cell = board[y][x]

            # We only care about revealed number cells
            # Hidden "_" and "F" and anything non-int are ignored
            if not isinstance(cell, int):
                continue

            number = cell
            hidden_neighbors = []
            flagged_neighbors = []

            for nx, ny in get_neighbors(x, y):
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
                    game.flag_cell(nx, ny)
                return "success"

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
                    game.reveal_cell(nx, ny)
                return "success"

    # If we went through all cells and found no 100% certain moves
    return "fail"

