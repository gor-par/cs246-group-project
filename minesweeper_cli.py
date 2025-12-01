"""
Small AI-generated module for playing the game in the CLI, outside of the project scope, just for our own convenience
"""

import sys
import time
from minesweeper import (
    Minesweeper,
)  # Assuming the provided script is saved as minesweeper.py


def format_board(board):
    """
    Formats the Minesweeper board for readable terminal output,
    including column and row indices.
    """
    if not board:
        return "Board is empty."

    # Get dimensions
    height = len(board)
    width = len(board[0])

    # 1. Create the column indices header
    # Add an extra space for the row index column
    header = "    " + " ".join(f"{i:2}" for i in range(width)) + "\n"
    # Add a separator line
    header += "   " + "-" * (width * 3 + 1) + "\n"

    # 2. Format each row with row indices
    formatted_rows = []
    for i in range(height):
        # Format the row index, then the cells
        row_str = f"{i:2} | " + " ".join(f"{str(cell):2}" for cell in board[i])
        formatted_rows.append(row_str)

    # Combine header and rows
    return header + "\n".join(formatted_rows)


def get_game_parameters():
    """Prompts the user for width, height, mines, and optional seed."""
    print("\n--- Minesweeper Game Setup 💣 ---")

    # Get Width
    while True:
        try:
            width = int(input("Enter board width (e.g., 10): "))
            if width <= 0:
                raise ValueError
            break
        except ValueError:
            print("Invalid input. Please enter a positive integer for width.")

    # Get Height
    while True:
        try:
            height = int(input("Enter board height (e.g., 10): "))
            if height <= 0:
                raise ValueError
            break
        except ValueError:
            print("Invalid input. Please enter a positive integer for height.")

    # Get Mines
    max_mines = width * height
    while True:
        try:
            mines = int(input(f"Enter number of mines (Max: {max_mines}): "))
            if not (0 < mines < max_mines):
                print(
                    f"Number of mines must be greater than 0 and less than {max_mines}."
                )
                continue
            break
        except ValueError:
            print("Invalid input. Please enter a positive integer for mines.")

    # Get Seed (Optional)
    seed_input = input("Enter an optional integer seed (Press Enter for random): ")
    if seed_input:
        try:
            seed = int(seed_input)
        except ValueError:
            print("Invalid seed input. Using a random seed instead.")
            seed = int(time.time() * 1000)
    else:
        seed = int(time.time() * 1000)  # Default to a time-based seed

    print(f"\nGame parameters: W={width}, H={height}, M={mines}, Seed={seed}")
    return width, height, mines, seed


def get_action_input(width, height):
    """
    Prompts the user for an action (reveal/flag) and coordinates.
    e.g., "R 5 3" to Reveal cell (5, 3) or "F 1 8" to Flag cell (1, 8).
    """
    prompt_msg = (
        f"\nEnter action (R x y to Reveal, F x y to Flag, Q to Quit).\n"
        f"x: 0-{width-1}, y: 0-{height-1}\n"
        f"Input (e.g., R 5 3): "
    )

    while True:
        try:
            user_input = input(prompt_msg).strip().upper()

            if user_input == "Q":
                return "Q", 0, 0

            parts = user_input.split()
            if len(parts) != 3:
                raise ValueError("Input must be in the format 'A x y' (e.g., R 5 3).")

            action = parts[0]
            x = int(parts[1])
            y = int(parts[2])

            if action not in ("R", "F"):
                raise ValueError("Action must be 'R' (Reveal) or 'F' (Flag).")

            if not (0 <= x < width and 0 <= y < height):
                raise ValueError(
                    f"Coordinates out of bounds. x must be 0-{width-1}, y must be 0-{height-1}."
                )

            return action, x, y

        except ValueError as e:
            print(f"Invalid input: {e}. Please try again.")
        except IndexError:
            print("Invalid input format. Please try again.")


def run_cli():
    """Main function to run the Minesweeper CLI game."""

    # 1. Get Game Parameters
    try:
        width, height, mines, seed = get_game_parameters()
    except Exception as e:
        print(f"An error occurred during setup: {e}")
        sys.exit(1)

    # 2. Initialize Game
    game = Minesweeper()
    game.start_new_game(width, height, mines, seed)

    # 3. Game Loop
    print("\n--- Game Started! ---")
    while True:
        # Get and print current state
        state = game.current_state
        print("\n" + "=" * 50)
        print(f"⏱️  Time: {state['time']:.2f}s | 🚩 Status: **{state['status']}**")
        print("-" * 50)
        print(format_board(state["board"]))
        print("=" * 50)

        if game.game_over:
            print(f"\nGame **{state['status']}**! Final time: {state['time']:.2f}s")
            break

        # Get user action
        action, x, y = get_action_input(width, height)

        if action == "Q":
            print("Quitting game. Goodbye!")
            break

        try:
            if action == "R":
                result = game.reveal_cell(x, y)
                print(f"Action: **Reveal ({x}, {y})** | Result: **{result}**")

                # If defeat, update state one last time before loop ends
                if result == "DEFEAT":
                    state = game.current_state
                    print("\n" + "=" * 50)
                    print(f"💥 Game Over! You hit a mine at ({x}, {y})!")
                    print(
                        f"⏱️  Time: {state['time']:.2f}s | 🚩 Status: **{state['status']}**"
                    )
                    print("-" * 50)
                    print(format_board(game.full_board))  # Show the full board on loss
                    print("=" * 50)
                    break

                if result == "VICTORY":
                    state = game.current_state
                    print("\n" + "=" * 50)
                    print(f"🎉 **CONGRATULATIONS! YOU WON!** 🎉")
                    print(
                        f"⏱️  Time: {state['time']:.2f}s | 🚩 Status: **{state['status']}**"
                    )
                    print("-" * 50)
                    print(format_board(state["board"]))
                    print("=" * 50)
                    break

            elif action == "F":
                result = game.flag_cell(x, y)
                print(f"Action: **Flag ({x}, {y})** | Result: **{result}**")

        except ValueError as e:
            print(f"Error: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            break


if __name__ == "__main__":
    run_cli()
