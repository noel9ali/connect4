from manim import *

class GameTree(Scene):
    def construct(self):
        # Root node
        root = Dot(point=UP * 2, radius=0.2, color=WHITE)
        self.play(Create(root))
        self.wait(0.5)

        # Child nodes
        left = Dot(point=UP * 0.5 + LEFT * 2, radius=0.2, color=WHITE)
        right = Dot(point=UP * 0.5 + RIGHT * 2, radius=0.2, color=WHITE)

        # Lines connecting root to children
        left_line = Line(root.get_center(), left.get_center())
        right_line = Line(root.get_center(), right.get_center())

        self.play(Create(left_line), Create(right_line))
        self.play(Create(left), Create(right))
        self.wait(0.5)