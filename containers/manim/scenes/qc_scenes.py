"""Quantum computing scene generators — circuit animation, VQE convergence."""

from scenes import register_scene


@register_scene("quantum_circuit_animation")
def generate_quantum_circuit_animation_scene(params):
    """Gate-by-gate quantum circuit animation."""
    n_qubits = params.get("n_qubits", 2)
    gates = params.get("gates", [])  # [{type, qubit, params, control}]
    title = params.get("title", "Quantum Circuit")

    gate_colors = {
        "H": "YELLOW", "X": "RED", "Y": "GREEN", "Z": "BLUE",
        "CNOT": "PURPLE", "CZ": "TEAL", "RX": "ORANGE", "RY": "ORANGE",
        "RZ": "ORANGE", "S": "PINK", "T": "PINK", "SWAP": "MAROON",
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
        f"        n_qubits = {n_qubits}",
        f"        gates = {gates}",
        "",
        "        # Draw qubit wires",
        "        wire_y = {}",
        "        wires = VGroup()",
        "        labels = VGroup()",
        "        for q in range(n_qubits):",
        "            y = 1.5 - q * 1.2",
        "            wire_y[q] = y",
        "            wire = Line([-5.5, y, 0], [5.5, y, 0], color=GREY, stroke_width=1.5)",
        "            wires.add(wire)",
        "            lbl = Text(f'q{q}', font_size=16, color=WHITE).move_to([-6, y, 0])",
        "            labels.add(lbl)",
        "        self.play(Create(wires), Write(labels))",
        "",
        f"        gate_colors = {gate_colors}",
        "        manim_colors = {'YELLOW': YELLOW, 'RED': RED, 'GREEN': GREEN, 'BLUE': BLUE,",
        "                        'PURPLE': PURPLE, 'TEAL': TEAL, 'ORANGE': ORANGE, 'PINK': PINK,",
        "                        'MAROON': MAROON}",
        "",
        "        # Place gates sequentially",
        "        n_gates = len(gates)",
        "        gate_spacing = min(10.0 / max(n_gates, 1), 1.0)",
        "        x_start = -4.5",
        "",
        "        for gi, gate in enumerate(gates):",
        "            x = x_start + gi * gate_spacing",
        "            g_type = gate.get('type', 'X').upper()",
        "            qubit = gate.get('qubit', 0)",
        "            control = gate.get('control', None)",
        "            y = wire_y.get(qubit, 0)",
        "",
        "            c_name = gate_colors.get(g_type, 'GREY')",
        "            color = manim_colors.get(c_name, GREY)",
        "",
        "            # Draw control line if CNOT/CZ",
        "            if control is not None and control in wire_y:",
        "                ctrl_y = wire_y[control]",
        "                ctrl_line = Line([x, ctrl_y, 0], [x, y, 0], color=WHITE, stroke_width=2)",
        "                ctrl_dot = Dot([x, ctrl_y, 0], color=WHITE, radius=0.06)",
        "                self.play(Create(ctrl_line), FadeIn(ctrl_dot), run_time=0.2)",
        "",
        "            # Draw gate box",
        "            box = Square(side_length=0.6, fill_color=color, fill_opacity=0.8,",
        "                        stroke_color=color, stroke_width=2)",
        "            box.move_to([x, y, 0])",
        "            g_lbl = Text(g_type[:3], font_size=14, color=WHITE).move_to([x, y, 0])",
        "            self.play(FadeIn(box), Write(g_lbl), run_time=0.3)",
        "",
        "        self.wait(2)",
    ]
    return "\n".join(lines)


@register_scene("vqe_convergence")
def generate_vqe_convergence_scene(params):
    """Animated VQE energy convergence plot."""
    iterations = params.get("iterations", [])
    energies = params.get("energies", [])
    exact_energy = params.get("exact_energy", None)
    title = params.get("title", "VQE Convergence")

    lines = [
        "from manim import *",
        "import numpy as np",
        "",
        "class GeneratedScene(Scene):",
        "    def construct(self):",
        f"        title = Text(\"{title}\", font_size=28, color=WHITE).to_edge(UP)",
        "        self.play(Write(title))",
        "",
        f"        iters = {iterations[:200]}",
        f"        energies = {energies[:200]}",
        "",
        "        if not iters or not energies:",
        "            msg = Text('No VQE data', font_size=20, color=GREY)",
        "            self.play(Write(msg))",
        "            self.wait(2)",
        "            return",
        "",
        "        i_min, i_max = min(iters), max(iters)",
        "        e_min, e_max = min(energies), max(energies)",
        "        e_margin = (e_max - e_min) * 0.1 + 0.1",
        "",
        "        axes = Axes(",
        "            x_range=[i_min, i_max, max(1, (i_max - i_min) / 5)],",
        "            y_range=[e_min - e_margin, e_max + e_margin, (e_max - e_min + 2*e_margin) / 4],",
        "            x_length=10, y_length=5,",
        "            axis_config={'color': WHITE},",
        "        ).shift(DOWN * 0.3)",
        "        x_lbl = axes.get_x_axis_label('Iteration')",
        "        y_lbl = axes.get_y_axis_label('Energy (Ha)')",
        "        self.play(Create(axes), Write(x_lbl), Write(y_lbl))",
        "",
    ]

    if exact_energy is not None:
        lines += [
            f"        exact = {exact_energy}",
            "        ref_line = DashedLine(",
            "            axes.c2p(i_min, exact), axes.c2p(i_max, exact),",
            "            color=GREEN, stroke_width=1.5)",
            "        ref_lbl = Text('Exact', font_size=14, color=GREEN).next_to(ref_line, RIGHT)",
            "        self.play(Create(ref_line), Write(ref_lbl))",
            "",
        ]

    lines += [
        "        # Animated convergence curve",
        "        pts = [axes.c2p(iters[j], energies[j]) for j in range(len(iters))]",
        "        curve = VMobject(stroke_color=BLUE, stroke_width=2.5)",
        "        curve.set_points_smoothly(pts)",
        "        self.play(Create(curve), run_time=4)",
        "",
        "        # Final energy annotation",
        "        final_e = energies[-1]",
        "        final_dot = Dot(axes.c2p(iters[-1], final_e), color=YELLOW, radius=0.08)",
        "        ann = Text(f'E = {final_e:.6f}', font_size=16, color=YELLOW)",
        "        ann.next_to(final_dot, UP)",
        "        self.play(FadeIn(final_dot), Write(ann))",
        "",
        "        self.wait(2)",
    ]
    return "\n".join(lines)
