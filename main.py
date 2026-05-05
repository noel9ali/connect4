from board import Board as b

def main():
    pieces = ("X", "O")
    board = b()

    while(True):
        player = board.turn % 2
        print(f"Your turn, Player {player+1} ({pieces[player]}).")
        try:
            col = int(input(f"Choose a column to play in: ")) - 1
        except ValueError:
            print("Please enter an integer.")
            continue
        move = [pieces[player], col]
        retval = board.add_piece(*move)
        if retval == b.BOUNDS_ERROR or retval == b.COL_FULL:
            continue

        print(f"Placed {pieces[player]} in column {col}.")
        board.print()
        result = board.check_result()
        if result != "":
            print(f"Player {player+1} wins!")
            break
        else:
            for i in range(board.cols):
                if board.arr[board.rows - 1][i] == " ":
                    break
            else: 
                print("The board is full! The game ends in a tie :(")
                break
            board.turn += 1



if __name__ == "__main__":
    main()