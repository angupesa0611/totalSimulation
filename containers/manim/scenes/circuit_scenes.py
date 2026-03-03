"""Circuit scene generators — Bode plot, transient waveform."""

from scenes import register_scene


@register_scene("bode_plot_animation")
def generate_bode_plot_animation_scene(params):
    """Animated Bode magnitude/phase plot."""
    frequencies = params.get("frequencies", [])
    magnitude_db = params.get("magnitude_db", [])
    phase_deg = params.get("phase_deg", [])
    title = params.get("title", "Bode Plot")

    lines = [
        "from manim import *",
        "import numpy as np",
        "",
        "class GeneratedScene(Scene):",
        "    def construct(self):",
        f"        title = Text(\"{title}\", font_size=28, color=WHITE).to_edge(UP)",
        "        self.play(Write(title))",
        "",
        f"        freq = {frequencies[:200]}",
        f"        mag = {magnitude_db[:200]}",
        f"        phase = {phase_deg[:200]}",
        "",
        "        if not freq:",
        "            msg = Text('No Bode data', font_size=20, color=GREY)",
        "            self.play(Write(msg))",
        "            self.wait(2)",
        "            return",
        "",
        "        # Use log10 of frequency for x-axis",
        "        log_freq = [np.log10(f) if f > 0 else 0 for f in freq]",
        "        lf_min, lf_max = min(log_freq), max(log_freq)",
        "",
        "        # Magnitude plot (top)",
        "        if mag:",
        "            m_min, m_max = min(mag), max(mag)",
        "            m_margin = (m_max - m_min) * 0.1 + 1",
        "            ax_mag = Axes(",
        "                x_range=[lf_min, lf_max, (lf_max - lf_min) / 5],",
        "                y_range=[m_min - m_margin, m_max + m_margin, (m_max - m_min + 2*m_margin) / 4],",
        "                x_length=10, y_length=2.5,",
        "                axis_config={'color': WHITE},",
        "            ).shift(UP * 1.5)",
        "            m_lbl = Text('|H| (dB)', font_size=14, color=BLUE).next_to(ax_mag, LEFT)",
        "            self.play(Create(ax_mag), Write(m_lbl))",
        "",
        "            pts_m = [ax_mag.c2p(log_freq[i], mag[i]) for i in range(min(len(log_freq), len(mag)))]",
        "            crv_m = VMobject(stroke_color=BLUE, stroke_width=2.5)",
        "            crv_m.set_points_smoothly(pts_m)",
        "            self.play(Create(crv_m), run_time=2)",
        "",
        "        # Phase plot (bottom)",
        "        if phase:",
        "            p_min, p_max = min(phase), max(phase)",
        "            p_margin = (p_max - p_min) * 0.1 + 1",
        "            ax_ph = Axes(",
        "                x_range=[lf_min, lf_max, (lf_max - lf_min) / 5],",
        "                y_range=[p_min - p_margin, p_max + p_margin, (p_max - p_min + 2*p_margin) / 4],",
        "                x_length=10, y_length=2.5,",
        "                axis_config={'color': WHITE},",
        "            ).shift(DOWN * 2)",
        "            p_lbl = Text('Phase (deg)', font_size=14, color=RED).next_to(ax_ph, LEFT)",
        "            self.play(Create(ax_ph), Write(p_lbl))",
        "",
        "            pts_p = [ax_ph.c2p(log_freq[i], phase[i]) for i in range(min(len(log_freq), len(phase)))]",
        "            crv_p = VMobject(stroke_color=RED, stroke_width=2.5)",
        "            crv_p.set_points_smoothly(pts_p)",
        "            self.play(Create(crv_p), run_time=2)",
        "",
        "        self.wait(2)",
    ]
    return "\n".join(lines)


@register_scene("transient_waveform")
def generate_transient_waveform_scene(params):
    """Animated voltage/current waveforms from circuit simulation."""
    times = params.get("times", [])
    signals = params.get("signals", {})  # {name: [values]}
    title = params.get("title", "Transient Analysis")

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
        f"        times = {times[:200]}",
    ]

    sig_items = list(signals.items())
    for i, (name, vals) in enumerate(sig_items):
        lines.append(f"        sig_{i} = {vals[:200]}")

    lines += [
        "",
        "        if not times:",
        "            msg = Text('No waveform data', font_size=20, color=GREY)",
        "            self.play(Write(msg))",
        "            self.wait(2)",
        "            return",
        "",
        "        t_min, t_max = min(times), max(times)",
        "        all_v = []",
    ]
    for i in range(len(sig_items)):
        lines.append(f"        all_v.extend(sig_{i})")
    lines += [
        "        v_min = min(all_v) if all_v else -1",
        "        v_max = max(all_v) if all_v else 1",
        "        v_margin = (v_max - v_min) * 0.1 + 1e-10",
        "",
        "        axes = Axes(",
        "            x_range=[t_min, t_max, (t_max - t_min) / 5],",
        "            y_range=[v_min - v_margin, v_max + v_margin, (v_max - v_min + 2*v_margin) / 4],",
        "            x_length=10, y_length=5,",
        "            axis_config={'color': WHITE},",
        "        ).shift(DOWN * 0.3)",
        "        x_lbl = axes.get_x_axis_label('Time')",
        "        y_lbl = axes.get_y_axis_label('V / I')",
        "        self.play(Create(axes), Write(x_lbl), Write(y_lbl))",
        "",
    ]

    for i, (name, _) in enumerate(sig_items):
        color = colors[i % len(colors)]
        lines += [
            f"        pts_{i} = [axes.c2p(times[j], sig_{i}[j]) for j in range(min(len(times), len(sig_{i})))]",
            f"        crv_{i} = VMobject(stroke_color={color}, stroke_width=2.5)",
            f"        crv_{i}.set_points_smoothly(pts_{i})",
            f"        lbl_{i} = Text(\"{name}\", font_size=14, color={color}).next_to(crv_{i}, RIGHT)",
            f"        self.play(Create(crv_{i}), Write(lbl_{i}), run_time=2)",
        ]

    lines.append("        self.wait(2)")
    return "\n".join(lines)
