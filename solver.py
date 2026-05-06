from board import Board as b


def negamax(board, depth):
    status = board.check_result()
    # check if last move won the game
    if status != "":
        return -1
    # check if game or search is complete
    if board.is_full() or depth == 0:
        return 0
    
    best = float("-inf")
    for move in board.get_legal_moves():
        board.add_piece(board.pieces[board.turn % 2], move)
        score = -negamax(board, depth-1)
        board.undo_move(move)
        best = max(best, score)
    
    return best

def best_move(board, depth):
    best = float("-inf")
    best_move = None
    for move in board.get_legal_moves():
        board.add_piece(board.pieces[board.turn % 2], move)
        score = -negamax(board, depth-1)
        board.undo_move(move)
        if score > best:
            best = score
            best_move = move
    return best_move