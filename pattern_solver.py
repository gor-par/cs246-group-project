"""
pattern_solver.py

High-level driver that uses:
    - minesweeper.Minesweeper
    - pattern_detector.one_step_for_game

to actually MODIFY the game state:

- Flags cells that must be mines (using game.flag_cell)
- Reveals cells that must be safe (using game.reveal_cell)

This is the "AI move" layer that sits on top of:
    - minesweeper.py
    - patterns.py
    - pattern_detector.py
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple, Optional, Any

from pattern_detector import one_step_for_game, PatternMatch
from minesweeper import Minesweeper  # your implementation

Cell = Tuple[int, int]


@dataclass
class StepResult:
    """
    One AI step summary.

    pattern:  which pattern was used (or None if nothing found)
    mines:    list of (x, y) the solver flagged as mines
    safes:    list of (x, y) the solver revealed as safe
    game_status: "Playing", "Won" or "Lost" (from game.current_state["status"])
    """
    pattern: Optional[PatternMatch]
    mines: List[Cell]
    safes: List[Cell]
    game_status: str


def apply_one_pattern_step_to_game(game: Minesweeper) -> StepResult:
    """
    Perform exactly ONE pattern-based reasoning step on the Minesweeper game.

    - Uses pattern_detector.one_step_for_game(game) to find the first
      pattern that deduces something (mines/safes).
    - Flags those mines with game.flag_cell(x, y).
    - Reveals those safes with game.reveal_cell(x, y).

    Returns:
        StepResult with details. If no pattern was found, pattern is None and
        mines/safes are empty.
    """
    # If game already over, do nothing
    state = game.current_state
    if state["status"] != "Playing":
        return StepResult(
            pattern=None,
            mines=[],
            safes=[],
            game_status=state["status"],
        )

    match, mines, safes = one_step_for_game(game)

    flagged: List[Cell] = []
    revealed: List[Cell] = []

    if match is None:
        # No pattern found that deduces anything
        state = game.current_state
        return StepResult(
            pattern=None,
            mines=[],
            safes=[],
            game_status=state["status"],
        )

    # 1) Flag all guaranteed mines
    for (x, y) in mines:
        # Only try to flag if it's not already revealed as a number
        # (in your implementation, "_" or "F" are unrevealed-like states)
        cell_val = game.current_board[y][x]
        if cell_val == "F":
            # already flagged, fine
            flagged.append((x, y))
            continue
        if cell_val != "_":
            # already revealed number or something else; skip
            continue

        game.flag_cell(x, y)
        flagged.append((x, y))

    # 2) Reveal all guaranteed safe cells
    for (x, y) in safes:
        # Don't reveal flags or already revealed cells
        cell_val = game.current_board[y][x]
        if cell_val in ("F", "M") or isinstance(cell_val, int):
            continue

        result = game.reveal_cell(x, y)
        revealed.append((x, y))

        # If we somehow hit "DEFEAT" (shouldn't happen if pattern is correct),
        # break early.
        if result == "DEFEAT":
            break

    state = game.current_state
    return StepResult(
        pattern=match,
        mines=flagged,
        safes=revealed,
        game_status=state["status"],
    )


def solve_with_patterns(
    game: Minesweeper,
    max_steps: int = 100,
) -> List[StepResult]:
    """
    Repeatedly apply pattern-based steps until:

    - game is no longer "Playing" (won or lost), or
    - no more patterns can deduce anything, or
    - max_steps is reached.

    Returns:
        A list of StepResult objects in the order the steps were applied.
    """
    history: List[StepResult] = []

    for _ in range(max_steps):
        state = game.current_state
        if state["status"] != "Playing":
            break

        step = apply_one_pattern_step_to_game(game)
        history.append(step)

        # If this step didn't do anything (no pattern or no moves), stop
        if step.pattern is None or (not step.mines and not step.safes):
            break

        # If game ended (win/lose) after this step, also stop
        if step.game_status != "Playing":
            break

    return history


# Optional quick demo
if __name__ == "__main__":
    # Tiny demo of how to use this with your Minesweeper class

    m = Minesweeper()
    m.start_new_game(width=10, height=10, mines=10, seed=1)

    # Make an initial click so the board is generated
    m.reveal_cell(3, 3)

    print("Initial visible board:")
    for row in m.current_state["board"]:
        print(row)

    steps = solve_with_patterns(m, max_steps=50)

    print("\nAfter pattern-based solving:")
    for row in m.current_state["board"]:
        print(row)

    print("\nSteps taken:")
    for i, s in enumerate(steps, start=1):
        pid = s.pattern.pattern.short_id if s.pattern else None
        print(
            f"Step {i}: pattern={pid}, "
            f"mines={s.mines}, safes={s.safes}, status={s.game_status}"
        )
