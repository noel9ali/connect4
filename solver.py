# Human negamax, else AI

from board import Board as b

transposition_table = {}
policy_table = {}  # (current_player, mask) -> best column to play

def negamax(board, alpha, beta):
    status = board.check_result()
    # positions are scored based on how quickly they win
    if status:
        return -(board.cols * board.rows + 1 - board.turn)
    # check if board is full
    if board.is_full():
        return 0

    legal = board.get_legal_moves()

    for move in legal:
        board.add_piece(move)
        win = board.check_result()
        board.undo_move(move)
        if win:
            # winning move, ignore rest of search
            key = (board.current_player, board.mask)
            policy_table[key] = move
            return board.rows * board.cols - board.turn

    order = sorted(range(board.cols), key=lambda col: abs(col - board.cols // 2))

    key = (board.current_player, board.mask)

    # if we already know the best move for this position from a prior search, try it first
    if key in policy_table:
        hint = policy_table[key]
        if hint in legal:
            order = [hint] + [c for c in order if c != hint]

    # check for key in transposition table
    if key in transposition_table:
        flag, val = transposition_table[key]
        if flag == "exact":
            return val
        elif flag == "lower":
            alpha = max(alpha, val)
        else:
            beta = min(beta, val)
        if beta <= alpha:
            return val

    # store starting alpha for comparison
    alpha_null = alpha
    best = float("-inf")
    best_col = None

    for move in order:
        if move not in legal:
            continue
        board.add_piece(move)
        score = -negamax(board, -beta, -alpha)
        board.undo_move(move)
        if score > best:
            best = score
            best_col = move
        if score >= beta:
            # beta cutoff, this move is good enough, store it
            transposition_table[key] = ("lower", beta)
            policy_table[key] = best_col
            return beta
        alpha = max(alpha, score)

    # store the optimal move
    if best_col is not None:
        policy_table[key] = best_col

    if best > alpha_null:
        transposition_table[key] = ("exact", best)
    else:
        transposition_table[key] = ("upper", best)
    return best

def best_move(board):
    legal = board.get_legal_moves()

    # always check for an immediate winning move first
    for move in legal:
        board.add_piece(move)
        win = board.check_result()
        board.undo_move(move)
        if win:
            return move

    key = (board.current_player, board.mask)
    order = sorted(range(board.cols), key=lambda col: abs(col - board.cols // 2))

    # use any cached hint only for move ordering, never as a definitive answer
    if key in policy_table:
        hint = policy_table[key]
        if hint in legal:
            order = [hint] + [c for c in order if c != hint]

    best = float("-inf")
    best_col = None
    alpha = -(board.cols * board.rows)
    beta = board.cols * board.rows

    for move in order:
        if move not in legal:
            continue
        board.add_piece(move)
        score = -negamax(board, -beta, -alpha)
        board.undo_move(move)
        if score > best:
            best = score
            best_col = move
        alpha = max(alpha, score)
        if alpha >= beta:
            break

    policy_table[key] = best_col
    return best_col

if __name__ == "__main__":
    import time
    board = b()
    start = time.time()
    move = best_move(board)
    elapsed = time.time() - start
    print(f"Best move: {move + 1}, Time: {elapsed:.2f}s")
