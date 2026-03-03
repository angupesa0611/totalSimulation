"""Biology scene generators — concentration time course, reaction network, spike raster."""

from scenes import register_scene


@register_scene("concentration_time_course")
def generate_concentration_time_course_scene(params):
    """Animated species concentration curves from systems biology."""
    times = params.get("times", [])
    species = params.get("species", {})  # {name: [values]}
    title = params.get("title", "Concentration Time Course")

    colors = ["BLUE", "RED", "GREEN", "YELLOW", "PURPLE", "ORANGE", "TEAL", "PINK"]

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
    ]

    species_items = list(species.items())
    for i, (name, values) in enumerate(species_items):
        lines.append(f"        sp_{i} = {values[:200]}")

    lines += [
        "",
        "        t_min, t_max = (min(times), max(times)) if times else (0, 1)",
        "        all_vals = []",
    ]
    for i in range(len(species_items)):
        lines.append(f"        all_vals.extend(sp_{i})")
    lines += [
        "        v_min = min(all_vals) if all_vals else 0",
        "        v_max = max(all_vals) if all_vals else 1",
        "        margin = (v_max - v_min) * 0.1 + 1e-10",
        "",
        "        axes = Axes(",
        "            x_range=[t_min, t_max, (t_max - t_min) / 5],",
        "            y_range=[max(0, v_min - margin), v_max + margin, (v_max - v_min + 2*margin) / 4],",
        "            x_length=10, y_length=5,",
        "            axis_config={'color': WHITE},",
        "        ).shift(DOWN * 0.3)",
        "        x_lbl = axes.get_x_axis_label('Time')",
        "        y_lbl = axes.get_y_axis_label('Conc.')",
        "        self.play(Create(axes), Write(x_lbl), Write(y_lbl))",
        "",
    ]

    for i, (name, _) in enumerate(species_items):
        color = colors[i % len(colors)]
        lines += [
            f"        pts_{i} = [axes.c2p(times[j], sp_{i}[j]) for j in range(min(len(times), len(sp_{i})))]",
            f"        crv_{i} = VMobject(stroke_color={color}, stroke_width=2.5)",
            f"        crv_{i}.set_points_smoothly(pts_{i})",
            f"        lbl_{i} = Text(\"{name}\", font_size=14, color={color}).next_to(crv_{i}, RIGHT)",
            f"        self.play(Create(crv_{i}), Write(lbl_{i}), run_time=2)",
        ]

    lines.append("        self.wait(2)")
    return "\n".join(lines)


@register_scene("reaction_network_graph")
def generate_reaction_network_graph_scene(params):
    """Animated reaction network with species nodes and reaction edges."""
    species_nodes = params.get("species_nodes", [])
    reactions = params.get("reactions", [])  # [{from, to, rate}]
    title = params.get("title", "Reaction Network")

    if not species_nodes:
        species_nodes = ["A", "B", "C"]
    if not reactions:
        reactions = [{"from": 0, "to": 1}, {"from": 1, "to": 2}]

    nodes_list = list(range(len(species_nodes)))
    edges_list = [[r["from"], r["to"]] for r in reactions]

    lines = [
        "from manim import *",
        "",
        "class GeneratedScene(Scene):",
        "    def construct(self):",
        f"        title = Text(\"{title}\", font_size=28, color=WHITE).to_edge(UP)",
        "        self.play(Write(title))",
        "",
        f"        species = {species_nodes}",
        f"        vertices = {nodes_list}",
        f"        edges = {edges_list}",
        "        edge_tuples = [(e[0], e[1]) for e in edges]",
        "",
        "        labels = {i: Text(s, font_size=16) for i, s in enumerate(species)}",
        "        graph = Graph(",
        "            vertices, edge_tuples,",
        "            layout='spring',",
        "            labels=labels,",
        "            vertex_config={'fill_color': TEAL, 'radius': 0.3},",
        "            edge_config={'stroke_color': WHITE},",
        "        )",
        "        self.play(Create(graph), run_time=2)",
        "",
        "        # Animate flux along edges",
        "        for edge in edge_tuples:",
        "            self.play(",
        "                graph.edges[edge].animate.set_color(YELLOW),",
        "                run_time=0.4",
        "            )",
        "            self.play(",
        "                graph.edges[edge].animate.set_color(WHITE),",
        "                run_time=0.2",
        "            )",
        "",
        "        self.wait(2)",
    ]
    return "\n".join(lines)


@register_scene("spike_raster_animation")
def generate_spike_raster_animation_scene(params):
    """Animated spike raster + voltage traces from neural simulation."""
    spike_trains = params.get("spike_trains", {})  # {neuron_id: [spike_times]}
    voltage_trace = params.get("voltage_trace", {})  # {times, values}
    title = params.get("title", "Spike Raster")
    t_max = params.get("t_max", 100)

    lines = [
        "from manim import *",
        "import numpy as np",
        "",
        "class GeneratedScene(Scene):",
        "    def construct(self):",
        f"        title = Text(\"{title}\", font_size=28, color=WHITE).to_edge(UP)",
        "        self.play(Write(title))",
        "",
        f"        spike_trains = {spike_trains}",
        f"        t_max = {t_max}",
        "",
        "        n_neurons = len(spike_trains)",
        "        if n_neurons == 0:",
        "            msg = Text('No spike data', font_size=20, color=GREY)",
        "            self.play(Write(msg))",
        "            self.wait(2)",
        "            return",
        "",
        "        # Raster plot area",
        "        raster_h = 3.5",
        "        raster_w = 10",
        "        origin = np.array([-5, -1, 0])",
        "",
        "        # Draw raster axes",
        "        x_axis = Line(origin, origin + RIGHT * raster_w, color=WHITE)",
        "        y_axis = Line(origin, origin + UP * raster_h, color=WHITE)",
        "        self.play(Create(x_axis), Create(y_axis))",
        "",
        "        # Draw spikes",
        "        spikes = VGroup()",
        "        row_h = raster_h / max(n_neurons, 1)",
        "        for i, (nid, times) in enumerate(spike_trains.items()):",
        "            y = origin[1] + (i + 0.5) * row_h",
        "            for t in times[:50]:",
        "                x = origin[0] + (t / t_max) * raster_w",
        "                tick = Line([x, y - row_h * 0.3, 0], [x, y + row_h * 0.3, 0],",
        "                           color=BLUE, stroke_width=1.5)",
        "                spikes.add(tick)",
        "",
        "        self.play(LaggedStart(*[FadeIn(s) for s in spikes], lag_ratio=0.01), run_time=3)",
        "",
    ]

    if voltage_trace:
        lines += [
            f"        v_times = {voltage_trace.get('times', [])[:200]}",
            f"        v_vals = {voltage_trace.get('values', [])[:200]}",
            "        if v_times and v_vals:",
            "            v_min, v_max_v = min(v_vals), max(v_vals)",
            "            v_span = v_max_v - v_min if v_max_v != v_min else 1",
            "            v_pts = []",
            "            for j in range(len(v_times)):",
            "                x = origin[0] + (v_times[j] / t_max) * raster_w",
            "                y = -2.5 + 1.5 * (v_vals[j] - v_min) / v_span",
            "                v_pts.append(np.array([x, y, 0]))",
            "            if len(v_pts) > 1:",
            "                v_curve = VMobject(stroke_color=YELLOW, stroke_width=2)",
            "                v_curve.set_points_smoothly(v_pts)",
            "                v_lbl = Text('Vm', font_size=14, color=YELLOW).next_to(v_curve, RIGHT)",
            "                self.play(Create(v_curve), Write(v_lbl), run_time=2)",
        ]

    lines.append("        self.wait(2)")
    return "\n".join(lines)
