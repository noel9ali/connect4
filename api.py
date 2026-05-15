# AI

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from board import Board
from solver import best_move
from opening_book import load_book, query_book
import sqlite3
import pickle
import os
import secrets

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DIST_DIR = os.path.join(BASE_DIR, "frontend", "dist")

app = Flask(__name__, static_folder=DIST_DIR, static_url_path="")
app.secret_key = secrets.token_hex(32)
CORS(app)

load_book("data/7x6.book")

def _load_pkl_book():
    # prefer the sqlite3 db; fall back to pkl for backwards compatibility
    db = "data/opening_book.db"
    pkl = "data/opening_book.pkl"
    if os.path.exists(db):
        conn = sqlite3.connect(db)
        book = {(row[0], row[1]): row[2]
                for row in conn.execute("SELECT player, mask, col FROM book")}
        conn.close()
        return book
    if os.path.exists(pkl):
        with open(pkl, "rb") as f:
            return pickle.load(f)
    return {}

pkl_book = _load_pkl_book()


def _query_pkl_book(board):
    return pkl_book.get((board.current_player, board.mask))


def _get_bot_move(board):
    col = _query_pkl_book(board)
    if col is None:
        col = query_book(board)
    if col is None:
        col = best_move(board)
    return col


def board_to_grid(board):
    rows, cols = board.rows, board.cols
    grid = [[0] * cols for _ in range(rows)]
    for col in range(cols):
        for row in range(rows):
            bit = row + col * (rows + 1)
            if board.mask & (1 << bit):
                is_current = bool(board.current_player & (1 << bit))
                # Bot goes first (turn 0), so:
                # turn%2==0 → bot moves next   → current_player = bot's pieces
                # turn%2==1 → human moves next → current_player = human's pieces
                if board.turn % 2 == 0:
                    grid[row][col] = 2 if is_current else 1
                else:
                    grid[row][col] = 1 if is_current else 2
    return grid


def _serialize(board):
    return {
        "current_player": board.current_player,
        "mask": board.mask,
        "turn": board.turn,
        "heights": board.heights[:],
    }


def _deserialize(data):
    board = Board()
    board.current_player = data["current_player"]
    board.mask = data["mask"]
    board.turn = data["turn"]
    board.heights = list(data["heights"])
    return board


def _state(board, game_over=False, winner=None, last_bot_col=None):
    return {
        "grid": board_to_grid(board),
        "turn": board.turn,
        "game_over": game_over,
        "winner": winner,
        "last_bot_col": last_bot_col,
        "board_data": _serialize(board),
    }


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_frontend(path):
    full = os.path.join(DIST_DIR, path)
    if path and os.path.isfile(full):
        return send_from_directory(DIST_DIR, path)
    return send_from_directory(DIST_DIR, "index.html")


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"ok": True})


@app.route("/api/new-game", methods=["POST"])
def new_game():
    board = Board()
    bot_col = _get_bot_move(board)
    board.add_piece(bot_col)
    return jsonify(_state(board, last_bot_col=bot_col))


@app.route("/api/move", methods=["POST"])
def move():
    body = request.get_json()
    board = _deserialize(body["board_state"]["board_data"])
    col = int(body["col"])

    result = board.add_piece(col)
    if result in (Board.COL_FULL, Board.BOUNDS_ERROR):
        return jsonify({"error": "Invalid move"}), 400

    if board.check_result():
        return jsonify(_state(board, game_over=True, winner="player"))
    if board.is_full():
        return jsonify(_state(board, game_over=True, winner="draw"))

    bot_col = _get_bot_move(board)
    board.add_piece(bot_col)

    if board.check_result():
        return jsonify(_state(board, game_over=True, winner="bot", last_bot_col=bot_col))
    if board.is_full():
        return jsonify(_state(board, game_over=True, winner="draw", last_bot_col=bot_col))

    return jsonify(_state(board, last_bot_col=bot_col))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
