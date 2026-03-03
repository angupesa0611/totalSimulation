"""Continuum mechanics scene generators — field heatmap, streamline, mesh deformation."""

from scenes import register_scene


@register_scene("field_heatmap_animation")
def generate_field_heatmap_animation_scene(params):
    """Animated 2D field heatmap (temperature, stress, etc.)."""
    frames = params.get("frames", [])  # list of 2D arrays
    title = params.get("title", "Field Evolution")
    field_name = params.get("field_name", "u")
    n_display = params.get("n_display_frames", 8)

    if len(frames) > n_display:
        step = len(frames) // n_display
        frames = frames[::step][:n_display]

    lines = [
        "from manim import *",
        "import numpy as np",
        "",
        "class GeneratedScene(Scene):",
        "    def construct(self):",
        f"        title = Text(\"{title}\", font_size=28, color=WHITE).to_edge(UP)",
        "        self.play(Write(title))",
        "",
        f"        frames = {frames}",
        "        if not frames:",
        "            msg = Text('No field data', font_size=20, color=GREY)",
        "            self.play(Write(msg))",
        "            self.wait(2)",
        "            return",
        "",
        "        # Find global min/max",
        "        global_min = min(min(row) for frame in frames for row in frame)",
        "        global_max = max(max(row) for frame in frames for row in frame)",
        "        val_range = global_max - global_min if global_max != global_min else 1",
        "",
        "        ny = len(frames[0])",
        "        nx = len(frames[0][0]) if ny > 0 else 0",
        "        cell_w = min(8.0 / max(nx, 1), 0.5)",
        "        cell_h = min(5.0 / max(ny, 1), 0.5)",
        "        x_off = nx * cell_w / 2",
        "        y_off = ny * cell_h / 2",
        "",
        "        frame_lbl = Text('', font_size=14, color=GREY).to_edge(DOWN)",
        "        self.add(frame_lbl)",
        "        prev_grid = None",
        "",
        "        for fi, field in enumerate(frames):",
        "            grid = VGroup()",
        "            for i in range(ny):",
        "                for j in range(nx):",
        "                    val = field[i][j]",
        "                    t = (val - global_min) / val_range",
        "                    # Blue (cold) -> Red (hot) interpolation",
        "                    r_c = interpolate_color(BLUE, RED, t)",
        "                    sq = Square(side_length=min(cell_w, cell_h),",
        "                               fill_color=r_c, fill_opacity=0.9,",
        "                               stroke_width=0)",
        "                    sq.move_to([j * cell_w - x_off, -i * cell_h + y_off, 0])",
        "                    grid.add(sq)",
        "            new_lbl = Text(f'Step {fi+1}/{len(frames)}', font_size=14, color=GREY).to_edge(DOWN)",
        "            if prev_grid is None:",
        "                self.play(FadeIn(grid), Transform(frame_lbl, new_lbl), run_time=1)",
        "            else:",
        "                self.play(ReplacementTransform(prev_grid, grid), Transform(frame_lbl, new_lbl), run_time=0.6)",
        "            prev_grid = grid",
        "            self.wait(0.3)",
        "",
        "        self.wait(1)",
    ]
    return "\n".join(lines)


@register_scene("streamline_flow")
def generate_streamline_flow_scene(params):
    """Animated streamlines for velocity fields."""
    velocity_field = params.get("velocity_field", None)
    title = params.get("title", "Flow Streamlines")
    n_lines = params.get("n_streamlines", 12)

    lines = [
        "from manim import *",
        "import numpy as np",
        "",
        "class GeneratedScene(Scene):",
        "    def construct(self):",
        f"        title = Text(\"{title}\", font_size=28, color=WHITE).to_edge(UP)",
        "        self.play(Write(title))",
        "",
    ]

    if velocity_field and "vx" in velocity_field and "vy" in velocity_field:
        vx = velocity_field["vx"]
        vy = velocity_field["vy"]
        lines += [
            f"        vx_data = {vx}",
            f"        vy_data = {vy}",
            "        ny = len(vx_data)",
            "        nx = len(vx_data[0]) if ny > 0 else 0",
            "",
            "        def vel_func(pos):",
            "            x, y = pos[0], pos[1]",
            "            # Map position to grid indices",
            "            ix = int((x + 5) / 10 * (nx - 1))",
            "            iy = int((y + 3) / 6 * (ny - 1))",
            "            ix = max(0, min(ix, nx - 1))",
            "            iy = max(0, min(iy, ny - 1))",
            "            return np.array([vx_data[iy][ix], vy_data[iy][ix], 0])",
            "",
            "        stream = StreamLines(",
            "            vel_func,",
            "            x_range=[-5, 5, 0.5],",
            "            y_range=[-3, 3, 0.5],",
            "            stroke_width=1.5,",
            "            color=BLUE,",
            "        )",
            "        self.play(stream.create(), run_time=4)",
        ]
    else:
        # Default swirl field for demonstration
        lines += [
            "        def vel_func(pos):",
            "            x, y = pos[0], pos[1]",
            "            return np.array([-y, x, 0]) * 0.5",
            "",
            "        stream = StreamLines(",
            "            vel_func,",
            "            x_range=[-4, 4, 0.5],",
            "            y_range=[-3, 3, 0.5],",
            "            stroke_width=1.5,",
            "            color=BLUE,",
            "        )",
            "        self.play(stream.create(), run_time=4)",
        ]

    lines.append("        self.wait(2)")
    return "\n".join(lines)


@register_scene("mesh_deformation")
def generate_mesh_deformation_scene(params):
    """Animated mesh stretching/deforming from FEM simulation."""
    nodes_initial = params.get("nodes_initial", [])  # [[x,y], ...]
    nodes_deformed = params.get("nodes_deformed", [])
    elements = params.get("elements", [])  # [[n1, n2, n3], ...] triangles
    title = params.get("title", "Mesh Deformation")
    scale = params.get("scale_factor", 3.0)

    lines = [
        "from manim import *",
        "import numpy as np",
        "",
        "class GeneratedScene(Scene):",
        "    def construct(self):",
        f"        title = Text(\"{title}\", font_size=28, color=WHITE).to_edge(UP)",
        "        self.play(Write(title))",
        "",
        f"        nodes_i = {nodes_initial}",
        f"        nodes_d = {nodes_deformed}",
        f"        elements = {elements}",
        f"        scale = {scale}",
        "",
        "        if not nodes_i or not elements:",
        "            msg = Text('No mesh data', font_size=20, color=GREY)",
        "            self.play(Write(msg))",
        "            self.wait(2)",
        "            return",
        "",
        "        # Center and scale",
        "        xs = [n[0] for n in nodes_i]",
        "        ys = [n[1] for n in nodes_i]",
        "        cx = (min(xs) + max(xs)) / 2",
        "        cy = (min(ys) + max(ys)) / 2",
        "        span = max(max(xs) - min(xs), max(ys) - min(ys), 1e-10)",
        "        s = scale / span",
        "",
        "        # Draw initial mesh",
        "        initial_mesh = VGroup()",
        "        for tri in elements:",
        "            if len(tri) >= 3:",
        "                pts = []",
        "                for ni in tri:",
        "                    if ni < len(nodes_i):",
        "                        pts.append([(nodes_i[ni][0] - cx) * s, (nodes_i[ni][1] - cy) * s, 0])",
        "                if len(pts) >= 3:",
        "                    polygon = Polygon(*[np.array(p) for p in pts],",
        "                                     stroke_color=BLUE, stroke_width=1.5, fill_opacity=0.1, fill_color=BLUE)",
        "                    initial_mesh.add(polygon)",
        "",
        "        self.play(Create(initial_mesh), run_time=2)",
        "",
        "        # Animate deformation",
        "        if nodes_d:",
        "            deformed_mesh = VGroup()",
        "            for tri in elements:",
        "                if len(tri) >= 3:",
        "                    pts = []",
        "                    for ni in tri:",
        "                        if ni < len(nodes_d):",
        "                            pts.append([(nodes_d[ni][0] - cx) * s, (nodes_d[ni][1] - cy) * s, 0])",
        "                    if len(pts) >= 3:",
        "                        polygon = Polygon(*[np.array(p) for p in pts],",
        "                                         stroke_color=RED, stroke_width=1.5, fill_opacity=0.1, fill_color=RED)",
        "                        deformed_mesh.add(polygon)",
        "            self.play(ReplacementTransform(initial_mesh, deformed_mesh), run_time=3)",
        "",
        "        self.wait(2)",
    ]
    return "\n".join(lines)
