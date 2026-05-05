from board import Board as b, build_tree
from manim import *

class DisplayBoard(Scene):
    def construct(self):
        board = b()
        board.arr[0][0] = "X"
        board.arr[0][1] = "O"
        board.arr[0][2] = "X"
        board.arr[1][0] = "O"
        group = display_board(board)
        group.move_to(ORIGIN)
        self.play(Create(group))
        self.wait(1)

class GameTree(MovingCameraScene):
    def construct(self):
        self.play(self.camera.frame.animate.set_width(4).move_to(LEFT * 2.5))
        board = b()
        tree = build_tree(board, 2)
        root_group = display_board(tree["board"], LEFT * 2.5)
        root_group.scale(0.5)
        self.play(Create(root_group))
        self.wait(1)
        self.play(self.camera.frame.animate.set_width(9).move_to(ORIGIN))
        self.wait(0.5)
        i = 1
        for node in tree["children"]:
            line = Line(LEFT * 1, RIGHT * 1.5 + UP * 2 * (4 - i))
            self.play(Create(line, run_time=0.3))
            node_group = display_board(node["board"], RIGHT * 2.5 + UP * 2 * (4 - i))
            node_group.scale(0.3)
            self.play(Create(node_group, run_time=0.3))
            i += 1
        self.wait(1)
        self.play(self.camera.frame.animate.set_width(6).move_to(RIGHT * 4.5))
        self.wait(1)
        middle_node = tree["children"][4]
        i = 1
        for node in middle_node["children"]:
            line = Line(RIGHT * 3.5, RIGHT * 5.3 + UP * 1.5 * (4 - i))
            self.play(Create(line, run_time=0.3))
            node_group = display_board(node["board"], RIGHT * 6 + UP * 1.5 * (4 - i))
            node_group.scale(0.25)
            self.play(Create(node_group, run_time=0.3))
            i += 1
        self.wait(1)


# display_board(board) produces manim animation for a given board state
def display_board(board, location=ORIGIN):
    group = VGroup()
    for row in reversed(range(6)):
        for col in range(7):
            if board.arr[5 - row][col] == " ":
                circle = Circle(radius=0.3, color=WHITE)
            elif board.arr[5 - row][col] == "X":
                circle = Circle(radius=0.3, color=RED, fill_color=RED, fill_opacity=0.8)
            else:
                circle = Circle(radius=0.3, color=YELLOW, fill_color=YELLOW, fill_opacity=0.8)
            circle.move_to(RIGHT * col * 0.7 + DOWN * row * 0.7)   
            group.add(circle)
    group.move_to(location)
    return group
