"""Astrophysics/GR scene generators — orbital, precession, geodesic, gravitational wave."""

from scenes import register_scene


@register_scene("orbital_animation")
def generate_orbital_animation_scene(params):
    """2D/3D orbit trails with planet markers from N-body simulation."""
    positions = params.get("positions", {})  # {name: [[x,y,z], ...]}
    names = params.get("names", list(positions.keys()))
    n_frames = params.get("n_frames", 100)
    title = params.get("title", "Orbital Animation")
    mode_3d = params.get("mode_3d", False)

    colors = ["YELLOW", "BLUE", "RED", "GREEN", "ORANGE", "PURPLE", "TEAL", "PINK", "WHITE"]
    base_class = "ThreeDScene" if mode_3d else "Scene"

    lines = [
        "from manim import *",
        "import numpy as np",
        "",
        f"class GeneratedScene({base_class}):",
        "    def construct(self):",
    ]

    if mode_3d:
        lines.append("        self.set_camera_orientation(phi=60 * DEGREES, theta=30 * DEGREES)")

    lines += [
        f"        title = Text(\"{title}\", font_size=24, color=WHITE).to_edge(UP)",
        "        self.add(title)",
        "",
    ]

    # Embed position data
    for i, name in enumerate(names):
        pos_data = positions.get(name, [[0, 0, 0]])
        # Downsample to n_frames
        if len(pos_data) > n_frames:
            step = len(pos_data) // n_frames
            pos_data = pos_data[::step][:n_frames]
        lines.append(f"        pos_{i} = {pos_data}")

    lines.append("")

    # Scale factor to fit scene
    lines += [
        "        all_pts = []",
    ]
    for i in range(len(names)):
        lines.append(f"        all_pts.extend(pos_{i})")
    lines += [
        "        if all_pts:",
        "            xs = [p[0] for p in all_pts]",
        "            ys = [p[1] for p in all_pts]",
        "            max_r = max(max(abs(min(xs)), abs(max(xs))), max(abs(min(ys)), abs(max(ys))), 1e-10)",
        "            scale = 5.0 / max_r",
        "        else:",
        "            scale = 1.0",
        "",
    ]

    # Draw orbit trails and animate
    for i, name in enumerate(names):
        color = colors[i % len(colors)]
        lines += [
            f"        pts_{i} = [np.array([p[0]*scale, p[1]*scale, 0]) for p in pos_{i}]",
            f"        if len(pts_{i}) > 1:",
            f"            trail_{i} = VMobject(stroke_color={color}, stroke_width=1.5, stroke_opacity=0.6)",
            f"            trail_{i}.set_points_smoothly(pts_{i})",
            f"            self.play(Create(trail_{i}), run_time=2)",
            f"        dot_{i} = Dot(point=pts_{i}[-1] if pts_{i} else ORIGIN, color={color}, radius=0.08)",
            f"        lbl_{i} = Text(\"{name}\", font_size=14, color={color}).next_to(dot_{i}, UR, buff=0.1)",
            f"        self.play(FadeIn(dot_{i}), Write(lbl_{i}), run_time=0.3)",
        ]

    lines.append("        self.wait(2)")
    return "\n".join(lines)


@register_scene("precession_diagram")
def generate_precession_diagram_scene(params):
    """Precessing ellipse with arcsec annotation for GR precession."""
    semi_major = params.get("semi_major", 1.0)
    eccentricity = params.get("eccentricity", 0.2)
    precession_arcsec = params.get("total_precession_arcsec", 43.0)
    n_orbits = params.get("n_orbits", 5)
    title = params.get("title", "Orbital Precession")

    lines = [
        "from manim import *",
        "import numpy as np",
        "",
        "class GeneratedScene(Scene):",
        "    def construct(self):",
        f"        title = Text(\"{title}\", font_size=28, color=WHITE).to_edge(UP)",
        "        self.play(Write(title))",
        "",
        f"        a = {semi_major}",
        f"        e = {eccentricity}",
        f"        total_prec = {precession_arcsec}",
        f"        n_orbits = {n_orbits}",
        "        b = a * np.sqrt(1 - e**2)",
        "        scale = 3.0 / a",
        "        prec_per_orbit = np.radians(total_prec / 3600) * 50  # exaggerated for visibility",
        "",
        "        ellipses = VGroup()",
        "        for k in range(n_orbits):",
        "            angle = k * prec_per_orbit",
        "            ell = Ellipse(width=2*a*scale, height=2*b*scale, color=BLUE)",
        "            ell.set_stroke(opacity=0.3 + 0.7 * k / max(n_orbits - 1, 1))",
        "            ell.rotate(angle)",
        "            ellipses.add(ell)",
        "",
        "        self.play(LaggedStart(*[Create(e) for e in ellipses], lag_ratio=0.3), run_time=3)",
        "",
        "        # Focus dot",
        "        focus = Dot(ORIGIN, color=YELLOW, radius=0.1)",
        "        self.play(FadeIn(focus))",
        "",
        f"        ann = Text(f\"{total_prec:.2f} arcsec/century\", font_size=20, color=YELLOW)",
        "        ann.to_edge(DOWN)",
        "        self.play(Write(ann))",
        "        self.wait(2)",
    ]
    return "\n".join(lines)


@register_scene("geodesic_visualization")
def generate_geodesic_visualization_scene(params):
    """Geodesic paths on spacetime embedding diagram."""
    trajectories = params.get("trajectories", [])
    metric_name = params.get("metric_name", "Schwarzschild")
    title = params.get("title", f"Geodesics — {metric_name}")

    lines = [
        "from manim import *",
        "import numpy as np",
        "",
        "class GeneratedScene(ThreeDScene):",
        "    def construct(self):",
        "        self.set_camera_orientation(phi=65 * DEGREES, theta=30 * DEGREES)",
        f"        title = Text(\"{title}\", font_size=24, color=WHITE).to_edge(UP)",
        "        self.add_fixed_in_frame_mobjects(title)",
        "",
        "        # Embedding surface (funnel for Schwarzschild)",
        "        surface = Surface(",
        "            lambda u, v: np.array([",
        "                u * np.cos(v),",
        "                u * np.sin(v),",
        "                -2 * np.sqrt(max(u - 0.5, 0.001))",
        "            ]),",
        "            u_range=[0.5, 3],",
        "            v_range=[0, TAU],",
        "            resolution=(24, 48),",
        "            fill_opacity=0.15,",
        "            stroke_width=0.3,",
        "            stroke_color=BLUE_D,",
        "        )",
        "        self.play(Create(surface), run_time=2)",
        "",
    ]

    colors = ["YELLOW", "RED", "GREEN", "ORANGE"]
    trajectories_data = trajectories if trajectories else [
        [[1.5, 0, 0], [1.2, 0.5, 0], [1.0, 1.0, 0], [0.8, 1.3, 0]]
    ]

    for i, traj in enumerate(trajectories_data):
        color = colors[i % len(colors)]
        # Map trajectory points onto the embedding
        lines += [
            f"        traj_{i} = {traj}",
            f"        pts_{i} = []",
            f"        for p in traj_{i}:",
            f"            r = np.sqrt(p[0]**2 + p[1]**2)",
            f"            r = max(r, 0.51)",
            f"            z = -2 * np.sqrt(r - 0.5)",
            f"            pts_{i}.append(np.array([p[0], p[1], z]))",
            f"        if len(pts_{i}) > 1:",
            f"            path_{i} = VMobject(stroke_color={color}, stroke_width=3)",
            f"            path_{i}.set_points_smoothly(pts_{i})",
            f"            self.play(Create(path_{i}), run_time=2)",
        ]

    lines.append("        self.wait(2)")
    return "\n".join(lines)


@register_scene("gravitational_wave_strain")
def generate_gravitational_wave_strain_scene(params):
    """Animated h+/hx strain waveform from numerical relativity."""
    times = params.get("times", [])
    h_plus = params.get("h_plus", [])
    h_cross = params.get("h_cross", [])
    title = params.get("title", "Gravitational Wave Strain")

    # Generate sample data if empty
    if not times:
        times = [i * 0.1 for i in range(100)]
        h_plus = [0.5 * __import__('math').sin(0.5 * t) * __import__('math').exp(-0.02 * t) for t in times]
        h_cross = [0.5 * __import__('math').cos(0.5 * t) * __import__('math').exp(-0.02 * t) for t in times]

    lines = [
        "from manim import *",
        "import numpy as np",
        "",
        "class GeneratedScene(Scene):",
        "    def construct(self):",
        f"        title = Text(\"{title}\", font_size=28, color=WHITE).to_edge(UP)",
        "        self.play(Write(title))",
        "",
        f"        times = {times[:200]}",
        f"        h_plus = {h_plus[:200]}",
        f"        h_cross = {h_cross[:200]}",
        "",
        "        t_min, t_max = min(times), max(times)",
        "        all_h = h_plus + h_cross",
        "        h_min, h_max = min(all_h) if all_h else -1, max(all_h) if all_h else 1",
        "        margin = (h_max - h_min) * 0.1 + 1e-10",
        "",
        "        axes = Axes(",
        "            x_range=[t_min, t_max, (t_max - t_min) / 5],",
        "            y_range=[h_min - margin, h_max + margin, (h_max - h_min + 2*margin) / 4],",
        "            x_length=10, y_length=4,",
        "            axis_config={'color': WHITE},",
        "        ).shift(DOWN * 0.5)",
        "        x_lbl = axes.get_x_axis_label('t [s]')",
        "        y_lbl = axes.get_y_axis_label('h')",
        "        self.play(Create(axes), Write(x_lbl), Write(y_lbl))",
        "",
        "        # h+ curve",
        "        pts_p = [axes.c2p(times[i], h_plus[i]) for i in range(len(times))]",
        "        curve_p = VMobject(stroke_color=BLUE, stroke_width=2.5)",
        "        curve_p.set_points_smoothly(pts_p)",
        "        lbl_p = Text('h+', font_size=18, color=BLUE).next_to(curve_p, RIGHT)",
        "        self.play(Create(curve_p), Write(lbl_p), run_time=3)",
        "",
        "        # hx curve",
        "        pts_x = [axes.c2p(times[i], h_cross[i]) for i in range(len(times))]",
        "        curve_x = VMobject(stroke_color=RED, stroke_width=2.5)",
        "        curve_x.set_points_smoothly(pts_x)",
        "        lbl_x = Text('hx', font_size=18, color=RED).next_to(curve_x, RIGHT)",
        "        self.play(Create(curve_x), Write(lbl_x), run_time=3)",
        "",
        "        self.wait(2)",
    ]
    return "\n".join(lines)
