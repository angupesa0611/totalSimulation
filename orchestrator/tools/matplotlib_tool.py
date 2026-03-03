import io
import base64
from typing import Any
import numpy as np
from celery_app import app as celery_app
from tools.base import SimulationTool
from results import save_result

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


class MatplotlibTool(SimulationTool):
    name = "Matplotlib"
    key = "matplotlib"
    layer = "visualization"

    SIMULATION_TYPES = {"line_plot", "scatter_plot", "histogram", "heatmap", "contour_plot", "bar_chart"}

    def validate_params(self, params: dict[str, Any]) -> dict[str, Any]:
        sim_type = params.get("simulation_type", "line_plot")
        if sim_type not in self.SIMULATION_TYPES:
            raise ValueError(f"Unknown simulation_type: {sim_type}. Supported: {self.SIMULATION_TYPES}")

        params.setdefault("simulation_type", sim_type)
        params.setdefault("title", "")
        params.setdefault("xlabel", "x")
        params.setdefault("ylabel", "y")
        params.setdefault("style", "seaborn-v0_8-darkgrid")
        params.setdefault("dpi", 150)
        params.setdefault("output_format", "png")

        # Normalize split figure size fields from frontend
        if "figure_width" in params or "figure_height" in params:
            params["figure_size"] = [
                params.pop("figure_width", 8),
                params.pop("figure_height", 6),
            ]
        params.setdefault("figure_size", [8, 6])

        return params

    def run(self, params: dict[str, Any]) -> dict[str, Any]:
        params = self.validate_params(params)
        sim_type = params["simulation_type"]

        if sim_type == "line_plot":
            return self._run_line_plot(params)
        elif sim_type == "scatter_plot":
            return self._run_scatter_plot(params)
        elif sim_type == "histogram":
            return self._run_histogram(params)
        elif sim_type == "heatmap":
            return self._run_heatmap(params)
        elif sim_type == "contour_plot":
            return self._run_contour_plot(params)
        elif sim_type == "bar_chart":
            return self._run_bar_chart(params)

    def _create_figure(self, params):
        style = params["style"]
        try:
            plt.style.use(style)
        except OSError:
            plt.style.use("default")
        fig, ax = plt.subplots(figsize=params["figure_size"], dpi=params["dpi"])
        return fig, ax

    def _finalize(self, fig, ax, params):
        if params["title"]:
            ax.set_title(params["title"])
        ax.set_xlabel(params["xlabel"])
        ax.set_ylabel(params["ylabel"])

        buf = io.BytesIO()
        fmt = params["output_format"]
        fig.savefig(buf, format=fmt, bbox_inches="tight", facecolor=fig.get_facecolor())
        plt.close(fig)
        buf.seek(0)
        image_b64 = base64.b64encode(buf.read()).decode("utf-8")

        return {
            "tool": "matplotlib",
            "simulation_type": params["simulation_type"],
            "image_base64": image_b64,
            "image_format": fmt,
            "figure_size": params["figure_size"],
            "dpi": params["dpi"],
        }

    def _run_line_plot(self, params):
        fig, ax = self._create_figure(params)
        datasets = params.get("datasets", [])
        colors = ['#6366f1', '#22c55e', '#f59e0b', '#ef4444', '#06b6d4', '#ec4899', '#a855f7', '#14b8a6']

        for i, ds in enumerate(datasets):
            x = ds.get("x", [])
            y = ds.get("y", [])
            label = ds.get("label", f"Series {i+1}")
            color = ds.get("color", colors[i % len(colors)])
            marker = ds.get("marker", None)
            ax.plot(x, y, label=label, color=color, marker=marker, linewidth=2)

        if datasets:
            ax.legend()
        return self._finalize(fig, ax, params)

    def _run_scatter_plot(self, params):
        fig, ax = self._create_figure(params)
        datasets = params.get("datasets", [])
        colors = ['#6366f1', '#22c55e', '#f59e0b', '#ef4444', '#06b6d4', '#ec4899']

        for i, ds in enumerate(datasets):
            x = ds.get("x", [])
            y = ds.get("y", [])
            label = ds.get("label", f"Series {i+1}")
            color = ds.get("color", colors[i % len(colors)])
            marker = ds.get("marker", "o")
            ax.scatter(x, y, label=label, color=color, marker=marker, alpha=0.7)

        if datasets:
            ax.legend()
        return self._finalize(fig, ax, params)

    def _run_histogram(self, params):
        fig, ax = self._create_figure(params)
        data = params.get("data", [])
        bins = params.get("bins", 30)
        density = params.get("density", False)

        ax.hist(data, bins=bins, density=density, color='#6366f1', edgecolor='#4338ca', alpha=0.8)
        return self._finalize(fig, ax, params)

    def _run_heatmap(self, params):
        fig, ax = self._create_figure(params)
        z_data = np.array(params.get("z_data", [[]]))
        x_data = params.get("x_data", None)
        y_data = params.get("y_data", None)
        colormap = params.get("colormap", "viridis")

        if x_data and y_data:
            im = ax.pcolormesh(x_data, y_data, z_data, cmap=colormap, shading='auto')
        else:
            im = ax.imshow(z_data, cmap=colormap, aspect='auto', origin='lower')
        fig.colorbar(im, ax=ax)
        return self._finalize(fig, ax, params)

    def _run_contour_plot(self, params):
        fig, ax = self._create_figure(params)
        z_data = np.array(params.get("z_data", [[]]))
        x_data = params.get("x_data", None)
        y_data = params.get("y_data", None)
        colormap = params.get("colormap", "viridis")

        if x_data and y_data:
            X, Y = np.meshgrid(x_data, y_data)
            cs = ax.contourf(X, Y, z_data, levels=20, cmap=colormap)
        else:
            cs = ax.contourf(z_data, levels=20, cmap=colormap)
        fig.colorbar(cs, ax=ax)
        return self._finalize(fig, ax, params)

    def _run_bar_chart(self, params):
        fig, ax = self._create_figure(params)
        categories = params.get("categories", [])
        values = params.get("values", [])
        colors = params.get("colors", None)

        if not colors:
            colors = '#6366f1'
        ax.bar(categories, values, color=colors, edgecolor='#4338ca', alpha=0.8)
        ax.set_xticklabels(categories, rotation=45, ha='right')
        return self._finalize(fig, ax, params)

    def get_default_params(self) -> dict[str, Any]:
        return {
            "simulation_type": "line_plot",
            "title": "Sine Wave",
            "xlabel": "x",
            "ylabel": "y",
            "style": "seaborn-v0_8-darkgrid",
            "figure_size": [8, 6],
            "dpi": 150,
            "output_format": "png",
            "datasets": [{"x": list(np.linspace(0, 6.28, 100).tolist()),
                          "y": list(np.sin(np.linspace(0, 6.28, 100)).tolist()),
                          "label": "sin(x)"}],
        }


@celery_app.task(name="tools.matplotlib_tool.run_matplotlib", bind=True)
def run_matplotlib(self, params: dict, project: str = "_default",
                   label: str | None = None) -> dict:
    tool = MatplotlibTool()

    self.update_state(state="PROGRESS", meta={"progress": 0.0, "message": "Starting Matplotlib rendering"})

    try:
        sim_type = params.get("simulation_type", "line_plot")
        self.update_state(state="PROGRESS", meta={"progress": 0.1, "message": f"Rendering {sim_type}"})
        result = tool.run(params)
    except Exception as e:
        self.update_state(state="FAILURE", meta={"message": str(e)})
        raise

    self.update_state(state="PROGRESS", meta={"progress": 0.9, "message": "Saving results"})
    save_result(self.request.id, "matplotlib", result, project, label)

    return result
