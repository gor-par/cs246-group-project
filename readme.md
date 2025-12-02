# CS246 Artificial Intelligence - Minesweeper AI Solution

## 1. About the Project

_To be filled in later_

---

## 2. Repository Outline

This repository contains a multi-layered Minesweeper solver that combines deterministic and probabilistic reasoning to solve Minesweeper games automatically.

### Project Structure

```
cs246-group-project/
├── minesweeper.py              # Core Minesweeper game implementation
├── hybrid_solver.py            # Main hybrid solver orchestrator
├── minesweeper_cli.py          # Command-line interface for the game
│
├── solver_layers/              # Individual solver layer implementations
│   ├── __init__.py
│   ├── layer_1.py             # Basic CSP rules solver
│   ├── layer_2.py             # Pattern-based solver
│   ├── layer_3.py             # Advanced CSP solver
│   └── layer_4.py             # Probabilistic solver
│
├── helpers/                    # Supporting modules
│   ├── __init__.py
│   └── patterns.py            # Pattern definitions for Layer 2
│
├── branch_merges_archive/      # Archived previous implementations
│
└── tests/                      # Test files and test cases
```

### Key Components

- **Core Game**: `minesweeper.py` implements the Minesweeper game logic with board generation, cell revelation, and game state management.

- **Solver Layers**: Four independent solving strategies (layers 1-4) that can be used individually or in combination.

- **Hybrid Solver**: `hybrid_solver.py` orchestrates all layers sequentially, cycling through them and tracking which layer makes each decision.

- **Pattern Library**: `helpers/patterns.py` contains geometric pattern templates used by Layer 2 for pattern-based deductions.

---

## 3. Layer-by-Layer Explanation

The solver uses a hierarchical approach with four distinct layers, each progressively more sophisticated and computationally intensive. Each layer only acts when it has 100% certainty or, in the case of Layer 4, makes the best probabilistic guess when deterministic methods fail.

### Layer 1: Basic Constraint Satisfaction Problem (CSP) Rules

**Purpose**: Applies fundamental Minesweeper deduction rules that work on individual numbered cells and their immediate neighbors.

**Decision Logic**:
- **Rule A (Flagging)**: For each revealed number cell, if `(number - flagged_neighbors) == hidden_neighbors`, then all hidden neighbors must be mines and are flagged.
- **Rule B (Revealing)**: For each revealed number cell, if `number == flagged_neighbors` and there are hidden neighbors, then all hidden neighbors must be safe and are revealed.

**Characteristics**:
- Fast and efficient (O(n) where n is board size)
- Only considers local, single-cell constraints
- 100% deterministic - never makes guesses
- Returns "success" if any action was taken, "fail" if no moves can be made

**When it succeeds**: Most common scenarios in Minesweeper, especially after initial reveals create obvious mine/safe patterns.

---

### Layer 2: Pattern-Based Reasoning

**Purpose**: Recognizes geometric patterns of revealed numbers and hidden cells to make deductions that Layer 1 cannot see.

**Decision Logic**:
- Scans the board for pre-defined geometric patterns (defined in `helpers/patterns.py`)
- Each pattern encodes a known configuration that guarantees certain cells are mines or safe
- Patterns can be rotated (0°, 90°, 180°, 270°) and matched at any board position
- When a pattern matches, it flags guaranteed mines and reveals guaranteed safe cells

**Characteristics**:
- Moderate computational cost (checks all patterns at all positions with all rotations)
- Handles multi-cell constraint relationships
- 100% deterministic - patterns encode proven logical relationships
- More powerful than Layer 1 but still only acts with certainty

**Example patterns**: Corner patterns, edge patterns, sandwich patterns, and other geometric configurations where number relationships guarantee mine/safe positions.

---

### Layer 3: Advanced CSP with Connected Components

**Purpose**: Solves constraint satisfaction problems by finding all valid mine placements within connected components of constraints.

**Decision Logic**:
1. **Constraint Extraction**: Identifies all numbered cells and their constraints (how many mines needed among hidden neighbors)
2. **Component Segmentation**: Groups constraints into connected components (constraints that share variables/cells)
3. **Solution Enumeration**: For each component, uses backtracking to find all valid mine placement configurations
4. **Unanimous Deduction**: If a cell is a mine (or safe) in ALL valid solutions, it flags (or reveals) that cell

**Characteristics**:
- More computationally intensive than Layers 1-2
- Solves complex interconnected constraint networks
- Handles cases where multiple constraints interact
- 100% deterministic - only acts when unanimous across all valid solutions
- Can handle larger constraint groups than Layer 1's single-cell approach

**When it succeeds**: Complex scenarios where multiple numbered cells interact, requiring simultaneous consideration of multiple constraints.

---

### Layer 4: Probabilistic Tree Search

**Purpose**: Makes educated guesses when all deterministic methods fail, using probability calculations based on valid mine configurations.

**Decision Logic**:
1. **Edge Cell Identification**: Finds hidden cells adjacent to revealed numbered cells
2. **Constraint Extraction**: Gathers all constraints from revealed numbers
3. **Tree Search**: Uses backtracking to enumerate all valid mine placement configurations around edge cells
4. **Probability Calculation**: For each edge cell, calculates probability of being a mine based on how many valid configurations place a mine there
5. **Cell Selection Strategies**:
   - Prioritizes isolated equal-probability cases (inevitable 50/50 guesses)
   - Selects cells with lowest mine probability
   - Optionally uses information gain heuristic to choose cells that maximize future deterministic solving opportunities
   - Falls back to exploring unexplored areas if edge cells are too risky

**Characteristics**:
- Most computationally intensive layer
- Makes probabilistic guesses (not 100% certain)
- Can be configured with safety thresholds (default: 35% max probability)
- Supports information gain heuristic to optimize for future deterministic solving
- Returns "success" when it makes a guess, "fail" only if no valid moves exist

**When it succeeds**: When deterministic layers fail and guessing is necessary to proceed. Often used in late-game scenarios or when the board has ambiguous regions.

---

## 4. Hybrid Solver Implementation

The `hybrid_solver.py` module orchestrates all four layers into a unified solving strategy.

### Solving Strategy

The hybrid solver implements a **sequential cycling approach**:

1. **Always starts with Layer 1** - tries the fastest, simplest rules first
2. **Progressive escalation** - if Layer 1 fails, tries Layer 2, then Layer 3, then Layer 4
3. **Restart on success** - whenever any layer makes progress, the solver restarts from Layer 1
4. **Termination** - stops when the game is won, lost, or all layers fail to make progress

### Key Features

- **Action Tracking**: Every action (reveal or flag) is recorded with which layer recommended it
- **Sequential Execution**: Layers are tried in order, ensuring deterministic methods are always preferred over probabilistic guesses
- **Iteration Limits**: Configurable maximum iterations to prevent infinite loops
- **Layer 4 Configuration**: Supports tuning Layer 4's information gain and safety threshold parameters

### Usage Example

```python
from minesweeper import Minesweeper
from hybrid_solver import solve_minesweeper, print_action_history

# Initialize game
game = Minesweeper()
game.start_new_game(width=16, height=16, mines=40, seed=12345)

# Make initial click
game.reveal_cell(8, 8)

# Solve with hybrid solver
result = solve_minesweeper(
    game,
    max_iterations=10000,
    l4_use_information_gain=False,
    l4_safe_threshold=0.35
)

# Print results
print_action_history(result, detailed=True)
```

### Return Structure

The `solve_minesweeper()` function returns a dictionary containing:

- `actions`: List of `ActionRecord` objects (in chronological order)
- `solved`: Boolean indicating if the game was won
- `final_status`: Final game status ("Won", "Lost", or "Playing")
- `iterations`: Total number of actions taken
- `action_summary`: Dictionary summarizing actions by layer (reveals, flags, totals)

### ActionRecord Class

Each action is represented by an `ActionRecord` object:

```python
ActionRecord(
    action_type="REVEAL" or "FLAG",
    x=<x_coordinate>,
    y=<y_coordinate>,
    layer=<1-4>
)
```

This structure allows complete traceability of which solver layer made each decision throughout the game.

---

## 5. Logging and Results Structure

The hybrid solver provides comprehensive logging capabilities to track solver behavior and analyze performance.

### Action History

Every action taken during solving is recorded as an `ActionRecord` object, stored in chronological order in the `actions` list. Each record contains:

- **Action Type**: Whether the cell was revealed or flagged
- **Coordinates**: The (x, y) position of the action
- **Layer Attribution**: Which solver layer (1-4) recommended this action

### Action Summary

The solver automatically generates summary statistics organized by layer:

```python
action_summary = {
    1: {"REVEAL": 45, "FLAG": 12, "total": 57},
    2: {"REVEAL": 8, "FLAG": 3, "total": 11},
    3: {"REVEAL": 2, "FLAG": 1, "total": 3},
    4: {"REVEAL": 5, "FLAG": 0, "total": 5}
}
```

This allows quick analysis of:
- Which layers contributed most to solving the game
- The balance between reveals and flags per layer
- How often probabilistic guessing (Layer 4) was needed

### Print Functions

The `print_action_history()` function provides formatted output:

**Summary Mode** (default):
- Final game status
- Total actions taken
- Breakdown by layer (reveals, flags, totals)

**Detailed Mode** (`detailed=True`):
- All of the above, plus:
- Complete sequential list of every action with layer attribution
- Numbered action sequence for easy reference

### Example Output

```
============================================================
HYBRID SOLVER RESULTS
============================================================
Final Status: Won
Total Actions: 76

Action Summary by Layer:
  Layer 1: 45 reveals, 12 flags, 57 total
  Layer 2: 8 reveals, 3 flags, 11 total
  Layer 3: 2 reveals, 1 flags, 3 total
  Layer 4: 5 reveals, 0 flags, 5 total

Detailed Action Sequence:
============================================================
    1. Layer 1: REVEAL (7, 8)
    2. Layer 1: REVEAL (8, 7)
    3. Layer 1: FLAG (9, 8)
    ...
============================================================
```

### Integration with Game State

The logging system captures board state changes by:
1. Taking snapshots before and after each layer execution
2. Comparing snapshots to identify what changed
3. Attributing all changes in a single layer execution cycle to that layer
4. Recording recursive reveals (from 0-tile cascades) as part of the initial action

This ensures complete traceability while maintaining clarity about which layer initiated each sequence of actions.

---

## Future Enhancements

Potential improvements for the solver system:

- Enhanced pattern library expansion
- Performance optimization for Layer 3 and Layer 4
- Machine learning integration for pattern recognition
- Statistical analysis tools for solver performance evaluation
- Visualization tools for action sequence playback
