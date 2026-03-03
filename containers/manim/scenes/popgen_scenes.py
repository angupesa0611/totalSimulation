"""Population genetics scene generators — allele frequency, phylogenetic tree."""

from scenes import register_scene


@register_scene("allele_frequency_trajectory")
def generate_allele_frequency_trajectory_scene(params):
    """Animated allele frequency drift/selection curves."""
    generations = params.get("generations", [])
    allele_freqs = params.get("allele_freqs", {})  # {locus/pop: [freq_values]}
    title = params.get("title", "Allele Frequency Trajectory")

    colors = ["BLUE", "RED", "GREEN", "YELLOW", "PURPLE", "ORANGE", "TEAL"]

    lines = [
        "from manim import *",
        "import numpy as np",
        "",
        "class GeneratedScene(Scene):",
        "    def construct(self):",
        f"        title = Text(\"{title}\", font_size=28, color=WHITE).to_edge(UP)",
        "        self.play(Write(title))",
        "",
        f"        gens = {generations[:200]}",
    ]

    freq_items = list(allele_freqs.items())
    for i, (name, vals) in enumerate(freq_items):
        lines.append(f"        freq_{i} = {vals[:200]}")

    lines += [
        "",
        "        g_min = min(gens) if gens else 0",
        "        g_max = max(gens) if gens else 1",
        "",
        "        axes = Axes(",
        "            x_range=[g_min, g_max, (g_max - g_min) / 5],",
        "            y_range=[0, 1.05, 0.25],",
        "            x_length=10, y_length=5,",
        "            axis_config={'color': WHITE},",
        "        ).shift(DOWN * 0.3)",
        "        x_lbl = axes.get_x_axis_label('Generation')",
        "        y_lbl = axes.get_y_axis_label('Freq')",
        "        self.play(Create(axes), Write(x_lbl), Write(y_lbl))",
        "",
    ]

    for i, (name, _) in enumerate(freq_items):
        color = colors[i % len(colors)]
        lines += [
            f"        pts_{i} = [axes.c2p(gens[j], freq_{i}[j]) for j in range(min(len(gens), len(freq_{i})))]",
            f"        crv_{i} = VMobject(stroke_color={color}, stroke_width=2)",
            f"        crv_{i}.set_points_smoothly(pts_{i})",
            f"        lbl_{i} = Text(\"{name}\", font_size=14, color={color}).next_to(crv_{i}, RIGHT)",
            f"        self.play(Create(crv_{i}), Write(lbl_{i}), run_time=2)",
        ]

    lines.append("        self.wait(2)")
    return "\n".join(lines)


@register_scene("phylogenetic_tree_animation")
def generate_phylogenetic_tree_animation_scene(params):
    """Animated phylogenetic tree growth."""
    nodes = params.get("nodes", [])  # [{id, label, x, y}]
    edges = params.get("edges", [])  # [[parent_id, child_id]]
    title = params.get("title", "Phylogenetic Tree")

    lines = [
        "from manim import *",
        "import numpy as np",
        "",
        "class GeneratedScene(Scene):",
        "    def construct(self):",
        f"        title = Text(\"{title}\", font_size=28, color=WHITE).to_edge(UP)",
        "        self.play(Write(title))",
        "",
        f"        nodes = {nodes}",
        f"        edges = {edges}",
        "",
        "        if not nodes:",
        "            msg = Text('No tree data', font_size=20, color=GREY)",
        "            self.play(Write(msg))",
        "            self.wait(2)",
        "            return",
        "",
        "        # Build position map",
        "        pos_map = {}",
        "        for n in nodes:",
        "            pos_map[n['id']] = np.array([n.get('x', 0) * 2, n.get('y', 0) * 2, 0])",
        "",
        "        # Draw edges (branches) first",
        "        branch_group = VGroup()",
        "        for e in edges:",
        "            if e[0] in pos_map and e[1] in pos_map:",
        "                p1, p2 = pos_map[e[0]], pos_map[e[1]]",
        "                # L-shaped branch",
        "                mid = np.array([p2[0], p1[1], 0])",
        "                branch_group.add(Line(p1, mid, color=TEAL, stroke_width=2))",
        "                branch_group.add(Line(mid, p2, color=TEAL, stroke_width=2))",
        "        self.play(LaggedStart(*[Create(b) for b in branch_group], lag_ratio=0.1), run_time=3)",
        "",
        "        # Draw leaf labels",
        "        leaf_ids = set(n['id'] for n in nodes) - set(e[0] for e in edges)",
        "        labels = VGroup()",
        "        for n in nodes:",
        "            if n['id'] in leaf_ids:",
        "                lbl = Text(n.get('label', str(n['id'])), font_size=12, color=WHITE)",
        "                lbl.next_to(pos_map[n['id']], RIGHT, buff=0.15)",
        "                labels.add(lbl)",
        "        self.play(LaggedStart(*[Write(l) for l in labels], lag_ratio=0.05), run_time=2)",
        "",
        "        self.wait(2)",
    ]
    return "\n".join(lines)
