# AI

from board import Board as b, PIECES
from solver import best_move
from opening_book import load_book, query_book
import pickle
import os

def load_pkl_book(filename="data/opening_book.pkl"):
    if os.path.exists(filename):
        with open(filename, "rb") as f:
            book = pickle.load(f)
        print(f"Loaded pkl book: {len(book)} positions")
        return book
    print("No pkl book found — run book_builder.py to generate one.")
    return {}

def query_pkl_book(book, board):
    return book.get((board.current_player, board.mask))

def main():
    board = b()
    load_book("data/7x6.book")
    pkl_book = load_pkl_book()

    while True:
        player = board.turn % 2
        board.print()

        if player == 0:
            print("Bot is thinking...")
            col = query_pkl_book(pkl_book, board)
            if col is not None:
                print("Bot is thinking... (pkl book)")
            else:
                col = query_book(board)
                if col is not None:
                    print("Bot is thinking... (binary book)")
                else:
                    print("Bot is thinking... (solver)")
                    col = best_move(board)
            board.add_piece(col)
        else:
            print(f"Your turn ({PIECES[player]}).")
            try:
                col = int(input(f"Choose a column to play in: ")) - 1
            except ValueError:
                print("Please enter an integer.")
                continue
            retval = board.add_piece(col)
            if retval == b.BOUNDS_ERROR or retval == b.COL_FULL:
                continue

        result = board.check_result()
        if result:
            board.print()
            print("You win!" if player == 1 else "Bot wins!")
            break
        elif board.is_full():
            board.print()
            print("Board is full. The game ends in a draw :(")
            break

if __name__ == "__main__":
    main()
