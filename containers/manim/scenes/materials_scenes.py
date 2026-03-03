"""Materials science scene generators — band structure, RDF."""

from scenes import register_scene


@register_scene("band_structure_animation")
def generate_band_structure_animation_scene(params):
    """Animated band structure plot from DFT."""
    k_points = params.get("k_points", [])
    bands = params.get("bands", [])  # list of band energy arrays
    k_labels = params.get("k_labels", [])  # [(k_index, label)]
    fermi_energy = params.get("fermi_energy", 0)
    title = params.get("title", "Band Structure")

    colors = ["BLUE", "RED", "GREEN", "YELLOW", "PURPLE", "ORANGE"]

    lines = [
        "from manim import *",
        "import numpy as np",
        "",
        "class GeneratedScene(Scene):",
        "    def construct(self):",
        f"        title = Text(\"{title}\", font_size=28, color=WHITE).to_edge(UP)",
        "        self.play(Write(title))",
        "",
        f"        k_pts = {k_points[:200]}",
        f"        bands = {[b[:200] for b in bands[:20]]}",
        f"        fermi = {fermi_energy}",
        "",
        "        if not k_pts or not bands:",
        "            msg = Text('No band data', font_size=20, color=GREY)",
        "            self.play(Write(msg))",
        "            self.wait(2)",
        "            return",
        "",
        "        k_min, k_max = min(k_pts), max(k_pts)",
        "        all_e = [e for band in bands for e in band]",
        "        e_min, e_max = min(all_e), max(all_e)",
        "        e_margin = (e_max - e_min) * 0.1 + 0.5",
        "",
        "        axes = Axes(",
        "            x_range=[k_min, k_max, (k_max - k_min) / 5],",
        "            y_range=[e_min - e_margin, e_max + e_margin, (e_max - e_min + 2*e_margin) / 4],",
        "            x_length=10, y_length=5,",
        "            axis_config={'color': WHITE},",
        "        ).shift(DOWN * 0.3)",
        "        y_lbl = axes.get_y_axis_label('E (eV)')",
        "        self.play(Create(axes), Write(y_lbl))",
        "",
        "        # Fermi level",
        "        fermi_line = DashedLine(",
        "            axes.c2p(k_min, fermi), axes.c2p(k_max, fermi),",
        "            color=YELLOW, stroke_width=1.5)",
        "        f_lbl = Text('Ef', font_size=14, color=YELLOW).next_to(fermi_line, RIGHT)",
        "        self.play(Create(fermi_line), Write(f_lbl))",
        "",
        "        # Draw bands",
        "        colors = [BLUE, RED, GREEN, TEAL, PURPLE, ORANGE]",
        "        for bi, band in enumerate(bands):",
        "            pts = [axes.c2p(k_pts[j], band[j]) for j in range(min(len(k_pts), len(band)))]",
        "            crv = VMobject(stroke_color=colors[bi % len(colors)], stroke_width=1.5)",
        "            crv.set_points_smoothly(pts)",
        "            self.play(Create(crv), run_time=0.5)",
        "",
        "        self.wait(2)",
    ]
    return "\n".join(lines)


@register_scene("rdf_animation")
def generate_rdf_animation_scene(params):
    """Animated radial distribution function g(r)."""
    r_values = params.get("r_values", [])
    g_values = params.get("g_values", [])
    rdf_frames = params.get("rdf_frames", [])  # optional: time evolution
    title = params.get("title", "Radial Distribution Function")

    lines = [
        "from manim import *",
        "import numpy as np",
        "",
        "class GeneratedScene(Scene):",
        "    def construct(self):",
        f"        title = Text(\"{title}\", font_size=28, color=WHITE).to_edge(UP)",
        "        self.play(Write(title))",
        "",
        f"        r = {r_values[:200]}",
        f"        g = {g_values[:200]}",
        f"        rdf_frames = {rdf_frames[:10]}",
        "",
        "        if not r:",
        "            msg = Text('No RDF data', font_size=20, color=GREY)",
        "            self.play(Write(msg))",
        "            self.wait(2)",
        "            return",
        "",
        "        r_min, r_max = min(r), max(r)",
        "        all_g = g if g else [v for frame in rdf_frames for v in frame]",
        "        g_max_v = max(all_g) if all_g else 2",
        "",
        "        axes = Axes(",
        "            x_range=[r_min, r_max, (r_max - r_min) / 5],",
        "            y_range=[0, g_max_v * 1.1, g_max_v / 4],",
        "            x_length=10, y_length=5,",
        "            axis_config={'color': WHITE},",
        "        ).shift(DOWN * 0.3)",
        "        x_lbl = axes.get_x_axis_label('r')",
        "        y_lbl = axes.get_y_axis_label('g(r)')",
        "        self.play(Create(axes), Write(x_lbl), Write(y_lbl))",
        "",
        "        # g(r) = 1 reference line",
        "        ref = DashedLine(axes.c2p(r_min, 1), axes.c2p(r_max, 1), color=GREY, stroke_width=1)",
        "        self.play(Create(ref))",
        "",
        "        if rdf_frames:",
        "            prev_crv = None",
        "            for fi, g_frame in enumerate(rdf_frames):",
        "                pts = [axes.c2p(r[j], g_frame[j]) for j in range(min(len(r), len(g_frame)))]",
        "                crv = VMobject(stroke_color=BLUE, stroke_width=2.5)",
        "                crv.set_points_smoothly(pts)",
        "                if prev_crv is None:",
        "                    self.play(Create(crv), run_time=2)",
        "                else:",
        "                    self.play(ReplacementTransform(prev_crv, crv), run_time=0.5)",
        "                prev_crv = crv",
        "        elif g:",
        "            pts = [axes.c2p(r[j], g[j]) for j in range(min(len(r), len(g)))]",
        "            crv = VMobject(stroke_color=BLUE, stroke_width=2.5)",
        "            crv.set_points_smoothly(pts)",
        "            self.play(Create(crv), run_time=3)",
        "",
        "        self.wait(2)",
    ]
    return "\n".join(lines)
