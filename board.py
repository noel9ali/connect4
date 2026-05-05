class Board():
    COL_FULL = -1
    BOUNDS_ERROR = -2

    def __init__(self, cols=7, rows=6):
        self.cols = cols
        self.rows = rows
        self.arr = [[" "] * cols for _ in range(rows)]
        self.turn = 0
    
    def add_piece(self, piece, col):
        if col >= self.cols or col < 0:
            print(f"Invalid column. Please try again.")
            return self.BOUNDS_ERROR
        if self.arr[self.rows - 1][col] != " ":
            print(f"Column {col} is full, try another row.")
            return self.COL_FULL
        for row in range(self.rows):
            if self.arr[row][col] == " ":
                self.arr[row][col] = piece
                return row
    
    def print(self):
        print("  " + "".join(f"{i+1}   " for i in range(self.cols)))
        for row in reversed(range(self.rows)):
            print("".join("+---" for i in range(self.cols)) + "+")
            print("".join("|   " for i in range(self.cols)) + "|")
            print("".join(f"| {self.arr[row][i]} " for i in range(self.cols)) + "|")
            print("".join("|   " for i in range(self.cols)) + "|")
        print("".join("+---" for i in range(self.cols)) + "+")

    def valid_point(self, row, col):
        return (row >= 0 and row < self.rows) and (col >=0 and col < self.cols)

    def check_result(self):
        directions = ((0, 1), (1, 0), (1, 1), (1, -1))
        for row in range(self.rows):
            for col in range(self.cols):
                index = self.arr[row][col]
                if index  == " ":
                    continue
                for (dr, dc) in directions:
                    for i in range(1, 4):
                        point = (row + i * dr, col + i * dc)
                        if not self.valid_point(*point) or self.arr[point[0]][point[1]] != index:
                            break
                    else:
                        return index
        return ""
    
    def get_legal_moves(self):
        legal = []
        for col in range(7):
            if self.arr[5][col] == " ":
                legal.append(col)
        return legal

    def copy(self):
        b = Board()
        b.rows = self.rows
        b.cols = self.cols
        b.turn = self.turn
        for i in range(self.rows):
            for j in range(self.cols):
                b.arr[i][j] = self.arr[i][j]
        return b    
    
# build_tree(board, depth) builds a tree of all possible legal moves with a given depth
def build_tree(board, depth):
    pieces = ("X", "O")
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
        temp.add_piece(pieces[temp.turn % 2], i)
        temp.turn += 1
        child_node = build_tree(temp, depth-1)
        node["children"].append(child_node)
    return node