# AI

from board import Board as b
from solver import best_move, policy_table
from opening_book import query_book, load_book, query_c4_book, load_c4_book
import sqlite3
import pickle
import os

DB_FILE = "data/opening_book.db"


def _init_db(filename=DB_FILE):
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    conn = sqlite3.connect(filename)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS book (
            player INTEGER NOT NULL,
            mask   INTEGER NOT NULL,
            col    INTEGER NOT NULL,
            PRIMARY KEY (player, mask)
        )
    """)
    conn.commit()
    return conn


def _flush(pending, conn):
    """Write only entries accumulated since the last flush — never the whole book."""
    if not pending:
        return
    conn.executemany(
        "INSERT OR REPLACE INTO book (player, mask, col) VALUES (?, ?, ?)",
        ((k[0], k[1], v) for k, v in pending.items())
    )
    conn.commit()
    pending.clear()


def load_book_db(filename=DB_FILE):
    """Load the full book from sqlite3 into a plain dict for fast in-memory lookup."""
    if not os.path.exists(filename):
        return {}
    conn = sqlite3.connect(filename)
    book = {(row[0], row[1]): row[2]
            for row in conn.execute("SELECT player, mask, col FROM book")}
    conn.close()
    return book


def _migrate_pkl(conn, pkl_path="data/opening_book.pkl"):
    """One-time migration of an existing pkl book into the sqlite3 db."""
    if not os.path.exists(pkl_path):
        return {}
    print(f"Migrating {pkl_path} → {DB_FILE} ...")
    try:
        with open(pkl_path, "rb") as f:
            old = pickle.load(f)
    except (EOFError, pickle.UnpicklingError):
        print("pkl file is corrupted (truncated mid-write from a previous crash) — starting fresh.")
        return {}
    if old:
        conn.executemany(
            "INSERT OR REPLACE INTO book (player, mask, col) VALUES (?, ?, ?)",
            ((k[0], k[1], v) for k, v in old.items())
        )
        conn.commit()
    print(f"Migrated {len(old)} positions.")
    return old


def build_book(board, depth, book, counter, min_turn, pending, conn):
    if depth == 0 or board.is_full() or board.check_result():
        return

    key = (board.current_player, board.mask)

    if board.turn % 2 == 0:  # bot's turn
        if board.turn < min_turn:
            for move in board.get_legal_moves():
                board.add_piece(move)
                build_book(board, depth - 1, book, counter, min_turn, pending, conn)
                board.undo_move(move)
            return

        if key in book:
            board.add_piece(book[key])
            build_book(board, depth - 1, book, counter, min_turn, pending, conn)
            board.undo_move(book[key])
            return

        # check fastest sources first; policy_table fills as a negamax side-effect
        col = policy_table.get(key)
        if col is not None:
            source = "policy"
        else:
            col = query_book(board)
            if col is not None:
                policy_table[key] = col
                source = "pons"
            else:
                col = query_c4_book(board)
                if col is not None:
                    policy_table[key] = col
                    source = "c4b"
                else:
                    col = best_move(board)   # also populates policy_table
                    source = "solver"

        book[key] = col
        pending[key] = col          # queued for the next incremental flush
        board.add_piece(col)
        counter[0] += 1
        print(f"[{source:6}] position {counter[0]} | turn {board.turn - 1} | col {col + 1}")

        if counter[0] % 500 == 0:
            _flush(pending, conn)   # write only the new 500 rows — no memory spike
            print(f"--- checkpoint: {counter[0]} stored | "
                  f"{len(book)} in memory | {len(policy_table)} in policy_table ---")

        build_book(board, depth - 1, book, counter, min_turn, pending, conn)
        board.undo_move(col)

    else:  # human's turn — explore every legal response
        for move in board.get_legal_moves():
            board.add_piece(move)
            build_book(board, depth - 1, book, counter, min_turn, pending, conn)
            board.undo_move(move)


def generate_book(depth):
    load_book("data/7x6.book")
    load_c4_book("data/opening_book.c4b")

    board = b()
    counter = [0]
    pending = {}

    conn = _init_db()

    # migrate pkl → sqlite3 the first time (if db is empty but pkl exists)
    db_count = conn.execute("SELECT COUNT(*) FROM book").fetchone()[0]
    if db_count == 0:
        book = _migrate_pkl(conn)
    else:
        book = load_book_db()

    print(f"Resuming from {len(book)} existing positions")

    try:
        build_book(board, depth, book, counter, 0, pending, conn)
        print(f"Book generation complete. {counter[0]} new positions added.")
    except KeyboardInterrupt:
        print(f"Interrupted — flushing {len(pending)} pending positions...")
    finally:
        _flush(pending, conn)
        conn.close()
        print(f"Done. Total book size: {len(book)} positions.")


if __name__ == "__main__":
    generate_book(42)
