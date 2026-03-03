"""Chemistry scene generators — molecule structure, ignition, flame, descriptor radar, SAPT."""

from scenes import register_scene


@register_scene("molecule_structure_2d")
def generate_molecule_structure_2d_scene(params):
    """2D molecular structure drawing with atoms and bonds."""
    atoms = params.get("atoms", [])  # [{element, x, y}]
    bonds = params.get("bonds", [])  # [[atom_i, atom_j, order]]
    title = params.get("title", "Molecular Structure")

    atom_colors = {
        "C": "GREY", "N": "BLUE", "O": "RED", "H": "WHITE",
        "S": "YELLOW", "P": "ORANGE", "F": "GREEN", "CL": "GREEN",
        "BR": "MAROON", "I": "PURPLE",
    }

    lines = [
        "from manim import *",
        "import numpy as np",
        "",
        "class GeneratedScene(Scene):",
        "    def construct(self):",
        f"        title = Text(\"{title}\", font_size=28, color=WHITE).to_edge(UP)",
        "        self.play(Write(title))",
        "",
        f"        atoms = {atoms}",
        f"        bonds = {bonds}",
        "",
        "        if not atoms:",
        "            msg = Text('No structure data', font_size=20, color=GREY)",
        "            self.play(Write(msg))",
        "            self.wait(2)",
        "            return",
        "",
        "        # Scale and center",
        "        xs = [a['x'] for a in atoms]",
        "        ys = [a['y'] for a in atoms]",
        "        cx = (min(xs) + max(xs)) / 2",
        "        cy = (min(ys) + max(ys)) / 2",
        "        span = max(max(xs) - min(xs), max(ys) - min(ys), 1e-10)",
        "        scale = 6.0 / span",
        "",
        f"        color_map = {atom_colors}",
        "        manim_colors = {{'GREY': GREY, 'BLUE': BLUE, 'RED': RED, 'WHITE': WHITE,",
        "                        'YELLOW': YELLOW, 'ORANGE': ORANGE, 'GREEN': GREEN,",
        "                        'MAROON': MAROON, 'PURPLE': PURPLE}}",
        "",
        "        # Draw bonds first",
        "        bond_group = VGroup()",
        "        for bond in bonds:",
        "            i, j = bond[0], bond[1]",
        "            order = bond[2] if len(bond) > 2 else 1",
        "            if i < len(atoms) and j < len(atoms):",
        "                p1 = np.array([(atoms[i]['x'] - cx) * scale, (atoms[i]['y'] - cy) * scale, 0])",
        "                p2 = np.array([(atoms[j]['x'] - cx) * scale, (atoms[j]['y'] - cy) * scale, 0])",
        "                if order == 1:",
        "                    bond_group.add(Line(p1, p2, color=GREY_B, stroke_width=3))",
        "                elif order == 2:",
        "                    perp = np.array([-(p2-p1)[1], (p2-p1)[0], 0])",
        "                    perp = perp / (np.linalg.norm(perp) + 1e-10) * 0.08",
        "                    bond_group.add(Line(p1+perp, p2+perp, color=GREY_B, stroke_width=2.5))",
        "                    bond_group.add(Line(p1-perp, p2-perp, color=GREY_B, stroke_width=2.5))",
        "                else:",
        "                    bond_group.add(Line(p1, p2, color=GREY_B, stroke_width=3))",
        "        self.play(Create(bond_group), run_time=1.5)",
        "",
        "        # Draw atoms",
        "        atom_group = VGroup()",
        "        for a in atoms:",
        "            x = (a['x'] - cx) * scale",
        "            y = (a['y'] - cy) * scale",
        "            elem = a.get('element', 'C').upper()",
        "            c_name = color_map.get(elem, 'GREY')",
        "            color = manim_colors.get(c_name, GREY)",
        "            dot = Dot([x, y, 0], color=color, radius=0.12)",
        "            lbl = Text(elem, font_size=12, color=WHITE).move_to([x, y, 0])",
        "            atom_group.add(VGroup(dot, lbl))",
        "        self.play(FadeIn(atom_group), run_time=1)",
        "",
        "        self.wait(2)",
    ]
    return "\n".join(lines)


@register_scene("ignition_animation")
def generate_ignition_animation_scene(params):
    """Temperature spike + species evolution from combustion simulation."""
    times = params.get("times", [])
    temperature = params.get("temperature", [])
    species = params.get("species", {})  # {name: [values]}
    title = params.get("title", "Ignition Delay")

    colors = ["RED", "BLUE", "GREEN", "YELLOW", "PURPLE", "ORANGE"]

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
        f"        temp = {temperature[:200]}",
        "",
        "        if not times or not temp:",
        "            msg = Text('No ignition data', font_size=20, color=GREY)",
        "            self.play(Write(msg))",
        "            self.wait(2)",
        "            return",
        "",
        "        t_min, t_max = min(times), max(times)",
        "        T_min, T_max = min(temp), max(temp)",
        "        T_margin = (T_max - T_min) * 0.1 + 1",
        "",
        "        axes = Axes(",
        "            x_range=[t_min, t_max, (t_max - t_min) / 5],",
        "            y_range=[T_min - T_margin, T_max + T_margin, (T_max - T_min + 2*T_margin) / 4],",
        "            x_length=10, y_length=5,",
        "            axis_config={'color': WHITE},",
        "        ).shift(DOWN * 0.3)",
        "        x_lbl = axes.get_x_axis_label('Time [s]')",
        "        y_lbl = axes.get_y_axis_label('T [K]')",
        "        self.play(Create(axes), Write(x_lbl), Write(y_lbl))",
        "",
        "        # Temperature curve",
        "        pts = [axes.c2p(times[i], temp[i]) for i in range(len(times))]",
        "        curve = VMobject(stroke_color=RED, stroke_width=3)",
        "        curve.set_points_smoothly(pts)",
        "        lbl = Text('T', font_size=18, color=RED).next_to(curve, RIGHT)",
        "        self.play(Create(curve), Write(lbl), run_time=3)",
        "",
        "        self.wait(2)",
    ]
    return "\n".join(lines)


@register_scene("flame_profile")
def generate_flame_profile_scene(params):
    """Animated flame temperature/species profile."""
    positions = params.get("positions", [])  # spatial coordinate
    temperature_profile = params.get("temperature_profile", [])
    species_profiles = params.get("species_profiles", {})
    title = params.get("title", "Flame Profile")

    colors = ["RED", "BLUE", "GREEN", "YELLOW", "PURPLE"]

    lines = [
        "from manim import *",
        "import numpy as np",
        "",
        "class GeneratedScene(Scene):",
        "    def construct(self):",
        f"        title = Text(\"{title}\", font_size=28, color=WHITE).to_edge(UP)",
        "        self.play(Write(title))",
        "",
        f"        pos = {positions[:200]}",
        f"        temp = {temperature_profile[:200]}",
        "",
        "        if not pos or not temp:",
        "            msg = Text('No flame data', font_size=20, color=GREY)",
        "            self.play(Write(msg))",
        "            self.wait(2)",
        "            return",
        "",
        "        x_min, x_max = min(pos), max(pos)",
        "        T_min, T_max = min(temp), max(temp)",
        "        T_margin = (T_max - T_min) * 0.1 + 1",
        "",
        "        axes = Axes(",
        "            x_range=[x_min, x_max, (x_max - x_min) / 5],",
        "            y_range=[T_min - T_margin, T_max + T_margin, (T_max - T_min + 2*T_margin) / 4],",
        "            x_length=10, y_length=5,",
        "            axis_config={'color': WHITE},",
        "        ).shift(DOWN * 0.3)",
        "        x_lbl = axes.get_x_axis_label('Position [m]')",
        "        y_lbl = axes.get_y_axis_label('T [K]')",
        "        self.play(Create(axes), Write(x_lbl), Write(y_lbl))",
        "",
        "        pts = [axes.c2p(pos[i], temp[i]) for i in range(len(pos))]",
        "        curve = VMobject(stroke_color=RED, stroke_width=3)",
        "        curve.set_points_smoothly(pts)",
        "        lbl = Text('T', font_size=18, color=RED).next_to(curve, RIGHT)",
        "        self.play(Create(curve), Write(lbl), run_time=2)",
        "",
        "        self.wait(2)",
    ]
    return "\n".join(lines)


@register_scene("descriptor_radar_chart")
def generate_descriptor_radar_chart_scene(params):
    """Animated radar chart of molecular descriptors."""
    descriptors = params.get("descriptors", {})  # {name: value}
    title = params.get("title", "Molecular Descriptors")

    desc_items = list(descriptors.items()) if descriptors else [("MW", 0.5), ("LogP", 0.3), ("HBA", 0.7)]

    lines = [
        "from manim import *",
        "import numpy as np",
        "",
        "class GeneratedScene(Scene):",
        "    def construct(self):",
        f"        title = Text(\"{title}\", font_size=28, color=WHITE).to_edge(UP)",
        "        self.play(Write(title))",
        "",
        f"        desc_names = {[d[0] for d in desc_items]}",
        f"        desc_values = {[d[1] for d in desc_items]}",
        "",
        "        n = len(desc_names)",
        "        if n == 0:",
        "            self.wait(2)",
        "            return",
        "",
        "        # Normalize values to [0, 1]",
        "        max_val = max(abs(v) for v in desc_values) if desc_values else 1",
        "        norm_vals = [v / max_val for v in desc_values]",
        "",
        "        radius = 2.5",
        "        angles = [i * TAU / n for i in range(n)]",
        "",
        "        # Draw axes",
        "        axes_group = VGroup()",
        "        for i in range(n):",
        "            angle = angles[i]",
        "            end = np.array([radius * np.cos(angle), radius * np.sin(angle), 0])",
        "            line = Line(ORIGIN, end, color=GREY, stroke_width=1)",
        "            lbl = Text(desc_names[i], font_size=14, color=WHITE)",
        "            lbl.move_to(end * 1.2)",
        "            axes_group.add(line, lbl)",
        "        self.play(Create(axes_group), run_time=1.5)",
        "",
        "        # Draw data polygon",
        "        pts = []",
        "        for i in range(n):",
        "            r = abs(norm_vals[i]) * radius",
        "            angle = angles[i]",
        "            pts.append(np.array([r * np.cos(angle), r * np.sin(angle), 0]))",
        "        pts.append(pts[0])  # close polygon",
        "        polygon = Polygon(*pts, stroke_color=BLUE, fill_color=BLUE, fill_opacity=0.3, stroke_width=2)",
        "        self.play(Create(polygon), run_time=2)",
        "",
        "        self.wait(2)",
    ]
    return "\n".join(lines)


@register_scene("sapt_decomposition")
def generate_sapt_decomposition_scene(params):
    """Animated SAPT energy component bar chart."""
    components = params.get("components", {})  # {name: value_kcal}
    title = params.get("title", "SAPT Energy Decomposition")

    if not components:
        components = {"Elst": -5.0, "Exch": 3.0, "Ind": -2.0, "Disp": -4.0}

    comp_items = list(components.items())
    colors = ["BLUE", "RED", "GREEN", "PURPLE", "ORANGE", "TEAL"]

    lines = [
        "from manim import *",
        "import numpy as np",
        "",
        "class GeneratedScene(Scene):",
        "    def construct(self):",
        f"        title = Text(\"{title}\", font_size=28, color=WHITE).to_edge(UP)",
        "        self.play(Write(title))",
        "",
        f"        names = {[c[0] for c in comp_items]}",
        f"        values = {[c[1] for c in comp_items]}",
        f"        colors = [{', '.join(colors[:len(comp_items)])}]",
        "",
        "        n = len(names)",
        "        max_abs = max(abs(v) for v in values) if values else 1",
        "        bar_width = 0.8",
        "        spacing = 1.5",
        "        scale = 3.0 / max_abs",
        "",
        "        # Zero line",
        "        x_start = -(n - 1) * spacing / 2 - 1",
        "        x_end = (n - 1) * spacing / 2 + 1",
        "        zero_line = Line([x_start, 0, 0], [x_end, 0, 0], color=GREY, stroke_width=1)",
        "        self.play(Create(zero_line))",
        "",
        "        # Bars",
        "        for i in range(n):",
        "            x = (i - (n - 1) / 2) * spacing",
        "            h = values[i] * scale",
        "            bar = Rectangle(",
        "                width=bar_width, height=abs(h),",
        "                fill_color=colors[i], fill_opacity=0.7,",
        "                stroke_color=colors[i], stroke_width=1.5,",
        "            )",
        "            bar.move_to([x, h / 2, 0])",
        "            lbl = Text(names[i], font_size=14, color=WHITE)",
        "            lbl.next_to(bar, DOWN if h >= 0 else UP, buff=0.15)",
        "            val_txt = Text(f'{values[i]:.1f}', font_size=12, color=colors[i])",
        "            val_txt.next_to(bar, UP if h >= 0 else DOWN, buff=0.1)",
        "            self.play(GrowFromEdge(bar, DOWN if h >= 0 else UP), Write(lbl), Write(val_txt), run_time=0.6)",
        "",
        "        self.wait(2)",
    ]
    return "\n".join(lines)
