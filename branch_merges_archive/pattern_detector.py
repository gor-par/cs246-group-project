"""
pattern_detector.py

Pattern-based Minesweeper helper.

Uses the geometric templates from patterns.py and tries to match them
on a given visible board. For each match, it returns cells that are
guaranteed mines and cells that are guaranteed safe.

Designed to work with:
- minesweeper.py      (Ani's game implementation)
- patterns.py         (pattern library we built)

Board convention (matches your Minesweeper.current_board):
- int 0–8 : revealed numbers
- "M"     : revealed mine (only after losing)
- "_"     : unrevealed
- "F"     : flagged mine

Pattern convention (from patterns.py):
- constraints: (dx, dy) -> expected:
    * int 0–8 : must equal that number
    * "U"     : unopened cell ("_" or "F")
    * "F"     : flagged mine
    * "?"     : don't care
- mines / safes: relative cells that MUST be mines or safe
  if the pattern matches.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple, Any, Iterable, Set, Optional


from patterns import ALL_PATTERNS, Pattern

try:
    from minesweeper import Minesweeper  # type: ignore
except ImportError:
    # Optional: pattern_detector can still be used directly on matrices
    Minesweeper = None  # type: ignore


Cell = Tuple[int, int]


# ========= Rotation utilities =========

def rotate_cell(dx: int, dy: int, rotation: int) -> Cell:
    """
    Rotate a relative coordinate (dx, dy) around (0,0) by rotation degrees.
    rotation must be one of {0, 90, 180, 270}.
    """
    if rotation == 0:
        return dx, dy
    elif rotation == 90:
        # (x,y) -> (-y, x)
        return -dy, dx
    elif rotation == 180:
        return -dx, -dy
    elif rotation == 270:
        # (x,y) -> (y, -x)
        return dy, -dx
    else:
        raise ValueError(f"Unsupported rotation: {rotation}")


@dataclass
class PatternMatch:
    """Represents a single successful pattern match on a board."""
    pattern: Pattern
    pivot: Cell          # absolute board coordinates of pivot
    rotation: int        # 0, 90, 180, or 270
    mines: List[Cell]    # cells that must be mines
    safes: List[Cell]    # cells that must be safe


# ========= Core matching logic =========

def _cell_matches_expected(board_cell: Any, expected: Any) -> bool:
    """
    Check if a board cell matches the expected symbol used in constraints.
    """
    if expected == "?":
        return True

    # Unopened cell (we accept both "_" and "F" as 'not revealed')
    if expected == "U":
        return board_cell in ("_", "F")

    if expected == "F":
        return board_cell == "F"

    if isinstance(expected, int):
        return board_cell == expected

    # Fallback: exact match
    return board_cell == expected


def match_pattern_at(
    board: List[List[Any]],
    x: int,
    y: int,
    pattern: Pattern,
    rotation: int,
) -> PatternMatch | None:
    """
    Try to match a pattern at board coordinate (x, y) as the pivot,
    with a given rotation. If it matches, return a PatternMatch; otherwise None.
    """
    height = len(board)
    if height == 0:
        return None
    width = len(board[0])

    # First, check constraints
    for (dx, dy), expected in pattern.constraints.items():
        rdx, rdy = rotate_cell(dx, dy, rotation)
        tx, ty = x + rdx, y + rdy

        # Out of bounds => no match
        if not (0 <= tx < width and 0 <= ty < height):
            return None

        cell_value = board[ty][tx]
        if not _cell_matches_expected(cell_value, expected):
            return None

    # If we got here, constraints match. Now compute absolute mines/safes.
    mines_abs: List[Cell] = []
    safes_abs: List[Cell] = []

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
        # Technically still a pattern match, but no direct deduction.
        # You can keep or drop it. We'll keep it.
        pass

    return PatternMatch(
        pattern=pattern,
        pivot=(x, y),
        rotation=rotation,
        mines=mines_abs,
        safes=safes_abs,
    )


def detect_pattern_matches(
    board: List[List[Any]],
    patterns: Iterable[Pattern] = ALL_PATTERNS,
    rotations: Iterable[int] = (0, 90, 180, 270),
) -> List[PatternMatch]:
    """
    Scan the whole board and return all pattern matches.

    board: 2D list like Minesweeper.current_state["board"].
    """
    height = len(board)
    if height == 0:
        return []
    width = len(board[0])

    matches: List[PatternMatch] = []

    for y in range(height):
        for x in range(width):
            for pattern in patterns:
                for rot in rotations:
                    m = match_pattern_at(board, x, y, pattern, rot)
                    if m is not None:
                        # Optional small optimization: ignore matches that do not
                        # deduce anything new (no mines, no safes).
                        if not m.mines and not m.safes:
                            continue
                        matches.append(m)
    return matches


def aggregate_deductions(
    board: List[List[Any]],
    patterns: Iterable[Pattern] = ALL_PATTERNS,
) -> Tuple[Set[Cell], Set[Cell], List[PatternMatch]]:
    """
    Run pattern detection and aggregate all deduced mines and safes.

    Returns:
        mines_to_flag: set of coordinates that must be mines
        safes_to_open: set of coordinates that must be safe
        matches:       list of PatternMatch objects that produced these
    """
    matches = detect_pattern_matches(board, patterns=patterns)

    mines_to_flag: Set[Cell] = set()
    safes_to_open: Set[Cell] = set()

    for m in matches:
        for c in m.mines:
            mines_to_flag.add(c)
        for c in m.safes:
            safes_to_open.add(c)

    return mines_to_flag, safes_to_open, matches


# ========= Convenience helpers for your Minesweeper class =========

def suggest_moves_for_game(game) -> Tuple[Set[Cell], Set[Cell], List[PatternMatch]]:
    """
    Convenience wrapper that works directly with your Minesweeper instance.

    Usage:
        m = Minesweeper()
        m.start_new_game(...)
        ...
        mines, safes, matches = suggest_moves_for_game(m)

    It uses the *current visible board* (m.current_state["board"]).
    """
    state = game.current_state
    board = state["board"]
    return aggregate_deductions(board)


def one_step_for_game(
    game,
) -> Tuple[Optional[PatternMatch], List[Cell], List[Cell]]:
    """
    Find the first pattern match that deduces something (mines or safes).

    Returns:
        (match, mines, safes) where:
        - match: PatternMatch object if a pattern was found, None otherwise
        - mines: list of (x, y) cells that must be mines
        - safes: list of (x, y) cells that must be safe

    This function returns only the FIRST pattern that provides deductions,
    useful for step-by-step solving.
    """
    state = game.current_state
    board = state["board"]
    
    # Get all pattern matches
    matches = detect_pattern_matches(board)
    
    # Find the first match that has deductions
    for match in matches:
        if match.mines or match.safes:
            # Return the first match with deductions
            return match, list(match.mines), list(match.safes)
    
    # No pattern found that deduces anything
    return None, [], []


# Optional: if you want a quick CLI test
if __name__ == "__main__":
    # Minimal smoke test / example usage.
    # You can comment this out if you don't want any side effects.
    if Minesweeper is None:
        print("Minesweeper class not available; run this only inside your project.")
    else:
        m = Minesweeper()
        m.start_new_game(width=8, height=8, mines=10, seed=42)
        # simulate one click so board is generated
        m.reveal_cell(0, 0)
        mines, safes, matches = suggest_moves_for_game(m)
        print("Mines to flag:", mines)
        print("Safes to open:", safes)
        print("Found matches:", [(mm.pattern.short_id, mm.pivot, mm.rotation) for mm in matches])
