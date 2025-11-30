import random


class Minesweeper:
    def __init__(self, width: int, height: int, mines: int, seed: int):
        self.board = Board.get_new_board(width, height, mines, seed)


# The awkward static method structure is to preserve a function-like signature and also have benefits of class methods
class Board:
    @staticmethod
    def get_new_board(width, height, mines, seed):
        return Board(width, height, mines, seed).board

    def __init__(self, width, height, mines, seed):
        random.seed(seed)

        self.width = width
        self.height = height
        self.mines = mines

        self.mine_coords = self.generate_mine_coordinates()
        self.board = self.populate_board()

    def generate_mine_coordinates(self):
        cell_positions_list = list(range(self.width * self.height))
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
        return str(adjacent_mines)


Minesweeper(10, 30, 50, 16)
