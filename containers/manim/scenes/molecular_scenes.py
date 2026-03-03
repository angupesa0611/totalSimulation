"""Molecular dynamics scene generators — trajectory, energy evolution, contact map."""

from scenes import register_scene


@register_scene("molecular_trajectory")
def generate_molecular_trajectory_scene(params):
    """Animated atom positions from MD frames (2D projection)."""
    frames = params.get("frames", [])  # list of [{x,y,z,element}, ...]
    title = params.get("title", "Molecular Trajectory")
    n_display = params.get("n_display_frames", 10)

    # Downsample frames
    if len(frames) > n_display:
        step = len(frames) // n_display
        frames = frames[::step][:n_display]

    lines = [
        "from manim import *",
        "import numpy as np",
        "",
        "class GeneratedScene(Scene):",
        "    def construct(self):",
        f"        title = Text(\"{title}\", font_size=24, color=WHITE).to_edge(UP)",
        "        self.add(title)",
        "",
        f"        frames = {frames}",
        "        if not frames:",
        "            msg = Text('No trajectory data', font_size=20, color=GREY)",
        "            self.play(Write(msg))",
        "            self.wait(2)",
        "            return",
        "",
        "        # Scale coordinates to fit scene",
        "        all_x = [a.get('x', 0) for f in frames for a in f]",
        "        all_y = [a.get('y', 0) for f in frames for a in f]",
        "        cx = (min(all_x) + max(all_x)) / 2 if all_x else 0",
        "        cy = (min(all_y) + max(all_y)) / 2 if all_y else 0",
        "        span = max(max(all_x) - min(all_x), max(all_y) - min(all_y), 1e-10)",
        "        scale = 8.0 / span",
        "",
        "        _color_map = {'C': GREY, 'N': BLUE, 'O': RED, 'H': WHITE,",
        "                      'S': YELLOW, 'P': ORANGE, 'CA': GREEN}",
        "",
        "        prev_atoms = VGroup()",
        "        frame_lbl = Text('', font_size=16, color=GREY).to_edge(DOWN)",
        "        self.add(frame_lbl)",
        "",
        "        for fi, frame in enumerate(frames):",
        "            new_atoms = VGroup()",
        "            for atom in frame:",
        "                x = (atom.get('x', 0) - cx) * scale",
        "                y = (atom.get('y', 0) - cy) * scale",
        "                elem = atom.get('element', 'C').upper()",
        "                color = _color_map.get(elem, GREY)",
        "                dot = Dot(point=[x, y, 0], color=color, radius=0.06)",
        "                new_atoms.add(dot)",
        "            new_lbl = Text(f'Frame {fi+1}/{len(frames)}', font_size=16, color=GREY).to_edge(DOWN)",
        "            if fi == 0:",
        "                self.play(FadeIn(new_atoms), Transform(frame_lbl, new_lbl), run_time=0.5)",
        "            else:",
        "                self.play(FadeOut(prev_atoms), FadeIn(new_atoms), Transform(frame_lbl, new_lbl), run_time=0.3)",
        "            prev_atoms = new_atoms",
        "            self.wait(0.3)",
        "",
        "        self.wait(1)",
    ]
    return "\n".join(lines)


@register_scene("energy_evolution")
def generate_energy_evolution_scene(params):
    """Animated energy (KE+PE+Total) over time."""
    times = params.get("times", [])
    kinetic = params.get("kinetic_energy", [])
    potential = params.get("potential_energy", [])
    total = params.get("total_energy", [])
    title = params.get("title", "Energy Evolution")

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
        f"        ke = {kinetic[:200]}",
        f"        pe = {potential[:200]}",
        f"        total = {total[:200]}",
        "",
        "        all_e = ke + pe + total",
        "        t_min, t_max = (min(times), max(times)) if times else (0, 1)",
        "        e_min = min(all_e) if all_e else -1",
        "        e_max = max(all_e) if all_e else 1",
        "        margin = (e_max - e_min) * 0.1 + 1e-10",
        "",
        "        axes = Axes(",
        "            x_range=[t_min, t_max, (t_max - t_min) / 5],",
        "            y_range=[e_min - margin, e_max + margin, (e_max - e_min + 2*margin) / 4],",
        "            x_length=10, y_length=5,",
        "            axis_config={'color': WHITE},",
        "        ).shift(DOWN * 0.3)",
        "        x_lbl = axes.get_x_axis_label('Time')",
        "        y_lbl = axes.get_y_axis_label('Energy')",
        "        self.play(Create(axes), Write(x_lbl), Write(y_lbl))",
        "",
        "        datasets = [",
        "            (ke, 'KE', RED),",
        "            (pe, 'PE', BLUE),",
        "            (total, 'Total', GREEN),",
        "        ]",
        "        for data, label, color in datasets:",
        "            if not data:",
        "                continue",
        "            pts = [axes.c2p(times[i], data[i]) for i in range(min(len(times), len(data)))]",
        "            curve = VMobject(stroke_color=color, stroke_width=2)",
        "            curve.set_points_smoothly(pts)",
        "            lbl = Text(label, font_size=16, color=color).next_to(curve, RIGHT)",
        "            self.play(Create(curve), Write(lbl), run_time=2)",
        "",
        "        self.wait(2)",
    ]
    return "\n".join(lines)


@register_scene("contact_map_animation")
def generate_contact_map_animation_scene(params):
    """Animated residue-residue contact map from MD analysis."""
    contact_matrices = params.get("contact_matrices", [])
    title = params.get("title", "Contact Map")

    n_frames = min(len(contact_matrices), 10)

    lines = [
        "from manim import *",
        "import numpy as np",
        "",
        "class GeneratedScene(Scene):",
        "    def construct(self):",
        f"        title = Text(\"{title}\", font_size=28, color=WHITE).to_edge(UP)",
        "        self.play(Write(title))",
        "",
        f"        matrices = {contact_matrices[:n_frames]}",
        "        if not matrices:",
        "            msg = Text('No contact data', font_size=20, color=GREY)",
        "            self.play(Write(msg))",
        "            self.wait(2)",
        "            return",
        "",
        "        n = len(matrices[0])",
        "        cell_size = min(6.0 / n, 0.4)",
        "        offset = n * cell_size / 2",
        "",
        "        frame_lbl = Text('', font_size=14, color=GREY).to_edge(DOWN)",
        "        self.add(frame_lbl)",
        "        prev_grid = None",
        "",
        "        for fi, mat in enumerate(matrices):",
        "            grid = VGroup()",
        "            for i in range(n):",
        "                for j in range(n):",
        "                    val = mat[i][j] if i < len(mat) and j < len(mat[i]) else 0",
        "                    opacity = min(abs(val), 1.0)",
        "                    sq = Square(side_length=cell_size, fill_color=BLUE, fill_opacity=opacity,",
        "                               stroke_width=0.2, stroke_color=GREY)",
        "                    sq.move_to([j * cell_size - offset, -i * cell_size + offset, 0])",
        "                    grid.add(sq)",
        "            new_lbl = Text(f'Frame {fi+1}/{len(matrices)}', font_size=14, color=GREY).to_edge(DOWN)",
        "            if prev_grid is None:",
        "                self.play(FadeIn(grid), Transform(frame_lbl, new_lbl), run_time=1)",
        "            else:",
        "                self.play(FadeOut(prev_grid), FadeIn(grid), Transform(frame_lbl, new_lbl), run_time=0.5)",
        "            prev_grid = grid",
        "            self.wait(0.5)",
        "",
        "        self.wait(1)",
    ]
    return "\n".join(lines)
