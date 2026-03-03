"""Physics scene generators — rigid body, mechanism animation."""

from scenes import register_scene


@register_scene("rigid_body_animation")
def generate_rigid_body_animation_scene(params):
    """Animated bodies with collision events from physics simulation."""
    bodies = params.get("bodies", [])  # [{name, positions: [[x,y],...], shape, size}]
    collisions = params.get("collisions", [])  # [{time_idx, body1, body2}]
    title = params.get("title", "Rigid Body Simulation")
    n_frames = params.get("n_frames", 30)

    lines = [
        "from manim import *",
        "import numpy as np",
        "",
        "class GeneratedScene(Scene):",
        "    def construct(self):",
        f"        title = Text(\"{title}\", font_size=28, color=WHITE).to_edge(UP)",
        "        self.play(Write(title))",
        "",
        f"        bodies = {bodies}",
        "        if not bodies:",
        "            msg = Text('No body data', font_size=20, color=GREY)",
        "            self.play(Write(msg))",
        "            self.wait(2)",
        "            return",
        "",
        "        colors = [BLUE, RED, GREEN, YELLOW, PURPLE, ORANGE, TEAL]",
        "",
        "        # Find scale",
        "        all_x = [p[0] for b in bodies for p in b.get('positions', [[0,0]])]",
        "        all_y = [p[1] for b in bodies for p in b.get('positions', [[0,0]])]",
        "        cx = (min(all_x) + max(all_x)) / 2",
        "        cy = (min(all_y) + max(all_y)) / 2",
        "        span = max(max(all_x) - min(all_x), max(all_y) - min(all_y), 1e-10)",
        "        scale = 8.0 / span",
        "",
        f"        n_frames = min({n_frames}, min(len(b.get('positions', [])) for b in bodies) if bodies else 1)",
        "",
        "        # Create initial body shapes",
        "        shapes = []",
        "        for i, body in enumerate(bodies):",
        "            pos = body.get('positions', [[0, 0]])",
        "            size = body.get('size', 0.3) * scale",
        "            shape_type = body.get('shape', 'circle')",
        "            color = colors[i % len(colors)]",
        "            x = (pos[0][0] - cx) * scale",
        "            y = (pos[0][1] - cy) * scale",
        "            if shape_type == 'square':",
        "                s = Square(side_length=size, color=color, fill_opacity=0.6)",
        "            else:",
        "                s = Circle(radius=size / 2, color=color, fill_opacity=0.6)",
        "            s.move_to([x, y, 0])",
        "            shapes.append(s)",
        "            self.play(FadeIn(s), run_time=0.2)",
        "",
        "        # Animate frames",
        "        for fi in range(1, n_frames):",
        "            anims = []",
        "            for i, body in enumerate(bodies):",
        "                pos = body.get('positions', [[0, 0]])",
        "                if fi < len(pos):",
        "                    x = (pos[fi][0] - cx) * scale",
        "                    y = (pos[fi][1] - cy) * scale",
        "                    anims.append(shapes[i].animate.move_to([x, y, 0]))",
        "            if anims:",
        "                self.play(*anims, run_time=0.15)",
        "",
        "        self.wait(2)",
    ]
    return "\n".join(lines)


@register_scene("mechanism_animation")
def generate_mechanism_animation_scene(params):
    """Joint-link mechanism visualization."""
    joints = params.get("joints", [])  # [{x, y, fixed}]
    links = params.get("links", [])  # [[joint_i, joint_j]]
    motion_frames = params.get("motion_frames", [])  # list of [{x,y}] per joint per frame
    title = params.get("title", "Mechanism Animation")

    lines = [
        "from manim import *",
        "import numpy as np",
        "",
        "class GeneratedScene(Scene):",
        "    def construct(self):",
        f"        title = Text(\"{title}\", font_size=28, color=WHITE).to_edge(UP)",
        "        self.play(Write(title))",
        "",
        f"        joints = {joints}",
        f"        links = {links}",
        f"        motion = {motion_frames[:50]}",
        "",
        "        if not joints:",
        "            msg = Text('No mechanism data', font_size=20, color=GREY)",
        "            self.play(Write(msg))",
        "            self.wait(2)",
        "            return",
        "",
        "        scale = 2.0",
        "",
        "        # Draw initial state",
        "        joint_dots = []",
        "        for j in joints:",
        "            color = RED if j.get('fixed', False) else BLUE",
        "            dot = Dot([j['x'] * scale, j['y'] * scale, 0], color=color, radius=0.1)",
        "            joint_dots.append(dot)",
        "            self.play(FadeIn(dot), run_time=0.1)",
        "",
        "        link_lines = []",
        "        for lk in links:",
        "            if len(lk) >= 2 and lk[0] < len(joints) and lk[1] < len(joints):",
        "                j1 = joints[lk[0]]",
        "                j2 = joints[lk[1]]",
        "                line = Line(",
        "                    [j1['x'] * scale, j1['y'] * scale, 0],",
        "                    [j2['x'] * scale, j2['y'] * scale, 0],",
        "                    color=WHITE, stroke_width=4)",
        "                link_lines.append((lk, line))",
        "                self.play(Create(line), run_time=0.2)",
        "",
        "        # Animate motion",
        "        for frame in motion:",
        "            anims = []",
        "            for i, pos in enumerate(frame):",
        "                if i < len(joint_dots):",
        "                    new_pos = [pos['x'] * scale, pos['y'] * scale, 0]",
        "                    anims.append(joint_dots[i].animate.move_to(new_pos))",
        "            for lk, line in link_lines:",
        "                if lk[0] < len(frame) and lk[1] < len(frame):",
        "                    p1 = frame[lk[0]]",
        "                    p2 = frame[lk[1]]",
        "                    new_line = Line(",
        "                        [p1['x'] * scale, p1['y'] * scale, 0],",
        "                        [p2['x'] * scale, p2['y'] * scale, 0],",
        "                        color=WHITE, stroke_width=4)",
        "                    anims.append(Transform(line, new_line))",
        "            if anims:",
        "                self.play(*anims, run_time=0.1)",
        "",
        "        self.wait(2)",
    ]
    return "\n".join(lines)
