"""Quantum scene generators — bloch_sphere, expectation_animation, energy_spectrum."""

from scenes import register_scene


@register_scene("bloch_sphere")
def generate_bloch_sphere_scene(params):
    """Generate a Manim ThreeDScene that renders a Bloch sphere with trajectory."""
    traj_x = params.get("trajectory_x", [0.0])
    traj_y = params.get("trajectory_y", [0.0])
    traj_z = params.get("trajectory_z", [1.0])

    # Downsample trajectory to max 100 points for rendering performance
    max_pts = 100
    if len(traj_x) > max_pts:
        step = len(traj_x) // max_pts
        traj_x = traj_x[::step][:max_pts]
        traj_y = traj_y[::step][:max_pts]
        traj_z = traj_z[::step][:max_pts]

    lines = [
        "from manim import *",
        "import numpy as np",
        "",
        "class GeneratedScene(ThreeDScene):",
        "    def construct(self):",
        "        self.set_camera_orientation(phi=70 * DEGREES, theta=30 * DEGREES)",
        "",
        "        # Draw wireframe Bloch sphere",
        "        sphere = Surface(",
        "            lambda u, v: np.array([",
        "                np.cos(u) * np.cos(v),",
        "                np.cos(u) * np.sin(v),",
        "                np.sin(u)",
        "            ]),",
        "            u_range=[-PI / 2, PI / 2],",
        "            v_range=[0, TAU],",
        "            resolution=(16, 32),",
        "            fill_opacity=0.05,",
        "            stroke_width=0.5,",
        "            stroke_color=BLUE_D,",
        "        )",
        "        self.add(sphere)",
        "",
        "        # Axes",
        "        axes_lines = VGroup(",
        "            Line3D(start=[-1.3, 0, 0], end=[1.3, 0, 0], color=RED_D),",
        "            Line3D(start=[0, -1.3, 0], end=[0, 1.3, 0], color=GREEN_D),",
        "            Line3D(start=[0, 0, -1.3], end=[0, 0, 1.3], color=BLUE_D),",
        "        )",
        "        self.add(axes_lines)",
        "",
        "        # Labels: poles and equator",
        "        label_0 = Tex(r'$|0\\rangle$', font_size=28).move_to([0, 0, 1.6])",
        "        label_1 = Tex(r'$|1\\rangle$', font_size=28).move_to([0, 0, -1.6])",
        "        label_plus = Tex(r'$|+\\rangle$', font_size=24).move_to([1.5, 0, 0])",
        "        label_minus = Tex(r'$|-\\rangle$', font_size=24).move_to([-1.5, 0, 0])",
        "        self.add_fixed_in_frame_mobjects(label_0, label_1, label_plus, label_minus)",
        "",
        "        # Trajectory points",
        f"        tx = {traj_x}",
        f"        ty = {traj_y}",
        f"        tz = {traj_z}",
        "",
        "        if len(tx) > 1:",
        "            points = [np.array([tx[i], ty[i], tz[i]]) for i in range(len(tx))]",
        "            path = VMobject(stroke_color=YELLOW, stroke_width=3)",
        "            path.set_points_smoothly(points)",
        "            self.play(Create(path), run_time=3)",
        "",
        "            # Mark start and end",
        "            start_dot = Dot3D(point=points[0], color=GREEN, radius=0.06)",
        "            end_dot = Dot3D(point=points[-1], color=RED, radius=0.06)",
        "            self.add(start_dot, end_dot)",
        "        else:",
        "            dot = Dot3D(point=[tx[0], ty[0], tz[0]], color=YELLOW, radius=0.08)",
        "            self.play(FadeIn(dot))",
        "",
        "        self.wait(2)",
    ]
    return "\n".join(lines)


@register_scene("expectation_animation")
def generate_expectation_animation_scene(params):
    """Animated expectation value time series from quantum simulation."""
    times = params.get("times", [0, 1, 2, 3, 4])
    expect_values = params.get("expect_values", {})
    labels = params.get("labels", [])
    title = params.get("title", "Expectation Values")

    colors = ["BLUE", "GREEN", "RED", "YELLOW", "PURPLE", "ORANGE"]

    # Build data lines
    data_lines = []
    plot_names = []
    for i, (key, values) in enumerate(expect_values.items()):
        label = labels[i] if i < len(labels) else key
        plot_names.append((f"graph{i}", label, colors[i % len(colors)]))
        data_lines.append(f"    data_{i} = {values}")

    t_min = min(times) if times else 0
    t_max = max(times) if times else 1
    if t_max == t_min:
        t_max = t_min + 1

    lines = [
        "from manim import *",
        "import numpy as np",
        "",
        "class GeneratedScene(Scene):",
        "    def construct(self):",
        f"        title = Text(\"{title}\", font_size=28, color=WHITE)",
        "        title.to_edge(UP)",
        "        self.play(Write(title))",
        "",
        f"        times = {times}",
    ]

    for dl in data_lines:
        lines.append(f"    {dl}")

    lines += [
        "",
        f"        axes = Axes(",
        f"            x_range=[{t_min}, {t_max}, {(t_max - t_min) / 5:.4f}],",
        "            y_range=[-1.1, 1.1, 0.5],",
        "            x_length=10, y_length=5,",
        "            axis_config={'color': WHITE},",
        "        ).shift(DOWN * 0.3)",
        "        x_label = axes.get_x_axis_label('t')",
        "        self.play(Create(axes), Write(x_label))",
        "",
    ]

    for i, (name, label, color) in enumerate(plot_names):
        lines += [
            f"        pts_{i} = [axes.c2p(times[j], data_{i}[j]) for j in range(len(times))]",
            f"        {name} = VMobject(stroke_color={color}, stroke_width=2.5)",
            f"        {name}.set_points_smoothly(pts_{i})",
            f"        lbl_{i} = Text(\"{label}\", font_size=18, color={color})",
            f"        lbl_{i}.next_to({name}, RIGHT)",
            f"        self.play(Create({name}), Write(lbl_{i}), run_time=2)",
        ]

    lines.append("        self.wait(2)")
    return "\n".join(lines)


@register_scene("energy_spectrum")
def generate_energy_spectrum_scene(params):
    """Energy level diagram with transitions."""
    energy_levels = params.get("energy_levels", [0, 1, 2, 3])
    level_labels = params.get("level_labels", [])
    transitions = params.get("transitions", [])
    title = params.get("title", "Energy Spectrum")

    lines = [
        "from manim import *",
        "import numpy as np",
        "",
        "class GeneratedScene(Scene):",
        "    def construct(self):",
        f"        title = Text(\"{title}\", font_size=28, color=WHITE)",
        "        title.to_edge(UP)",
        "        self.play(Write(title))",
        "",
        f"        levels = {energy_levels}",
        "        n = len(levels)",
        "        e_min, e_max = min(levels), max(levels)",
        "        span = e_max - e_min if e_max != e_min else 1",
        "",
        "        level_lines = VGroup()",
        "        level_texts = VGroup()",
        "        y_positions = []",
        "        for i, e in enumerate(levels):",
        "            y = -2.5 + 5.0 * (e - e_min) / span",
        "            y_positions.append(y)",
        "            line = Line(LEFT * 1.5, RIGHT * 1.5, color=BLUE).shift(UP * y)",
        "            level_lines.add(line)",
        f"            labels = {level_labels}",
        "            lbl = labels[i] if i < len(labels) else f'E={e:.2f}'",
        "            txt = Text(lbl, font_size=16, color=WHITE).next_to(line, RIGHT, buff=0.3)",
        "            level_texts.add(txt)",
        "",
        "        self.play(LaggedStart(*[Create(l) for l in level_lines], lag_ratio=0.2))",
        "        self.play(LaggedStart(*[Write(t) for t in level_texts], lag_ratio=0.1))",
        "",
    ]

    if transitions:
        lines += [
            f"        transitions = {transitions}",
            "        for t in transitions:",
            "            i_from, i_to = t[0], t[1]",
            "            color = RED if i_from > i_to else GREEN",
            "            arrow = Arrow(",
            "                start=RIGHT * 2.2 + UP * y_positions[i_from],",
            "                end=RIGHT * 2.2 + UP * y_positions[i_to],",
            "                color=color, buff=0.1, stroke_width=3,",
            "            )",
            "            self.play(GrowArrow(arrow), run_time=0.5)",
        ]

    lines.append("        self.wait(2)")
    return "\n".join(lines)
