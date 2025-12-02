"""
Phase 4 Solver for Minesweeper

This module implements a probabilistic solver that uses tree search to calculate
possible mine placements around the edge of the revealed board. It handles cases
where CSP solvers (phases 1-3) cannot make deterministic decisions.

The solver:
1. Identifies edge cells (hidden cells adjacent to revealed numbered cells)
2. Uses tree search to find all valid mine placement configurations
3. Calculates probabilities based on valid configurations
4. Flags cells that are mines in all valid configurations
5. Returns the cell with the lowest probability of being a mine
"""

from typing import List, Tuple, Set, Dict, Optional
from collections import defaultdict


class Phase4Solver:
    """
    Phase 4 probabilistic solver for Minesweeper.
    
    Uses tree search to explore all possible mine placements around the edge
    of revealed cells and calculates probabilities based on valid configurations.
    """
    
    def __init__(self, board: List[List], width: int, height: int, total_mines: int, 
                 flagged_cells: Optional[Set[Tuple[int, int]]] = None):
        """
        Initialize the Phase 4 solver.
        
        Args:
            board: Current game board state (2D list)
            width: Board width
            height: Board height
            total_mines: Total number of mines in the game
            flagged_cells: Set of (x, y) coordinates of already flagged cells
        """
        self.board = board
        self.width = width
        self.height = height
        self.total_mines = total_mines
        self.flagged_cells = flagged_cells if flagged_cells is not None else set()
        
    def is_valid_coordinate(self, x: int, y: int) -> bool:
        """Check if coordinates are within board bounds."""
        return 0 <= x < self.width and 0 <= y < self.height
    
    def get_neighbors(self, x: int, y: int) -> List[Tuple[int, int]]:
        """Get all valid neighboring coordinates."""
        neighbors = []
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                nx, ny = x + dx, y + dy
                if self.is_valid_coordinate(nx, ny):
                    neighbors.append((nx, ny))
        return neighbors
    
    def get_edge_cells(self) -> Set[Tuple[int, int]]:
        """
        Identify edge cells: hidden cells that are adjacent to at least one
        revealed numbered cell.
        
        Returns:
            Set of (x, y) coordinates of edge cells
        """
        edge_cells = set()
        
        for y in range(self.height):
            for x in range(self.width):
                cell = self.board[y][x]
                # Check if this is a revealed numbered cell
                if isinstance(cell, int) and cell > 0:
                    # Check all neighbors
                    for nx, ny in self.get_neighbors(x, y):
                        neighbor = self.board[ny][nx]
                        # If neighbor is hidden (not revealed, not flagged)
                        if neighbor == "_":
                            edge_cells.add((nx, ny))
        
        return edge_cells
    
    def extract_constraints(self) -> List[Dict]:
        """
        Extract constraints from revealed numbered cells.
        
        Each constraint is a dict with:
        - 'cell': (x, y) coordinates of the numbered cell
        - 'value': the number (mine count)
        - 'hidden_neighbors': list of (x, y) hidden neighbor coordinates
        - 'flagged_neighbors': count of flagged neighbors
        
        Returns:
            List of constraint dictionaries
        """
        constraints = []
        
        for y in range(self.height):
            for x in range(self.width):
                cell = self.board[y][x]
                # Check if this is a revealed numbered cell
                if isinstance(cell, int) and cell > 0:
                    hidden_neighbors = []
                    flagged_count = 0
                    
                    for nx, ny in self.get_neighbors(x, y):
                        neighbor = self.board[ny][nx]
                        if neighbor == "_":
                            # Check if it's flagged in flagged_cells (and still hidden)
                            if (nx, ny) in self.flagged_cells:
                                flagged_count += 1
                            else:
                                hidden_neighbors.append((nx, ny))
                        elif neighbor == "F":
                            # Flagged on board (and hidden)
                            flagged_count += 1
                    
                    # Only add constraint if there are hidden neighbors
                    if hidden_neighbors:
                        constraints.append({
                            'cell': (x, y),
                            'value': cell,
                            'hidden_neighbors': hidden_neighbors,
                            'flagged_neighbors': flagged_count
                        })
        
        return constraints
    
    def count_remaining_mines(self) -> int:
        """Count how many mines are still unaccounted for."""
        # Count flags on the board
        board_flags = sum(1 for y in range(self.height) 
                         for x in range(self.width) if self.board[y][x] == "F")
        # Also count flags in the flagged_cells set that might not be on board yet
        # Only count if the cell is still hidden (not revealed)
        additional_flags = sum(1 for x, y in self.flagged_cells 
                              if self.is_valid_coordinate(x, y) and self.board[y][x] == "_")
        total_flagged = board_flags + additional_flags
        return max(0, self.total_mines - total_flagged)
    
    def is_valid_configuration(self, edge_mines: Set[Tuple[int, int]], 
                               constraints: List[Dict]) -> bool:
        """
        Check if a mine configuration satisfies all constraints.
        
        Args:
            edge_mines: Set of (x, y) coordinates where mines are placed
            constraints: List of constraint dictionaries
            
        Returns:
            True if configuration is valid, False otherwise
        """
        for constraint in constraints:
            x, y = constraint['cell']
            required_mines = constraint['value']
            hidden_neighbors = constraint['hidden_neighbors']
            flagged_neighbors = constraint['flagged_neighbors']
            
            # Count mines in hidden neighbors
            mine_count = sum(1 for neighbor in hidden_neighbors if neighbor in edge_mines)
            total_mines = mine_count + flagged_neighbors
            
            if total_mines != required_mines:
                return False
        
        return True
    
    def calculate_min_max_edge_mines(self, constraints: List[Dict], 
                                     num_edge_cells: int) -> Tuple[int, int]:
        """
        Calculate the minimum and maximum number of mines that could be in edge cells
        based on constraints. This helps bound the search space.
        
        Args:
            constraints: List of constraint dictionaries
            num_edge_cells: Number of edge cells
            
        Returns:
            Tuple of (min_mines, max_mines) in edge cells
        """
        # Minimum: at least the maximum requirement from any single constraint
        # Maximum: sum of all required mines (if no overlaps)
        min_mines = 0
        max_mines = 0
        
        for constraint in constraints:
            required = constraint['value'] - constraint['flagged_neighbors']
            if required > 0:
                min_mines = max(min_mines, required)  # At least one constraint's requirement
                max_mines += required  # Upper bound (no overlaps)
        
        return min_mines, min(max_mines, num_edge_cells)
    
    def tree_search_mine_placements(self, edge_cells: Set[Tuple[int, int]], 
                                    constraints: List[Dict],
                                    remaining_mines: int) -> List[Set[Tuple[int, int]]]:
        """
        Use tree search to find all valid mine placement configurations.
        
        We find all valid ways to place mines in edge cells that satisfy constraints.
        The number of mines in edge cells can vary as long as constraints are satisfied.
        
        Args:
            edge_cells: Set of edge cell coordinates
            constraints: List of constraint dictionaries
            remaining_mines: Number of mines remaining to place (used as upper bound)
            
        Returns:
            List of sets, where each set contains mine coordinates for a valid configuration
        """
        edge_list = list(edge_cells)
        valid_configurations = []
        
        # Calculate bounds for number of mines in edge cells
        min_edge_mines, max_edge_mines = self.calculate_min_max_edge_mines(constraints, len(edge_cells))
        max_edge_mines = min(max_edge_mines, remaining_mines, len(edge_cells))
        
        def backtrack(current_mines: Set[Tuple[int, int]], index: int):
            """Recursive backtracking to explore all mine placements."""
            # Check if we've used too many mines
            if len(current_mines) > max_edge_mines:
                return
            
            # Early pruning: check if current partial configuration violates constraints
            if not self.is_partial_configuration_valid(current_mines, constraints):
                return
            
            # If we've processed all edge cells, check if this is a valid complete configuration
            if index >= len(edge_list):
                if len(current_mines) >= min_edge_mines and self.is_valid_configuration(current_mines, constraints):
                    valid_configurations.append(current_mines.copy())
                return
            
            # Try placing mine at current cell
            current_cell = edge_list[index]
            current_mines.add(current_cell)
            backtrack(current_mines, index + 1)
            current_mines.remove(current_cell)
            
            # Try not placing mine at current cell
            backtrack(current_mines, index + 1)
        
        backtrack(set(), 0)
        return valid_configurations
    
    def is_partial_configuration_valid(self, partial_mines: Set[Tuple[int, int]], 
                                      constraints: List[Dict]) -> bool:
        """
        Check if a partial mine configuration doesn't violate any constraints.
        This is used for early pruning in the tree search.
        
        Args:
            partial_mines: Set of mine coordinates placed so far
            constraints: List of constraint dictionaries
            
        Returns:
            True if partial configuration is still valid, False otherwise
        """
        for constraint in constraints:
            x, y = constraint['cell']
            required_mines = constraint['value']
            hidden_neighbors = constraint['hidden_neighbors']
            flagged_neighbors = constraint['flagged_neighbors']
            
            # Count mines in hidden neighbors
            mine_count = sum(1 for neighbor in hidden_neighbors if neighbor in partial_mines)
            total_mines = mine_count + flagged_neighbors
            
            # If we've exceeded the required mines, this is invalid
            if total_mines > required_mines:
                return False
        
        return True
    
    def calculate_probabilities_tree_search(self, edge_cells: Set[Tuple[int, int]], 
                                           constraints: List[Dict],
                                           remaining_mines: int) -> Dict[Tuple[int, int], float]:
        """
        Calculate probabilities of edge cells being mines using tree search.
        
        This is the default/modular probability calculation function.
        
        Args:
            edge_cells: Set of edge cell coordinates
            constraints: List of constraint dictionaries
            remaining_mines: Number of mines remaining to place
            
        Returns:
            Dictionary mapping (x, y) coordinates to probability (0.0 to 1.0)
        """
        if not edge_cells:
            return {}
        
        # Find all valid configurations
        valid_configurations = self.tree_search_mine_placements(
            edge_cells, constraints, remaining_mines
        )
        
        if not valid_configurations:
            # If no valid configurations found, assign equal probability
            # This shouldn't happen in practice, but handle edge case
            prob = min(1.0, remaining_mines / len(edge_cells)) if edge_cells else 0.0
            return {cell: prob for cell in edge_cells}
        
        # Count how many configurations have a mine at each cell
        mine_counts = defaultdict(int)
        for config in valid_configurations:
            for cell in config:
                mine_counts[cell] += 1
        
        # Calculate probabilities
        total_configs = len(valid_configurations)
        probabilities = {}
        for cell in edge_cells:
            probabilities[cell] = mine_counts[cell] / total_configs
        
        return probabilities
    
    def find_connected_components(self, cells: Set[Tuple[int, int]]) -> List[Set[Tuple[int, int]]]:
        """
        Find connected components of cells (cells that are adjacent to each other).
        
        Args:
            cells: Set of cell coordinates
            
        Returns:
            List of sets, where each set is a connected component
        """
        if not cells:
            return []
        
        components = []
        visited = set()
        
        for start_cell in cells:
            if start_cell in visited:
                continue
            
            # BFS to find all connected cells
            component = set()
            queue = [start_cell]
            visited.add(start_cell)
            
            while queue:
                cell = queue.pop(0)
                component.add(cell)
                x, y = cell
                
                # Check all neighbors
                for nx, ny in self.get_neighbors(x, y):
                    neighbor = (nx, ny)
                    if neighbor in cells and neighbor not in visited:
                        visited.add(neighbor)
                        queue.append(neighbor)
            
            if component:
                components.append(component)
        
        return components
    
    def is_component_isolated(self, component: Set[Tuple[int, int]], 
                             constraints: List[Dict]) -> bool:
        """
        Check if a component of edge cells is isolated from other constraints.
        
        A component is isolated if:
        1. All constraints affecting cells in this component only affect cells in this component
        2. No future reveals outside this component can provide information about it
        
        Args:
            component: Set of cell coordinates in the component
            constraints: List of constraint dictionaries
            
        Returns:
            True if the component is isolated and won't get more information
        """
        # Find all constraints that affect this component
        component_constraints = []
        for constraint in constraints:
            constraint_cells = set(constraint['hidden_neighbors'])
            # If this constraint has any overlap with the component
            if constraint_cells & component:
                component_constraints.append(constraint)
        
        if not component_constraints:
            # No constraints affect this component - it's isolated
            return True
        
        # Check if all cells affected by these constraints are within the component
        all_constraint_cells = set()
        for constraint in component_constraints:
            all_constraint_cells.update(constraint['hidden_neighbors'])
        
        # If all constraint cells are in the component, it's isolated
        if all_constraint_cells.issubset(component):
            return True
        
        return False
    
    def _find_isolated_equal_prob_component(self, 
                                           probabilities: Dict[Tuple[int, int], float], 
                                           edge_cells: Set[Tuple[int, int]],
                                           constraints: List[Dict]) -> Tuple[bool, Optional[Set[Tuple[int, int]]]]:
        """
        Find isolated equal-probability components (helper for detect_equal_probability_case).
        
        Returns:
            Tuple of (found_equal_prob_case, isolated_component)
            - If global case: (True, None)
            - If sub-board case: (True, component_set)
            - If no case: (False, None)
        """
        if not probabilities:
            return False, None
        
        # Check global case: all edge cells have equal probability
        prob_values = list(probabilities.values())
        if len(prob_values) == 0:
            return False, None
        
        first_prob = prob_values[0]
        all_equal_global = all(abs(p - first_prob) < 1e-9 for p in prob_values)
        
        if all_equal_global:
            # Count total hidden cells (not just edge)
            total_hidden = sum(1 for y in range(self.height) 
                              for x in range(self.width) 
                              if self.board[y][x] == "_")
            
            if total_hidden == len(edge_cells):
                # All hidden cells are edge cells with equal probability
                return True, None
            
            # If no constraints, it's a global equal probability case
            if len(constraints) == 0:
                return True, None
        
        # Check sub-board cases: find connected components and check each
        components = self.find_connected_components(edge_cells)
        
        for component in components:
            if len(component) < 2:
                continue  # Skip single-cell components
            
            # Get probabilities for this component
            component_probs = {cell: probabilities[cell] 
                              for cell in component if cell in probabilities}
            
            if not component_probs:
                continue
            
            # Check if all cells in this component have equal probability
            comp_prob_values = list(component_probs.values())
            if len(comp_prob_values) == 0:
                continue
            
            first_comp_prob = comp_prob_values[0]
            all_equal_component = all(abs(p - first_comp_prob) < 1e-9 
                                     for p in comp_prob_values)
            
            if all_equal_component:
                # Check if this component is isolated (won't get more info)
                if self.is_component_isolated(component, constraints):
                    # This is an inevitable equal-probability sub-board case
                    return True, component
        
        return False, None
    
    def detect_equal_probability_case(self, probabilities: Dict[Tuple[int, int], float], 
                                      edge_cells: Set[Tuple[int, int]],
                                      constraints: List[Dict]) -> bool:
        """
        Detect if there are equal probability cases (global or sub-board) that won't change.
        
        This checks both:
        1. Global case: All edge cells have equal probability globally
        2. Sub-board case: Isolated connected components of edge cells with equal probability
           that are independent and won't get more information from future reveals
        
        Args:
            probabilities: Dictionary of cell probabilities
            edge_cells: Set of edge cell coordinates
            constraints: List of constraint dictionaries
            
        Returns:
            True if there's an equal probability case that can't be resolved later
        """
        if not probabilities:
            return False
        
        # Check global case: all edge cells have equal probability
        prob_values = list(probabilities.values())
        if len(prob_values) == 0:
            return False
        
        first_prob = prob_values[0]
        all_equal_global = all(abs(p - first_prob) < 1e-9 for p in prob_values)
        
        if all_equal_global:
            # Count total hidden cells (not just edge)
            total_hidden = sum(1 for y in range(self.height) 
                              for x in range(self.width) 
                              if self.board[y][x] == "_")
            
            if total_hidden == len(edge_cells):
                # All hidden cells are edge cells with equal probability
                return True
            
            # If no constraints, it's a global equal probability case
            if len(constraints) == 0:
                return True
        
        # Check sub-board cases: find connected components and check each
        components = self.find_connected_components(edge_cells)
        
        for component in components:
            if len(component) < 2:
                continue  # Skip single-cell components
            
            # Get probabilities for this component
            component_probs = {cell: probabilities[cell] 
                              for cell in component if cell in probabilities}
            
            if not component_probs:
                continue
            
            # Check if all cells in this component have equal probability
            comp_prob_values = list(component_probs.values())
            if len(comp_prob_values) == 0:
                continue
            
            first_comp_prob = comp_prob_values[0]
            all_equal_component = all(abs(p - first_comp_prob) < 1e-9 
                                     for p in comp_prob_values)
            
            if all_equal_component:
                # Check if this component is isolated (won't get more info)
                if self.is_component_isolated(component, constraints):
                    # This is an inevitable equal-probability sub-board case
                    return True
        
        return False
    
    def calculate_information_gain(self, cell: Tuple[int, int], 
                                   edge_cells: Set[Tuple[int, int]],
                                   constraints: List[Dict]) -> float:
        """
        Calculate information gain heuristic for revealing a cell.
        
        Estimates how much revealing this cell would help phases 1-3 by:
        1. Counting how many new constraints it would create (if it reveals a number)
        2. Estimating how many cells might become deterministically solvable
        3. Considering how many hidden neighbors it has (more neighbors = more info)
        
        Args:
            cell: (x, y) coordinates of the cell to evaluate
            edge_cells: Set of all edge cell coordinates
            constraints: Current list of constraints
            
        Returns:
            Information gain score (higher is better)
        """
        x, y = cell
        if not self.is_valid_coordinate(x, y):
            return 0.0
        
        # Count hidden neighbors (these would become edge cells if we reveal this)
        hidden_neighbors = []
        revealed_neighbors = []
        for nx, ny in self.get_neighbors(x, y):
            if self.is_valid_coordinate(nx, ny):
                neighbor = self.board[ny][nx]
                if neighbor == "_":
                    hidden_neighbors.append((nx, ny))
                elif isinstance(neighbor, int):
                    revealed_neighbors.append((nx, ny))
        
        # Information gain factors:
        # 1. Number of hidden neighbors (more = more potential new constraints)
        info_gain = len(hidden_neighbors) * 2.0
        
        # 2. If this cell is adjacent to many revealed cells, revealing it might
        #    create new constraints that connect with existing ones
        info_gain += len(revealed_neighbors) * 1.5
        
        # 3. Prefer cells that are adjacent to multiple constraints
        #    (revealing them might help resolve multiple constraints at once)
        adjacent_constraints = 0
        for constraint in constraints:
            cx, cy = constraint['cell']
            if abs(cx - x) <= 1 and abs(cy - y) <= 1:
                adjacent_constraints += 1
        
        info_gain += adjacent_constraints * 1.0
        
        # 4. Prefer cells that are in the "middle" of edge cells
        #    (they're more likely to create interconnected constraints)
        if cell in edge_cells:
            # Count how many other edge cells are neighbors
            edge_neighbors = sum(1 for nx, ny in self.get_neighbors(x, y) 
                               if (nx, ny) in edge_cells)
            info_gain += edge_neighbors * 0.5
        
        return info_gain
    
    def select_cell_with_heuristic(self, probabilities: Dict[Tuple[int, int], float],
                                   edge_cells: Set[Tuple[int, int]],
                                   constraints: List[Dict],
                                   use_information_gain: bool = False) -> Tuple[int, int]:
        """
        Select a cell to reveal using either probability-only or information gain heuristic.
        
        Args:
            probabilities: Dictionary of cell probabilities
            edge_cells: Set of edge cell coordinates
            constraints: List of constraint dictionaries
            use_information_gain: If True, use information gain heuristic; if False, use probability only
        
        Returns:
            (x, y) coordinates of selected cell
        """
        if not probabilities:
            raise ValueError("No probabilities provided")
        
        if use_information_gain:
            # Combine probability and information gain
            # Lower probability is better (safer), higher info gain is better
            # Score = -probability + info_gain_weight * information_gain
            info_gain_weight = 0.1  # Tune this to balance safety vs. information
            
            scored_cells = []
            for cell, prob in probabilities.items():
                info_gain = self.calculate_information_gain(cell, edge_cells, constraints)
                # Lower probability is better, so we negate it
                # Higher info gain is better, so we add it
                score = -prob + info_gain_weight * info_gain
                scored_cells.append((score, cell, prob, info_gain))
            
            # Sort by score (higher is better)
            scored_cells.sort(reverse=True, key=lambda x: x[0])
            
            # Return the cell with best score
            return scored_cells[0][1]
        else:
            # Original behavior: just pick lowest probability
            min_prob_cell = min(probabilities.items(), key=lambda x: x[1])
            return min_prob_cell[0]
    
    def get_unexplored_cells(self) -> Set[Tuple[int, int]]:
        """
        Get all unexplored (hidden) cells on the board that are not on the edge.
        
        Returns:
            Set of (x, y) coordinates of unexplored cells
        """
        unexplored = set()
        edge_cells = self.get_edge_cells()
        
        for y in range(self.height):
            for x in range(self.width):
                if self.board[y][x] == "_":
                    cell = (x, y)
                    # Only include if not on edge
                    if cell not in edge_cells:
                        unexplored.add(cell)
        
        return unexplored
    
    def calculate_global_probability(self, remaining_mines: int, 
                                    total_unexplored: int) -> float:
        """
        Calculate global probability of a mine in unexplored cells.
        
        Args:
            remaining_mines: Number of mines remaining
            total_unexplored: Total number of unexplored cells
            
        Returns:
            Global probability (0.0 to 1.0)
        """
        if total_unexplored == 0:
            return 0.0
        return min(1.0, remaining_mines / total_unexplored)
    
    def find_safe_unexplored_cell(self, remaining_mines: int,
                                  safe_threshold: float = 0.35) -> Optional[Tuple[int, int]]:
        """
        Find an unexplored cell to reveal when edge cells are too risky.
        
        Strategy:
        1. Calculate global probability for unexplored cells
        2. If global probability is below threshold, prefer cells far from revealed areas
        3. Otherwise, pick randomly from unexplored cells
        
        Args:
            remaining_mines: Number of mines remaining
            safe_threshold: Maximum acceptable mine probability (default 0.35 = 65% confidence safe)
        
        Returns:
            (x, y) coordinates of a cell to reveal, or None if no unexplored cells
        """
        unexplored = self.get_unexplored_cells()
        
        if not unexplored:
            return None
        
        total_unexplored = len(unexplored) + len(self.get_edge_cells())
        global_prob = self.calculate_global_probability(remaining_mines, total_unexplored)
        
        # If global probability is acceptable, prefer cells far from revealed areas
        # (they're more likely to open up new regions)
        if global_prob < safe_threshold:
            # Find cells that are farthest from any revealed cell
            cell_distances = []
            for cell in unexplored:
                x, y = cell
                min_distance = float('inf')
                
                # Find minimum distance to any revealed cell
                for ry in range(self.height):
                    for rx in range(self.width):
                        if isinstance(self.board[ry][rx], int):
                            dist = max(abs(rx - x), abs(ry - y))
                            min_distance = min(min_distance, dist)
                
                if min_distance != float('inf'):
                    cell_distances.append((min_distance, cell))
            
            if cell_distances:
                # Sort by distance (farthest first) and pick one
                cell_distances.sort(reverse=True, key=lambda x: x[0])
                return cell_distances[0][1]
        
        # Otherwise, just pick a random unexplored cell
        # (or the first one if we need determinism)
        return list(unexplored)[0]
    
    def solve(self, probability_calculator=None, use_information_gain: bool = False,
              safe_threshold: float = 0.35) -> Tuple[Optional[str], Optional[Tuple[int, int]]]:
        """
        Main solver function.
        
        Args:
            probability_calculator: Optional function to calculate probabilities.
                                  If None, uses default tree search method.
                                  Signature: (edge_cells, constraints, remaining_mines) -> Dict[Tuple[int, int], float]
            use_information_gain: If True, uses information gain heuristic to select cells
                                 that maximize help for phases 1-3 downstream
            safe_threshold: Maximum acceptable mine probability for edge cells (default 0.35).
                           If all edge cells exceed this, explore unexplored areas instead.
        
        Returns:
            Tuple of (action, coordinates):
            - ("FLAG", (x, y)) if a cell should be flagged (mine in all configurations)
            - ("REVEAL", (x, y)) if a cell should be revealed (lowest mine probability or best info gain)
            - (None, None) if no action can be determined
        """
        # Step 1: Get edge cells
        edge_cells = self.get_edge_cells()
        
        # Step 2: Extract constraints
        constraints = self.extract_constraints()
        
        # Step 3: Count remaining mines
        remaining_mines = self.count_remaining_mines()
        
        if remaining_mines < 0:
            # More flags than mines - something is wrong
            return None, None
        
        # If no edge cells, try exploring unexplored areas
        if not edge_cells:
            unexplored_cell = self.find_safe_unexplored_cell(remaining_mines, safe_threshold)
            if unexplored_cell:
                return "REVEAL", unexplored_cell
            return None, None
        
        # If no constraints, try exploring unexplored areas
        if not constraints:
            unexplored_cell = self.find_safe_unexplored_cell(remaining_mines, safe_threshold)
            if unexplored_cell:
                return "REVEAL", unexplored_cell
            return None, None
        
        # Step 4: Use probability calculator (default or provided)
        if probability_calculator is None:
            probabilities = self.calculate_probabilities_tree_search(
                edge_cells, constraints, remaining_mines
            )
        else:
            probabilities = probability_calculator(edge_cells, constraints, remaining_mines)
        
        if not probabilities:
            # No probabilities calculated - try exploring unexplored areas
            unexplored_cell = self.find_safe_unexplored_cell(remaining_mines, safe_threshold)
            if unexplored_cell:
                return "REVEAL", unexplored_cell
            return None, None
        
        # Step 5: Check for cells that are mines in all configurations (probability = 1.0)
        for cell, prob in probabilities.items():
            if prob == 1.0:
                return "FLAG", cell
        
        # Step 6: Check if all edge cells exceed safe threshold
        min_edge_prob = min(probabilities.values()) if probabilities else 1.0
        if min_edge_prob > safe_threshold:
            # All edge cells are too risky - explore unexplored areas instead
            unexplored_cell = self.find_safe_unexplored_cell(remaining_mines, safe_threshold)
            if unexplored_cell:
                return "REVEAL", unexplored_cell
            # If no unexplored cells, fall through to selecting best edge cell anyway
        
        # Step 7: Check for equal probability case (global or sub-board)
        equal_prob_detected, isolated_component = self._find_isolated_equal_prob_component(
            probabilities, edge_cells, constraints
        )
        
        if equal_prob_detected:
            # If we found an isolated component, prioritize cells from that component
            if isolated_component:
                # Pick from the isolated component (prefer info gain if enabled)
                component_probs = {cell: probabilities[cell] 
                                 for cell in isolated_component if cell in probabilities}
                if use_information_gain:
                    selected_cell = self.select_cell_with_heuristic(
                        component_probs, edge_cells, constraints, 
                        use_information_gain=True
                    )
                else:
                    # Just pick the first one from the component
                    selected_cell = list(component_probs.keys())[0]
            else:
                # Global equal probability case - pick any
                if use_information_gain:
                    selected_cell = self.select_cell_with_heuristic(
                        probabilities, edge_cells, constraints, 
                        use_information_gain=True
                    )
                else:
                    selected_cell = list(probabilities.keys())[0]
            return "REVEAL", selected_cell
        
        # Step 8: Select cell using probability or information gain heuristic
        selected_cell = self.select_cell_with_heuristic(
            probabilities, edge_cells, constraints, use_information_gain=use_information_gain
        )
        return "REVEAL", selected_cell


def solve_phase_4(board: List[List], width: int, height: int, total_mines: int,
                  flagged_cells: Optional[Set[Tuple[int, int]]] = None,
                  probability_calculator=None,
                  use_information_gain: bool = False,
                  safe_threshold: float = 0.35) -> Tuple[Optional[str], Optional[Tuple[int, int]]]:
    """
    Convenience function to solve using Phase 4 solver.
    
    Args:
        board: Current game board state (2D list)
        width: Board width
        height: Board height
        total_mines: Total number of mines in the game
        flagged_cells: Set of (x, y) coordinates of already flagged cells
        probability_calculator: Optional function to calculate probabilities
        use_information_gain: If True, uses information gain heuristic to select cells
                             that maximize help for phases 1-3 downstream
        safe_threshold: Maximum acceptable mine probability for edge cells (default 0.35).
                       If all edge cells exceed this, explore unexplored areas instead.
        
    Returns:
        Tuple of (action, coordinates):
        - ("FLAG", (x, y)) if a cell should be flagged
        - ("REVEAL", (x, y)) if a cell should be revealed
        - (None, None) if no action can be determined
    """
    solver = Phase4Solver(board, width, height, total_mines, flagged_cells)
    return solver.solve(probability_calculator=probability_calculator, 
                       use_information_gain=use_information_gain,
                       safe_threshold=safe_threshold)

