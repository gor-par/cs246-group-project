"""
patterns.py

Library of local Minesweeper patterns (geometric templates) based on
https://minesweeper.online/help/patterns

This module only contains patterns that are naturally expressible as
fixed local layouts:

- Basic line patterns: 1-1, 1-1+, 1-2, 1-2+, 1-2C, 1-2C+, 1-2-1, 1-2-2-1
- Hole patterns: H1, H2, H3

Global rules (like B1/B2, endgame counting, etc.) should be implemented
directly in the solver, not here.

Coordinate convention for constraints / mines / safes:
- Relative coordinates (dx, dy) around a pivot cell (0, 0)
- dy > 0 is “down”, dy < 0 is “up”
- dx > 0 is “right”, dx < 0 is “left”
"""

from dataclasses import dataclass
from typing import Dict, Tuple, List, Any, Literal, Optional

Cell = Tuple[int, int]


@dataclass
class Pattern:
    # Human metadata
    name: str                      # e.g. "1-2-1"
    code: str                      # e.g. "M1–2–1"
    category: Literal["basic", "holes"]
    cells_count: Optional[int]     # "(4)" etc. from the website, if given
    short_id: str                  # e.g. "1-2-1", "h1"
    description: str               # explanation in plain language

    # Logic-related fields for pattern matching
    #
    # constraints: (dx, dy) -> expected symbol on the current board
    #   - int (0–8): exact number
    #   - "U": unopened cell (your "_" cells)
    #   - "F": flagged mine (if you want to require a flag)
    #   - "?": don't care
    #
    # mines / safes:
    #   list of (dx, dy) that must be mines / safe if the pattern matches.
    constraints: Dict[Cell, Any]
    mines: List[Cell]
    safes: List[Cell]
    pivot: Cell = (0, 0)


# ========== BASIC PATTERNS ==========

BASIC_PATTERNS: List[Pattern] = [

    # --- 1–1 --------------------------------------------------------------

    Pattern(
        name="1-1",
        short_id="1-1",
        code="M1–1",
        category="basic",
        cells_count=4,
        description=(
            "Classic flat 1–1 pattern. Two adjacent 1s share exactly two unopened "
            "cells above them. Those two cells must contain the single mine that "
            "satisfies both 1s, so the third cell above the right 1 is safe."
        ),
        # Layout (pivot = middle 1 at (0,0)):
        #
        #   (-1,-1)  (0,-1)  (1,-1)
        #       Y       Y       G
        #   (-1, 0)  (0, 0)  (1, 0)
        #       1       1       1
        constraints={
            (0, 0): 1,     # pivot (middle 1)
            (-1, 0): 1,    # left 1
            (1, 0): 1,     # right 1

            (-1, -1): "U", # yellow (mine)
            (0, -1): "U",  # yellow (mine)
            (1, -1): "U",  # green (safe)
        },
        mines=[(-1, -1), (0, -1)],
        safes=[(1, -1)],
    ),

    # --- 1–1+ -------------------------------------------------------------

    Pattern(
        name="1-1+ (extended)",
        short_id="1-1p",
        code="M1–1+",
        category="basic",
        cells_count=4,
        description=(
            "Extended 1–1 pattern. Two adjacent 1s share a pair of unopened cells "
            "that must contain the mine used by both 1s. Since the right 1 already "
            "uses that mine, every other unopened cell it touches in this pattern "
            "is guaranteed safe."
        ),
        # Same base as 1–1, plus a column of extra safe cells under the green one.
        # Pivot = middle 1 at (0,0).
        constraints={
            (-1, 0): 1,
            (0, 0): 1,
            (1, 0): 1,

            (-1, -1): "U",  # yellow
            (0, -1): "U",   # yellow
            (1, -1): "U",   # top safe

            (1, 1): "U",    # lower safe neighbors of right 1
            (1, 2): "U",
        },
        mines=[(-1, -1), (0, -1)],
        safes=[(1, -1), (1, 1), (1, 2)],
    ),

    # --- 1–2 --------------------------------------------------------------

    Pattern(
        name="1-2",
        short_id="1-2",
        code="M1–2",
        category="basic",
        cells_count=4,
        description=(
            "1–2 pattern. The 1 touches two unopened cells (yellow), which together "
            "must contain exactly one mine. The 2 touches those same two cells plus "
            "a third cell; that third cell must be the second mine."
        ),
        # Pivot = the 2 at (0,0).
        #
        #   (-1,-1)  (0,-1)  (1,-1)
        #       Y       Y       M
        #   (-1, 0)  (0, 0)  (1, 0)
        #       1       2       1
        constraints={
            (-1, 0): 1,
            (0, 0): 2,
            (1, 0): 1,

            (-1, -1): "U",
            (0, -1): "U",
            (1, -1): "U",   # forced mine
        },
        mines=[(1, -1)],
        safes=[],
    ),

    # --- 1–2+ -------------------------------------------------------------

    Pattern(
        name="1-2+ (extended)",
        short_id="1-2p",
        code="M1–2+",
        category="basic",
        cells_count=4,
        description=(
            "Extended 1–2 pattern. The 1 touches two unopened cells (yellow) that "
            "contain exactly one mine. The larger number (e.g. 4) also sees those "
            "cells and still needs three more mines, and it has exactly three "
            "additional unopened neighbors in this configuration. All three of "
            "those must be mines."
        ),
        # Pivot = larger number (4) at (0,0).
        #
        #   (-1,-1)  (0,-1)  (1,-1)
        #       Y       Y       M
        #   (-1, 0)  (0, 0)  (1, 0)
        #       1       4       M
        #                  (1, 1)=M
        #                  (1, 2)=M
        constraints={
            (-1, 0): 1,
            (0, 0): 4,

            (-1, -1): "U",
            (0, -1): "U",

            (1, -1): "U",
            (1, 0): "U",
            (1, 1): "U",
            (1, 2): "U",
        },
        mines=[(1, -1), (1, 0), (1, 1), (1, 2)],
        safes=[],
    ),

    # --- 1–2C -------------------------------------------------------------

    Pattern(
        name="1-2C (classic)",
        short_id="1-2c",
        code="M1–2C",
        category="basic",
        cells_count=4,
        description=(
            "Classic 1–2 pattern with a constrained pair. The 1 touches two purple "
            "cells, so they can contain at most one mine. The 2 touches those same "
            "two cells plus one extra cell; that extra cell must be a mine."
        ),
        # Pivot = the 1 at (0,0).
        #
        #   (-1,-1)  (0,-1)  (1,-1)
        #       P       P       M
        #         0,0=1   1,0=2
        constraints={
            (0, 0): 1,
            (1, 0): 2,

            (-1, -1): "U",  # purple
            (0, -1): "U",   # purple
            (1, -1): "U",   # forced mine
        },
        mines=[(1, -1)],
        safes=[],
    ),

    # --- 1–2C+ ------------------------------------------------------------

    Pattern(
        name="1-2C+ (classic extended)",
        short_id="1-2cp",
        code="M1–2C+",
        category="basic",
        cells_count=4,
        description=(
            "Extended classic 1–2 pattern. The 1 touches two purple cells, which "
            "can contain at most one mine. The larger number (e.g. 4) touches those "
            "cells plus three other unopened cells; those three must all be mines."
        ),
        # Pivot = 1 at (0,0), big number at (1,0).
        constraints={
            (0, 0): 1,
            (1, 0): 4,

            (-1, -1): "U",  # purple
            (0, -1): "U",   # purple

            (1, -1): "U",   # three forced mines
            (1, 1): "U",
            (1, 2): "U",
        },
        mines=[(1, -1), (1, 1), (1, 2)],
        safes=[],
    ),

    # --- 1–2–1 ------------------------------------------------------------

    Pattern(
        name="1-2-1",
        short_id="1-2-1",
        code="M1–2–1",
        category="basic",
        cells_count=3,
        description=(
            "1–2–1 pattern. Each outer 1 must take exactly one mine. Those two "
            "mines already satisfy the middle 2, so the two cells above the outer "
            "1s are mines."
        ),
        # Pivot = the 2 at (0,0).
        #
        #   (-1,-1)     (0,-1)     (1,-1)
        #      M           ?          M
        #   (-1, 0)     (0, 0)     (1, 0)
        #      1           2          1
        constraints={
            (-1, 0): 1,
            (0, 0): 2,
            (1, 0): 1,

            (-1, -1): "U",
            (0, -1): "U",
            (1, -1): "U",
        },
        mines=[(-1, -1), (1, -1)],
        safes=[],
    ),

    # --- 1–2–2–1 ----------------------------------------------------------

    Pattern(
        name="1-2-2-1",
        short_id="1-2-2-1",
        code="M1–2–2–1",
        category="basic",
        cells_count=3,
        description=(
            "1–2–2–1 pattern. The outer 1s each have a single candidate directly "
            "above them, so those two cells are mines. These two mines already "
            "satisfy both 2s, giving a unique pair of outer-top mines."
        ),
        # Pivot = left 2 at (0,0).
        #
        #  (-1,-1) (0,-1) (1,-1) (2,-1)
        #     M      U      U      M
        #  (-1, 0) (0, 0) (1, 0) (2, 0)
        #     1      2      2      1
        constraints={
            (-1, 0): 1,
            (0, 0): 2,
            (1, 0): 2,
            (2, 0): 1,

            (-1, -1): "U",
            (0, -1): "U",
            (1, -1): "U",
            (2, -1): "U",
        },
        mines=[(-1, -1), (2, -1)],
        safes=[],
    ),
]


# ========== HOLE PATTERNS ==========

HOLE_PATTERNS: List[Pattern] = [

    # --- H1 ---------------------------------------------------------------

    Pattern(
        name="Hole 1",
        short_id="h1",
        code="HH1",
        category="holes",
        cells_count=4,
        description=(
            "Hole pattern H1. The bottom 1 touches the two yellow cells, which "
            "together contain exactly one mine. The top 1 touches the same yellow "
            "cells, so that mine already satisfies it. All three cells above the "
            "hole (green) are therefore safe."
        ),
        # Pivot = top 1 at (0,0).
        #
        #   (-1,-1)  (0,-1)  (1,-1)   -> green (safe)
        #   (-1, 0)  (0, 0)  (1, 0)   -> yellow, 1, yellow
        #              (0, 1)         -> bottom 1
        constraints={
            (0, 0): 1,
            (0, 1): 1,

            (-1, 0): "U",
            (1, 0): "U",

            (-1, -1): "U",
            (0, -1): "U",
            (1, -1): "U",
        },
        mines=[],
        safes=[(-1, -1), (0, -1), (1, -1)],
    ),

    # --- H2 ---------------------------------------------------------------

    Pattern(
        name="Hole 2",
        short_id="h2",
        code="HH2",
        category="holes",
        cells_count=4,
        description=(
            "Hole pattern H2. Again the lower 1 touches two yellow cells that "
            "contain exactly one mine, and the middle 1 touches the same pair. "
            "As in H1, the row of green cells above the structure is guaranteed safe."
        ),
        # Pivot = middle 1 at (0,0).
        constraints={
            # Safe green row
            (-1, -2): "U",
            (0, -2): "U",
            (1, -2): "U",

            # Numbers just above the yellows
            (-1, -1): 2,
            (0, -1): 1,
            (1, -1): 3,

            # Yellow pair
            (-1, 0): "U",
            (1, 0): "U",

            # Pivot 1
            (0, 0): 1,
        },
        mines=[],
        safes=[(-1, -2), (0, -2), (1, -2)],
    ),

    # --- H3 ---------------------------------------------------------------

    Pattern(
        name="Hole 3",
        short_id="h3",
        code="HH3",
        category="holes",
        cells_count=4,
        description=(
            "Hole pattern H3. Same logical core as H1/H2: a lower 1 and a middle 1 "
            "share a pair of yellow cells that together hold exactly one mine, so "
            "the entire green row above is safe."
        ),
        # Pivot = middle 1 at (0,0).
        constraints={
            # Safe green row
            (-1, -2): "U",
            (0, -2): "U",
            (1, -2): "U",

            # cells just below the safe row (unconstrained numbers / empties)
            (-1, -1): "U",
            (0, -1): "U",
            (1, -1): "U",

            # Yellow pair around pivot
            (-1, 0): "U",
            (1, 0): "U",

            # Pivot and lower 1
            (0, 0): 1,
            (0, 1): 1,
        },
        mines=[],
        safes=[(-1, -2), (0, -2), (1, -2)],
    ),
]


# ========== AGGREGATED LIBRARY ==========

ALL_PATTERNS: List[Pattern] = BASIC_PATTERNS + HOLE_PATTERNS


def get_patterns_by_category(category: str) -> List[Pattern]:
    return [p for p in ALL_PATTERNS if p.category == category]


def get_pattern(short_id: str) -> Optional[Pattern]:
    for p in ALL_PATTERNS:
        if p.short_id == short_id:
            return p
    return None
