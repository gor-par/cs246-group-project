import random
import time


class Minesweeper:
    def __init__(self):
        pass

    def start_new_game(self, width: int, height: int, mines: int, seed: int):
        self.width = width
        self.height = height
        self.mines = mines

        board = Board(width, height, mines, seed)
        self.board = board
        self.current_board = board.empty_board

        self.reveals_count = 0
        self.unrevealed_cells_count = width * height - mines

        self.start_time = None
        self.stop_time = None
        self.game_over = False

    @property
    def current_state(self):
        elapsed_time = 0
        if self.game_over:
            elapsed_time = self.stop_time - self.start_time
        elif self.start_time is not None:
            elapsed_time = time.perf_counter() - self.start_time

        status = "Playing"
        if self.game_over:
            status = "Won" if self.won else "Lost"

        return {"time": elapsed_time, "board": self.current_board, "status": status}

    def reveal_cell(self, x: int, y: int):
        # print(x, y)
        if not self.board.is_valid_cell_coordinate(x, y):
            raise ValueError("Coordinate value out of board range")

        if (
            self.current_board[y][x] != "_" and self.current_board[y][x] != "F"
        ):  # if already revealed, no need to do anything more, but flags act as empties since you should've known better before clicking
            return "REPEAT"

        if self.reveals_count == 0:
            self.start_time = time.perf_counter()
            self.full_board = self.board.get_full_board(
                x, y
            )  # generating the board after first click

        value = self.full_board[y][x]
        self.current_board[y][x] = value

        if value == "M":
            self.won = False
            self._stop_game()
            return "DEFEAT"

        self.reveals_count += 1

        if self.reveals_count == self.unrevealed_cells_count:
            self.won = True
            self._stop_game()
            return "VICTORY"

        if value == 0:  # update adjacent cells recursively
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    if dx == 0 and dy == 0:
                        continue
                    try:
                        self.reveal_cell(x + dx, y + dy)
                    except ValueError:
                        pass

        return "SUCCESS"

    def flag_cell(self, x, y):
        print(x, y)
        if not self.board.is_valid_cell_coordinate(x, y):
            raise ValueError("Coordinate value out of board range")

        if (
            self.current_board[y][x] != "_"
        ):  # if already revealed, no need to do anything more
            return "NO FLAG"

        self.current_board[y][x] = "F"
        return "FLAG"

    def _stop_game(self):
        self.game_over = True
        self.stop_time = time.perf_counter()


class Board:

    def __init__(self, width, height, mines, seed):
        random.seed(seed)

        self.width = width
        self.height = height
        self.mines = mines

    def generate_mine_coordinates(self, init_x, init_y):
        cell_positions_list = list(range(self.width * self.height))
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                x = init_x + dx
                y = init_y + dy
                if self.is_valid_cell_coordinate(x, y):
                    safe_cell_position = self.coord_to_position(x, y)
                    cell_positions_list.remove(safe_cell_position)

        mine_positions = random.sample(cell_positions_list, self.mines)
        mine_coords = [(pos // self.width, pos % self.width) for pos in mine_positions]
        return mine_coords

    def populate_board(self):
        board = []

        for i in range(self.height):
            row = [self.calculate_cell_value(i, j) for j in range(self.width)]
            board.append(row)
        return board

    def calculate_cell_value(self, i, j):
        adjacent_mines = 0
        for x, y in self.mine_coords:
            if i == x and j == y:
                return "M"
            if abs(x - i) <= 1 and abs(y - j) <= 1:
                adjacent_mines += 1
        return adjacent_mines

    @property
    def empty_board(self):
        board = []
        for i in range(self.height):
            row = ["_" for j in range(self.width)]
            board.append(row)
        return board

    def get_full_board(self, x, y):
        self.mine_coords = self.generate_mine_coordinates(x, y)
        self.matrix = self.populate_board()
        return self.matrix

    def coord_to_position(self, x, y):
        return y * self.width + x

    def is_valid_cell_coordinate(self, x, y):
        return x >= 0 and x < self.width and y >= 0 and y < self.height


# Example programmatic game

# m = Minesweeper()
# m.start_new_game(10, 10, 9, 1)
# print(m.current_state)
# print(m.reveal_cell(2, 2))

# print(m.current_state["board"])
# print(m.reveal_cell(7, 6))
# print(m.reveal_cell(8, 6))

# print(m.current_state["board"])
# print(m.reveal_cell(9, 1))
# print(m.flag_cell(8, 1))
# print(m.reveal_cell(9, 0))
# print(m.flag_cell(8, 0))

# print(m.current_state["board"])
# print(m.reveal_cell(0, 3))
# print(m.flag_cell(0, 2))
# print(m.flag_cell(1, 4))
# print(m.reveal_cell(0, 4))
# print(m.current_state["board"])
# print(m.reveal_cell(0, 5))
# print(m.reveal_cell(1, 5))
# print(m.current_state["board"])
# print(m.reveal_cell(0, 6))
# print(m.reveal_cell(1, 6))
# print(m.flag_cell(6, 6))
# print(m.flag_cell(9, 6))
# print(m.flag_cell(2, 7))
# print(m.reveal_cell(2, 8))
# print(m.flag_cell(2, 9))
# print(m.flag_cell(1, 8))
# print(m.reveal_cell(0, 9))
# print(m.reveal_cell(0, 8))
# print(m.reveal_cell(1, 9))

# print(m.current_state["board"])


# """
# 0, 0, 0, 0, 0, 0, 0, 2, F, 2
# 1, 1, 0, 0, 0, 0, 0, 2, F, 2
# F, 1, 0, 0, 0, 0, 0, 1, 1, 1
# 2, 2, 1, 0, 0, 0, 0, 0, 0, 0
# 1, F, 1, 0, 0, 0, 0, 0, 0, 0
# 1, 1, 1, 0, 0, 1, 1, 1, 1, 1
# 0, 1, 1, 1, 0, 1, F, 1, 1, F
# 1, 2, F, 1, 0, 1, 1, 1, 1, 1
# 1, F, 3, 2, 0, 0, 0, 0, 0, 0
# 1, 2, F, 1, 0, 0, 0, 0, 0, 0
# """
