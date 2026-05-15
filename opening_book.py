# AI

import struct

def _is_prime(n):
    if n < 2:
        return False
    for i in range(2, int(n ** 0.5) + 1):
        if n % i == 0:
            return False
    return True

def _next_prime(n):
    while not _is_prime(n):
        n += 1
    return n

def _encode(cols, player, mask, height):
    key = 0
    for col in cols:
        pos = 1 << (col * (height + 1))
        while pos & mask:
            key *= 3
            key += 1 if (pos & player) else 2
            pos <<= 1
        key *= 3
    return key

# compute_key3(current_player, mask) computes Pascal Pons's canonical base-3 position key
def compute_key3(current_player, mask, width=7, height=6):
    fwd = _encode(range(width), current_player, mask, height)
    rev = _encode(range(width - 1, -1, -1), current_player, mask, height)
    return min(fwd, rev) // 3

class OpeningBook():
    def __init__(self, width=7, height=6):
        self.width = width
        self.height = height
        self.depth = -1
        self.size = None
        self.key_bytes = None
        self.keys = None
        self.values = None

    def load(self, filename):
        with open(filename, 'rb') as f:
            width = struct.unpack('B', f.read(1))[0]
            height = struct.unpack('B', f.read(1))[0]
            depth = struct.unpack('B', f.read(1))[0]
            key_bytes = struct.unpack('B', f.read(1))[0]
            value_bytes = struct.unpack('B', f.read(1))[0]
            log_size = struct.unpack('B', f.read(1))[0]

            self.depth = depth
            self.key_bytes = key_bytes
            self.size = _next_prime(1 << log_size)

            fmt = {1: 'B', 2: 'H', 4: 'I'}[key_bytes]
            kdata = f.read(self.size * key_bytes)
            vdata = f.read(self.size)

            self.keys = struct.unpack(f'<{self.size}{fmt}', kdata)
            self.values = struct.unpack(f'<{self.size}B', vdata)

        print(f"Opening book loaded: depth={depth}, size={self.size}")

    def lookup(self, key):
        index = key % self.size
        m = (1 << (self.key_bytes * 8)) - 1
        if self.keys[index] == (key & m):
            return self.values[index]
        return 0

    def query(self, board):
        if self.keys is None or board.turn > self.depth:
            return None

        # terminal positions (raw=0) aren't in the book, check for immediate wins first
        for col in board.get_legal_moves():
            board.add_piece(col)
            if board.check_result():
                board.undo_move(col)
                return col
            board.undo_move(col)

        best = None
        best_col = None

        for col in board.get_legal_moves():
            board.add_piece(col)
            raw = self.lookup(compute_key3(board.current_player, board.mask))
            board.undo_move(col)

            if raw == 0:
                continue

            # lower score for opponent = better for bot
            if best is None or raw < best:
                best = raw
                best_col = col

        return best_col

book = OpeningBook()

def load_book(filename="data/7x6.book"):
    book.load(filename)

def query_book(board):
    return book.query(board)

_c4_book = {}

def load_c4_book(filename="data/opening_book.c4b"):
    global _c4_book
    try:
        with open(filename, 'rb') as f:
            magic = f.read(4)
            if magic != b'C4BK':
                return
            # skip version field
            f.read(4)
            count = struct.unpack('<I', f.read(4))[0]
            for _ in range(count):
                k1, k2 = struct.unpack('<QQ', f.read(16))
                col = struct.unpack('b', f.read(1))[0]
                _c4_book[(k1, k2)] = col
        print(f"C book loaded: {len(_c4_book)} positions")
    except FileNotFoundError:
        pass

def query_c4_book(board):
    return _c4_book.get((board.current_player, board.mask))
