"""Math scene generators — equation, function_plot, geometry, graph_animation."""

from scenes import register_scene


@register_scene("equation_animation")
def generate_equation_scene(params):
    """Generate a Manim scene for equation animation."""
    expressions = params.get("expressions", [r"E = mc^2"])
    anim_type = params.get("animation_type", "write")

    lines = [
        "from manim import *",
        "",
        "class GeneratedScene(Scene):",
        "    def construct(self):",
    ]

    if anim_type == "write":
        for i, expr in enumerate(expressions):
            var = f"eq{i}"
            lines.append(f"        {var} = MathTex(r\"{expr}\")")
            if i > 0:
                lines.append(f"        {var}.next_to(eq{i-1}, DOWN)")
            lines.append(f"        self.play(Write({var}))")
            lines.append(f"        self.wait(0.5)")
    elif anim_type == "transform":
        if len(expressions) >= 1:
            lines.append(f"        eq = MathTex(r\"{expressions[0]}\")")
            lines.append("        self.play(Write(eq))")
            lines.append("        self.wait(0.5)")
            for i in range(1, len(expressions)):
                lines.append(f"        new_eq = MathTex(r\"{expressions[i]}\")")
                lines.append("        self.play(TransformMatchingTex(eq, new_eq))")
                lines.append("        eq = new_eq")
                lines.append("        self.wait(0.5)")
    elif anim_type == "fade":
        for i, expr in enumerate(expressions):
            var = f"eq{i}"
            lines.append(f"        {var} = MathTex(r\"{expr}\")")
            lines.append(f"        self.play(FadeIn({var}))")
            lines.append(f"        self.wait(0.5)")
            if i < len(expressions) - 1:
                lines.append(f"        self.play(FadeOut({var}))")

    lines.append("        self.wait(1)")
    return "\n".join(lines)


@register_scene("function_plot")
def generate_function_plot_scene(params):
    """Generate a Manim scene for function plotting."""
    functions = params.get("functions", ["lambda x: np.sin(x)"])
    x_range = params.get("x_range", [-5, 5])
    animate_draw = params.get("animate_draw", True)

    colors = ["BLUE", "GREEN", "RED", "YELLOW", "PURPLE", "ORANGE"]

    lines = [
        "from manim import *",
        "import numpy as np",
        "",
        "class GeneratedScene(Scene):",
        "    def construct(self):",
        f"        axes = Axes(x_range=[{x_range[0]}, {x_range[1]}, 1], y_range=[-2, 2, 1],"
        "            axis_config={\"color\": WHITE})",
        "        axes_labels = axes.get_axis_labels(x_label=\"x\", y_label=\"y\")",
        "        self.play(Create(axes), Write(axes_labels))",
    ]

    for i, func_str in enumerate(functions):
        color = colors[i % len(colors)]
        lines.append(f"        graph{i} = axes.plot({func_str}, color={color})")
        if animate_draw:
            lines.append(f"        self.play(Create(graph{i}))")
        else:
            lines.append(f"        self.add(graph{i})")

    lines.append("        self.wait(2)")
    return "\n".join(lines)


@register_scene("geometry_animation")
def generate_geometry_scene(params):
    """Generate a Manim scene for geometry animation."""
    shapes = params.get("shapes", [{"type": "circle", "params": {"radius": 1}}])
    transformations = params.get("transformations", [])

    lines = [
        "from manim import *",
        "",
        "class GeneratedScene(Scene):",
        "    def construct(self):",
    ]

    shape_vars = []
    for i, shape_def in enumerate(shapes):
        stype = shape_def["type"]
        sparams = shape_def.get("params", {})
        var = f"shape{i}"
        shape_vars.append(var)

        if stype == "circle":
            r = sparams.get("radius", 1)
            lines.append(f"        {var} = Circle(radius={r}, color=BLUE)")
        elif stype == "square":
            side = sparams.get("side_length", 2)
            lines.append(f"        {var} = Square(side_length={side}, color=GREEN)")
        elif stype == "line":
            start = sparams.get("start", [-2, 0, 0])
            end = sparams.get("end", [2, 0, 0])
            lines.append(f"        {var} = Line(start={start}, end={end}, color=RED)")
        elif stype == "arrow":
            start = sparams.get("start", [-2, 0, 0])
            end = sparams.get("end", [2, 0, 0])
            lines.append(f"        {var} = Arrow(start={start}, end={end}, color=YELLOW)")

        lines.append(f"        self.play(Create({var}))")

    for t in transformations:
        ttype = t["type"]
        tparams = t.get("params", {})
        target = t.get("target", shape_vars[0] if shape_vars else "shape0")

        if ttype == "rotate":
            angle = tparams.get("angle", 3.14159)
            lines.append(f"        self.play(Rotate({target}, angle={angle}))")
        elif ttype == "scale":
            factor = tparams.get("factor", 2)
            lines.append(f"        self.play({target}.animate.scale({factor}))")
        elif ttype == "shift":
            direction = tparams.get("direction", [2, 0, 0])
            lines.append(f"        self.play({target}.animate.shift({direction}))")

    lines.append("        self.wait(1)")
    return "\n".join(lines)


@register_scene("graph_animation")
def generate_graph_animation_scene(params):
    """Generate a Manim scene for graph traversal animation."""
    nodes = params.get("nodes", [0, 1, 2, 3])
    edges = params.get("edges", [[0, 1], [1, 2], [2, 3]])
    highlight_path = params.get("highlight_path", [])

    lines = [
        "from manim import *",
        "",
        "class GeneratedScene(Scene):",
        "    def construct(self):",
        f"        vertices = {nodes}",
        f"        edges_list = {edges}",
        "        graph = Graph(vertices, edges_list, layout=\"spring\","
        "            vertex_config={\"fill_color\": BLUE},"
        "            edge_config={\"stroke_color\": WHITE})",
        "        self.play(Create(graph))",
        "        self.wait(0.5)",
    ]

    if highlight_path:
        lines.append(f"        path = {highlight_path}")
        lines.append("        for i in range(len(path) - 1):")
        lines.append("            self.play(")
        lines.append("                graph[path[i]].animate.set_color(RED),")
        lines.append("                graph.edges[(path[i], path[i+1])].animate.set_color(RED)")
        lines.append("                if (path[i], path[i+1]) in graph.edges")
        lines.append("                else graph.edges[(path[i+1], path[i])].animate.set_color(RED),")
        lines.append("                run_time=0.5)")
        lines.append("        self.play(graph[path[-1]].animate.set_color(RED))")

    lines.append("        self.wait(2)")
    return "\n".join(lines)
