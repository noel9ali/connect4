# Human

from board import Board as b, build_tree
from manim import *

class DisplayBoard(Scene):
    def construct(self):
        board = b()
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

class PlotFunction(Scene):
    def construct(self):
        # 1. Create axes
        axes = Axes(
            x_range=[0, 4, 1],   # [min, max, step]
            y_range=[0, 400, 100],
            x_length=8,
            y_length=6,
            axis_config={
                "include_numbers": True,
                "include_tip": False,
            }
        )

        # 2. Plot your function
        graph = axes.plot(lambda x: 7**x, x_range=[0, 3.08], color=BLUE)

        # 3. Add a label
        label = axes.get_graph_label(graph, label="f(x)", x_val=3, direction=RIGHT, buff=0)

        pt1 = Dot(axes.input_to_graph_point(1, graph), color=YELLOW)
        label1 = MathTex("(1, 7)").next_to(pt1, UL, buff=0.15)
        pt2 = Dot(axes.input_to_graph_point(2, graph), color=YELLOW)
        label2 = MathTex("(2, 49)").next_to(pt2, UL, buff=0.15)
        pt3 = Dot(axes.input_to_graph_point(3, graph), color=YELLOW)
        label3 = MathTex("(3, 343)").next_to(pt3, UL, buff=0.15)
        group = VGroup(axes, graph, pt1, label1, pt2, label2, pt3, label3)
        group.scale(0.8)

        # 4. Animate
        self.play(Create(axes))
        self.wait(1)
        self.play(Create(graph), Write(label))
        self.wait(2)
        self.play(Create(pt1), Write(label1), duration=0.5)
        self.wait(0.3)
        self.play(Create(pt2), Write(label2), duration=0.5)
        self.wait(0.3)
        self.play(Create(pt3), Write(label3), duration=0.5)
        self.wait(0.3)

class Pruning(MovingCameraScene):
    def construct(self):
        SCORES       = [-3, 2, 5, 9, 4, 1, -1]
        SCORE_COLORS = [RED, WHITE, YELLOW, GREEN, YELLOW, WHITE, RED]
        BEST_IDX     = 3  # center column has the highest score

        self.play(self.camera.frame.animate.set_width(11).move_to(ORIGIN))

        board = blocking_position
        tree  = build_tree(board, 1)

        root_group = display_board(tree["board"], LEFT * 2.5)
        root_group.scale(0.5)
        self.play(Create(root_group))
        self.wait(0.5)

        alpha_text = MathTex(r"\alpha = -\infty", font_size=36).next_to(root_group, DOWN, buff=0.3)
        self.play(Write(alpha_text))
        self.wait(0.3)

        lines, boards, score_labels = [], [], []
        best_so_far = float("-inf")
        pruned_indices = []

        i = 1
        for node_idx, node in enumerate(tree["children"]):
            y_offset   = UP * 2 * (4 - i)
            line       = Line(LEFT * 1, RIGHT * 1.5 + y_offset)
            self.play(Create(line, run_time=0.25))
            lines.append(line)

            node_group = display_board(node["board"], RIGHT * 2.5 + y_offset)
            node_group.scale(0.3)
            self.play(Create(node_group, run_time=0.25))
            boards.append(node_group)

            score     = SCORES[node_idx]
            score_tex = Text(str(score), font_size=30, color=SCORE_COLORS[node_idx])
            score_tex.next_to(node_group, RIGHT, buff=0.3)
            self.play(Write(score_tex, run_time=0.3))
            score_labels.append(score_tex)

            if score < best_so_far:
                # score is below alpha — prune immediately
                self.play(
                    FadeOut(boards[node_idx]),
                    FadeOut(lines[node_idx]),
                    FadeOut(score_labels[node_idx]),
                    run_time=0.3,
                )
                pruned_indices.append(node_idx)
            else:
                best_so_far = score
                new_alpha   = MathTex(rf"\alpha = {score}", font_size=24).next_to(root_group, DOWN, buff=0.3)
                self.play(Transform(alpha_text, new_alpha, run_time=0.3))

            self.wait(0.2)
            i += 1

        self.wait(1)

        rect = SurroundingRectangle(boards[BEST_IDX], color=GREEN, buff=0.15, stroke_width=6)
        self.play(Create(rect))
        self.wait(0.7)

        non_best = [j for j in range(len(boards)) if j != BEST_IDX and j not in pruned_indices]
        if non_best:
            self.play(*[lines[j].animate.set_color(RED) for j in non_best])
            self.wait(0.4)

        self.play(
            *[FadeOut(boards[j]) for j in non_best],
            *[FadeOut(lines[j]) for j in non_best],
            *[FadeOut(score_labels[j]) for j in non_best],
            FadeOut(rect),
            FadeOut(alpha_text)
        )

        self.play(
            boards[BEST_IDX].animate.scale(3),
            FadeOut(root_group),
            FadeOut(lines[BEST_IDX]),
            FadeOut(score_labels[BEST_IDX]),
            self.camera.frame.animate.set_width(5).move_to(RIGHT * 2.5),
        )
        self.wait(1)

class Combinations(Scene):
    def construct(self):
        upper = MathTex("311,973,482,284,542,371,").move_to(UP * 0.25)
        lower = MathTex("301,330,321,821,976,049").move_to(DOWN * 0.25)
        group = upper
        group.add(lower)
        self.play(Create(group))
        self.wait(1.5)
        final = MathTex("4,531,985,219,092")
        self.play(TransformMatchingShapes(group, final))
        self.wait(1)

class InfeasibleBoards(Scene):
    def construct(self):
        board = b()
        moves = [0, 1, 1, 2, 3, 2, 2, 3, 3, 4, 3]
        # fill remaining spots column by column
        fill = [0]*5 + [1]*4 + [2]*3 + [3]*2 + [4]*5 + [5]*6 + [6]*6
        for col in moves + fill:
            board.add_piece(col)
        group = display_board(board)
        self.play(Create(group))
        self.wait(0.5)
        line = Line(LEFT * 2.15 + DOWN * 1.8, UP * 0.35, color=GREEN, stroke_width=8)
        self.play(Create(line))
        self.wait(1)


class TranspositionTable(Scene):
    def construct(self):
        # --- Setup ---
        board_a = b()
        board_b = b()

        group_a = display_board(board_a, ORIGIN)
        group_a.scale(0.6).move_to(LEFT * 2.5)
        group_b = display_board(board_b, ORIGIN)
        group_b.scale(0.6).move_to(RIGHT * 2.5)

        label_a = Text("Path A", font_size=32).next_to(group_a, UP, buff=0.3)
        label_b = Text("Path B", font_size=32).next_to(group_b, UP, buff=0.3)

        self.play(Create(group_a), Create(group_b))
        self.play(Write(label_a), Write(label_b))
        self.wait(0.5)

        def player_color(turn):
            return YELLOW if turn % 2 == 0 else RED

        def drop_piece(board, group, col):
            row = board.heights[col] - col * (board.rows + 1)
            idx = row * board.cols + col
            color = player_color(board.turn)
            board.add_piece(col)
            return group[idx].animate.set_fill(color, opacity=0.8).set_stroke(color)

        def col_dot(group, col, color):
            x = group[col].get_center()[0]
            top_y = group.get_top()[1]
            return Dot(point=[x, top_y + 0.35, 0], color=color, radius=0.15)

        moves_a = [3, 3, 4, 5]
        moves_b = [4, 5, 3, 3]

        for i in range(4):
            color = player_color(board_a.turn)
            dot_a = col_dot(group_a, moves_a[i], color)
            anim_a = drop_piece(board_a, group_a, moves_a[i])
            dot_b = col_dot(group_b, moves_b[i], color)
            anim_b = drop_piece(board_b, group_b, moves_b[i])
            self.play(FadeIn(dot_a), FadeIn(dot_b), run_time=0.2)
            self.play(anim_a, anim_b, FadeOut(dot_a), FadeOut(dot_b), run_time=0.5)
            self.wait(0.2)

        self.wait(0.4)

        # --- Reveal: same position ---
        rect_a = SurroundingRectangle(group_a, color=GREEN, buff=0.15, stroke_width=4)
        rect_b = SurroundingRectangle(group_b, color=GREEN, buff=0.15, stroke_width=4)
        same_text = Text("Same Position!", font_size=34, color=GREEN).move_to(UP * 3.2)

        self.play(Create(rect_a), Create(rect_b), Write(same_text), run_time=0.7)
        self.wait(0.8)

        # --- Merge ---
        tt_label = Text("Transposition Table", font_size=30, color=GOLD_A).move_to(UP * 3.2)
        self.play(
            Transform(same_text, tt_label),
            FadeOut(rect_a), FadeOut(rect_b),
            FadeOut(label_a), FadeOut(label_b),
            run_time=0.7,
        )
        self.wait(0.3)

        self.play(
            group_a.animate.move_to(ORIGIN),
            group_b.animate.move_to(ORIGIN),
            run_time=1.0,
        )
        self.play(FadeOut(group_b), run_time=0.5)

        self.wait(2)


def _make_blocking_position():
    board = b()
    board.current_player = 13297218764801
    board.mask           = 13434940833921
    board.heights        = [1, 8, 15, 24, 29, 38, 44]
    board.turn           = 12
    return board

blocking_position = _make_blocking_position()

def _find_winning_cells(board):
    """Return (row, col) pairs for the 4 cells that form the winning connection."""
    other_player = board.current_player ^ board.mask
    rows = board.rows
    for direction in [rows + 1, 1, rows + 2, rows]:
        m      = other_player & (other_player >> direction)
        streak = m & (m >> (2 * direction))
        if streak:
            start = (streak & -streak).bit_length() - 1
            return [
                (bit % (rows + 1), bit // (rows + 1))
                for bit in (start + i * direction for i in range(4))
            ]
    return []


class BRoll(Scene):
    def construct(self):
        # 7-move game: Yellow plays cols 3,2,4,5; Red plays 0,1,6
        # Yellow wins horizontally at row 0, cols 2-5
        MOVES      = [3, 3, 2, 3, 3, 4, 0, 1, 1, 2, 2]
        CELL       = 0.7
        COLS, ROWS = 7, 6

        board = b()

        bg = RoundedRectangle(
            corner_radius=0.2,
            width=COLS * CELL + 0.5,
            height=ROWS * CELL + 0.5,
            fill_color="#1a3564",
            fill_opacity=1,
            stroke_color="#2a50a0",
            stroke_width=4,
        )

        cells = {}
        grid  = VGroup()
        for row in range(ROWS):
            for col in range(COLS):
                x = (col - (COLS - 1) / 2) * CELL
                y = (row - (ROWS - 1) / 2) * CELL
                hole = Circle(
                    radius=0.28,
                    fill_color="#0a1a3a",
                    fill_opacity=1,
                    stroke_color="#2255aa",
                    stroke_width=2,
                )
                hole.move_to([x, y, 0])
                cells[(row, col)] = hole
                grid.add(hole)

        self.play(FadeIn(bg), Create(grid, lag_ratio=0.05), run_time=1.2)
        self.wait(0.4)

        i = 1

        for col in MOVES:
            row   = board.heights[col] - col * (ROWS + 1)
            color = YELLOW if board.turn % 2 == 0 else RED

            target = cells[(row, col)].get_center()
            above  = np.array([target[0], bg.get_top()[1] + CELL * 0.8, 0])

            piece = Circle(
                radius=0.28,
                fill_color=color,
                fill_opacity=1,
                stroke_color=color,
                stroke_width=2,
            )
            piece.move_to(above)
            self.add(piece)

            fall_time = max(0.22, (above[1] - target[1]) / (ROWS * CELL) * 0.55)
            self.play(
                piece.animate.move_to(target),
                run_time=fall_time,
                rate_func=lambda t: t ** 2,
            )

            cells[(row, col)].set_fill(color, opacity=1).set_stroke(color, width=2)
            self.remove(piece)
            self.play(cells[(row, col)].animate.scale(1.12), run_time=0.07)
            self.play(cells[(row, col)].animate.scale(1 / 1.12), run_time=0.07)
            self.wait(0.1 - 0.005 * i)
            i += 1

            board.add_piece(col)

            if board.check_result():
                winners = _find_winning_cells(board)
                self.play(
                    *[cells[rc].animate.set_stroke(WHITE, width=5).scale(1.1)
                      for rc in winners],
                    run_time=0.4,
                )
                self.play(
                    *[Flash(cells[rc], color=WHITE, line_length=0.2, num_lines=8)
                      for rc in winners],
                    run_time=0.6,
                )
                self.wait(1.5)
                break

        self.wait(1)


# display_board(board) produces manim animation for a given board state
def display_board(board, location=ORIGIN):
    group = VGroup()
    for row in range(board.rows):
        for col in range(board.cols):
            bit = row + col * (board.rows + 1)
            if board.mask & (1 << bit):
                if board.current_player & (1 << bit):
                    player = board.turn % 2
                else:
                    player = (board.turn + 1) % 2
                if player == 1:
                    circle = Circle(radius=0.3, color=RED, fill_color=RED, fill_opacity=0.8)
                else:
                    circle = Circle(radius=0.3, color=YELLOW, fill_color=YELLOW, fill_opacity=0.8)
            else:
                circle = Circle(radius=0.3, color=WHITE)
            circle.move_to(RIGHT * col * 0.7 + DOWN * (board.rows - 1 - row) * 0.7)
            group.add(circle)
    group.move_to(location)
    return group
