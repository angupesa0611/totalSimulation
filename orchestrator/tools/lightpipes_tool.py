"""LightPipes tool — physical wave optics simulation."""

from typing import Any

import numpy as np
from celery_app import app as celery_app
from tools.base import SimulationTool
from results import save_result


class LightPipesTool(SimulationTool):
    name = "LightPipes"
    key = "lightpipes"
    layer = "optics"

    def validate_params(self, params: dict[str, Any]) -> dict[str, Any]:
        sim_type = params.get("simulation_type")
        valid = ("double_slit", "circular_aperture", "lens_focus", "interferometer")
        if sim_type not in valid:
            raise ValueError(f"simulation_type must be one of: {valid}")
        return params

    def run(self, params: dict[str, Any]) -> dict[str, Any]:
        params = self.validate_params(params)
        sim_type = params["simulation_type"]

        if sim_type == "double_slit":
            return self._run_double_slit(params.get("double_slit", {}))
        elif sim_type == "circular_aperture":
            return self._run_circular_aperture(params.get("circular_aperture", {}))
        elif sim_type == "lens_focus":
            return self._run_lens_focus(params.get("lens_focus", {}))
        elif sim_type == "interferometer":
            return self._run_interferometer(params.get("interferometer", {}))

    def _run_double_slit(self, p: dict) -> dict[str, Any]:
        import LightPipes as lp

        wavelength = p.get("wavelength", 532e-9)  # m
        grid_size = p.get("grid_size", 10e-3)  # m
        N = int(p.get("grid_points", 512))
        slit_width = p.get("slit_width", 0.1e-3)  # m
        slit_sep = p.get("slit_separation", 0.2e-3)  # m
        prop_dist = p.get("propagation_distance", 1.0)  # m

        F = lp.Begin(grid_size, wavelength, N)

        # Create double slit via rectangular apertures
        F1 = lp.RectAperture(F, slit_width, grid_size, -slit_sep / 2, 0)
        F2 = lp.RectAperture(F, slit_width, grid_size, slit_sep / 2, 0)
        F = lp.BeamMix(F1, F2)

        F = lp.Fresnel(F, prop_dist)

        intensity = np.abs(lp.Field2D(F)) ** 2 if hasattr(lp, 'Field2D') else lp.Intensity(F, 0)
        if isinstance(intensity, (list, tuple)):
            intensity = np.array(intensity)
        intensity = intensity.tolist() if hasattr(intensity, 'tolist') else intensity

        return {
            "tool": "lightpipes",
            "simulation_type": "double_slit",
            "wavelength_nm": wavelength * 1e9,
            "grid_size_mm": grid_size * 1e3,
            "grid_points": N,
            "slit_width_mm": slit_width * 1e3,
            "slit_separation_mm": slit_sep * 1e3,
            "propagation_distance_m": prop_dist,
            "intensity": intensity,
            "x_mm": np.linspace(-grid_size / 2 * 1e3, grid_size / 2 * 1e3, N).tolist(),
            "params": p,
        }

    def _run_circular_aperture(self, p: dict) -> dict[str, Any]:
        import LightPipes as lp

        wavelength = p.get("wavelength", 632.8e-9)
        grid_size = p.get("grid_size", 10e-3)
        N = int(p.get("grid_points", 512))
        aperture_radius = p.get("aperture_radius", 0.5e-3)
        prop_dist = p.get("propagation_distance", 2.0)

        F = lp.Begin(grid_size, wavelength, N)
        F = lp.CircAperture(F, aperture_radius)
        F = lp.Fresnel(F, prop_dist)

        intensity = lp.Intensity(F, 0)
        if isinstance(intensity, (list, tuple)):
            intensity = np.array(intensity)
        intensity = intensity.tolist() if hasattr(intensity, 'tolist') else intensity

        return {
            "tool": "lightpipes",
            "simulation_type": "circular_aperture",
            "wavelength_nm": wavelength * 1e9,
            "aperture_radius_mm": aperture_radius * 1e3,
            "propagation_distance_m": prop_dist,
            "intensity": intensity,
            "x_mm": np.linspace(-grid_size / 2 * 1e3, grid_size / 2 * 1e3, N).tolist(),
            "params": p,
        }

    def _run_lens_focus(self, p: dict) -> dict[str, Any]:
        import LightPipes as lp

        wavelength = p.get("wavelength", 532e-9)
        grid_size = p.get("grid_size", 10e-3)
        N = int(p.get("grid_points", 512))
        focal_length = p.get("focal_length", 0.5)
        beam_radius = p.get("beam_radius", 2e-3)

        F = lp.Begin(grid_size, wavelength, N)
        F = lp.CircAperture(F, beam_radius)
        F = lp.Lens(F, focal_length)
        F = lp.Fresnel(F, focal_length)

        intensity = lp.Intensity(F, 0)
        if isinstance(intensity, (list, tuple)):
            intensity = np.array(intensity)
        intensity = intensity.tolist() if hasattr(intensity, 'tolist') else intensity

        return {
            "tool": "lightpipes",
            "simulation_type": "lens_focus",
            "wavelength_nm": wavelength * 1e9,
            "focal_length_m": focal_length,
            "beam_radius_mm": beam_radius * 1e3,
            "intensity": intensity,
            "x_mm": np.linspace(-grid_size / 2 * 1e3, grid_size / 2 * 1e3, N).tolist(),
            "params": p,
        }

    def _run_interferometer(self, p: dict) -> dict[str, Any]:
        import LightPipes as lp

        wavelength = p.get("wavelength", 632.8e-9)
        grid_size = p.get("grid_size", 10e-3)
        N = int(p.get("grid_points", 512))
        tilt_angle = p.get("tilt_angle", 0.001)  # rad

        # Mach-Zehnder: split, tilt one arm, recombine
        F = lp.Begin(grid_size, wavelength, N)
        F1 = lp.Field2D(F) if hasattr(lp, 'Field2D') else F
        F2 = lp.Tilt(F, tilt_angle, 0)

        F_out = lp.BeamMix(F, F2)
        intensity = lp.Intensity(F_out, 0)
        if isinstance(intensity, (list, tuple)):
            intensity = np.array(intensity)
        intensity = intensity.tolist() if hasattr(intensity, 'tolist') else intensity

        return {
            "tool": "lightpipes",
            "simulation_type": "interferometer",
            "wavelength_nm": wavelength * 1e9,
            "tilt_angle_mrad": tilt_angle * 1e3,
            "intensity": intensity,
            "x_mm": np.linspace(-grid_size / 2 * 1e3, grid_size / 2 * 1e3, N).tolist(),
            "params": p,
        }

    def get_default_params(self) -> dict[str, Any]:
        return {
            "simulation_type": "double_slit",
            "double_slit": {
                "wavelength": 532e-9,
                "grid_size": 10e-3,
                "grid_points": 512,
                "slit_width": 0.1e-3,
                "slit_separation": 0.2e-3,
                "propagation_distance": 1.0,
            },
        }


@celery_app.task(name="tools.lightpipes_tool.run_lightpipes", bind=True)
def run_lightpipes(self, params: dict, project: str = "_default",
                   label: str | None = None) -> dict:
    tool = LightPipesTool()
    self.update_state(state="PROGRESS", meta={"progress": 0.0, "message": "Starting LightPipes simulation"})

    try:
        result = tool.run(params)
    except Exception as e:
        raise

    self.update_state(state="PROGRESS", meta={"progress": 0.9, "message": "Saving results"})
    save_result(self.request.id, "lightpipes", result, project, label)
    return result
