import collections
from minesweeper import Minesweeper


def l3_step(game: Minesweeper):
    """
    Analyzes the game state using a Constraint Satisfaction Problem (CSP) approach.
    Finds all valid local mine permutations for boundary cells.
    If a cell is safe in all permutations, it reveals it.
    If a cell is a mine in all permutations, it flags it.

    game: An instance of the Minesweeper class.

    Returns "success" if an action was taken, "fail" if no safe actions found, should go to the next step.
    """

    state = game.current_state
    board = state["board"]
    width = game.width
    height = game.height

    variables = set()
    constraints = []

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

            # We only care about revealed numbers
            if isinstance(cell, int) and cell > 0:
                hidden_neighbors = []
                flag_count = 0

                for nx, ny in get_neighbors(x, y):
                    n_val = board[ny][nx]
                    if n_val == "F":
                        flag_count += 1
                    elif n_val == "_":
                        hidden_neighbors.append((nx, ny))

                # If this number exerts a constraint on hidden cells
                if hidden_neighbors:
                    remaining_mines = cell - flag_count
                    constraints.append(
                        {
                            "pos": (x, y),
                            "needed": remaining_mines,
                            "vars": hidden_neighbors,
                        }
                    )
                    for v in hidden_neighbors:
                        variables.add(v)

    if not constraints:
        return "fail"

    # 2. Segregate Constraints into Connected Components
    # We map variables to the constraints that affect them
    var_to_constraints = collections.defaultdict(list)
    for i, c in enumerate(constraints):
        for v in c["vars"]:
            var_to_constraints[v].append(i)

    # Build adjacency graph for constraints:
    # Two constraints are connected if they share a variable
    constraint_graph = collections.defaultdict(set)
    for v, c_indices in var_to_constraints.items():
        for i in range(len(c_indices)):
            for j in range(i + 1, len(c_indices)):
                idx1, idx2 = c_indices[i], c_indices[j]
                constraint_graph[idx1].add(idx2)
                constraint_graph[idx2].add(idx1)

    # Find connected components of constraints
    visited_constraints = set()

    for i in range(len(constraints)):
        if i in visited_constraints:
            continue

        # BFS to find component
        component_indices = []
        queue = [i]
        visited_constraints.add(i)

        while queue:
            curr = queue.pop(0)
            component_indices.append(curr)
            for neighbor in constraint_graph[curr]:
                if neighbor not in visited_constraints:
                    visited_constraints.add(neighbor)
                    queue.append(neighbor)

        # 3. Solve this Component
        # Gather all unique variables in this component
        comp_vars = set()
        comp_constraints = [constraints[idx] for idx in component_indices]
        for c in comp_constraints:
            for v in c["vars"]:
                comp_vars.add(v)

        comp_vars_list = list(comp_vars)
        var_to_index = {v: k for k, v in enumerate(comp_vars_list)}

        # valid_solutions will be a list of lists (e.g., [[0,1,0], [0,0,1]])
        valid_solutions = []

        # Pre-process constraints for faster checking inside recursion
        # Each constraint maps to specific indices in comp_vars_list
        optimized_constraints = []
        for c in comp_constraints:
            indices = [var_to_index[v] for v in c["vars"]]
            optimized_constraints.append({"indices": indices, "needed": c["needed"]})

        # Recursive Backtracking (DFS)
        # solution_builder: list of 0 (Safe) or 1 (Mine)
        def backtrack(k, current_solution):
            # Optimization: Check validity early
            # We iterate over constraints. If a constraint is fully determined
            # by variables 0..k-1, we check it.
            # Even if not fully determined, we check if we've already exceeded 'needed'

            for c in optimized_constraints:
                current_mines = 0
                unknowns = 0
                for idx in c["indices"]:
                    if idx < k:
                        current_mines += current_solution[idx]
                    else:
                        unknowns += 1

                # Pruning 1: Too many mines
                if current_mines > c["needed"]:
                    return
                # Pruning 2: Not enough space to satisfy mines
                if current_mines + unknowns < c["needed"]:
                    return

            # Base case: All variables assigned
            if k == len(comp_vars_list):
                valid_solutions.append(list(current_solution))
                return

            # Try assuming Safe (0)
            current_solution.append(0)
            backtrack(k + 1, current_solution)
            current_solution.pop()

            # Try assuming Mine (1)
            current_solution.append(1)
            backtrack(k + 1, current_solution)
            current_solution.pop()

        backtrack(0, [])

        # 4. Analyze Solutions for this component
        if not valid_solutions:
            # Should technically not happen if board is consistent
            continue

        num_solutions = len(valid_solutions)
        num_vars = len(comp_vars_list)

        # Sum columns to find unanimous values
        # sums[j] = total number of times variable j was a mine
        sums = [0] * num_vars
        for sol in valid_solutions:
            for idx, val in enumerate(sol):
                sums[idx] += val

        for idx, total_mines in enumerate(sums):
            target_x, target_y = comp_vars_list[idx]

            # CASE 1: Cell is a Mine in ALL solutions
            if total_mines == num_solutions:
                game.flag_cell(target_x, target_y)
                return "success"

            # CASE 2: Cell is Safe (0) in ALL solutions
            if total_mines == 0:
                game.reveal_cell(target_x, target_y)
                return "success"

    # If we went through all components and found no 100% certain moves
    return "fail"
