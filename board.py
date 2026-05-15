# init, print, valid_point, check_result, get_legal_moves, copy, is_full, build_tree all human, rest AI

PIECES = ("O", "X")

class Board():
    COL_FULL = -1
    BOUNDS_ERROR = -2

    def __init__(self, cols=7, rows=6):
        self.current_player = 0
        self.mask = 0
        self.turn = 0
        self.cols = cols
        self.rows = rows
        self.heights = [col * (rows + 1) for col in range(cols)]

    def add_piece(self, col):
        if col >= self.cols or col < 0:
            print(f"Invalid column. Please try again.")
            return self.BOUNDS_ERROR
        if self.heights[col] >= col * (self.rows + 1) + self.rows:
            print(f"Column {col + 1} is full, try another.")
            return self.COL_FULL
        self.current_player ^= self.mask
        self.mask |= 1 << self.heights[col]
        self.heights[col] += 1
        self.turn += 1

    def print(self):
        print("  " + "".join(f"{i+1}   " for i in range(self.cols)))
        for row in reversed(range(self.rows)):
            print("".join("+---" for i in range(self.cols)) + "+")
            print("".join("|   " for i in range(self.cols)) + "|")
            row_str = ""
            for col in range(self.cols):
                bit = row + col * (self.rows + 1)
                if self.mask & (1 << bit):
                    if self.current_player & (1 << bit):
                        piece = PIECES[self.turn % 2]
                    else:
                        piece = PIECES[(self.turn + 1) % 2]
                    row_str += f"| {piece} "
                else:
                    row_str += "|   "
            print(row_str + "|")
            print("".join("|   " for i in range(self.cols)) + "|")
        print("".join("+---" for i in range(self.cols)) + "+")

    def valid_point(self, row, col):
        return (row >= 0 and row < self.rows) and (col >= 0 and col < self.cols)

    def check_result(self):
        directions = [self.rows + 1, 1, self.rows + 2, self.rows]
        other_player = self.current_player ^ self.mask

        for direction in directions:
            m = other_player & (other_player >> direction)
            if m & (m >> (2 * direction)):
                return True
        return False

    def get_legal_moves(self):
        legal = []
        for col in range(self.cols):
            if self.heights[col] < col * (self.rows + 1) + self.rows:
                legal.append(col)
        return legal

    def copy(self):
        b = Board(self.cols, self.rows)
        b.current_player = self.current_player
        b.mask = self.mask
        b.turn = self.turn
        b.heights = self.heights[:]
        return b

    def is_full(self):
        for col in range(self.cols):
            if self.heights[col] < col * (self.rows + 1) + self.rows:
                return False
        return True

    def undo_move(self, col):
        self.heights[col] -= 1
        self.turn -= 1
        self.mask &= ~(1 << self.heights[col])
        self.current_player ^= self.mask


# build_tree(board, depth) builds a tree of all possible legal moves with a given depth
def build_tree(board, depth):
    node = {
    "board": board,
    "children": []
    }
    # base case
    if depth == 0:
        return node

    # create subtree for each legal move recursively
    legal_moves = board.get_legal_moves()
    for i in legal_moves:
        temp = board.copy()
        temp.add_piece(i)
        child_node = build_tree(temp, depth-1)
        node["children"].append(child_node)
    return node
