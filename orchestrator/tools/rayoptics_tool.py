"""RayOptics tool — geometrical ray tracing through optical systems."""

from typing import Any

import numpy as np
from celery_app import app as celery_app
from tools.base import SimulationTool
from results import save_result

# Glass catalog: name → (n_d, V_d) for common optical glasses
GLASS_CATALOG = {
    "N-BK7": (1.5168, 64.17),
    "N-SF2": (1.6477, 33.82),
    "N-SF11": (1.7847, 25.76),
    "N-LAK9": (1.6910, 54.71),
    "N-SK16": (1.6204, 60.32),
    "F2": (1.6200, 36.37),
    "SF6": (1.8052, 25.43),
    "BK7": (1.5168, 64.17),
}


def _glass_to_numeric(glass):
    """Convert a glass name to [n_d, V_d] or pass through numeric values."""
    if isinstance(glass, str):
        key = glass.upper().replace(" ", "")
        if key in GLASS_CATALOG:
            return list(GLASS_CATALOG[key])
        return [1.5168, 64.17]  # fallback to N-BK7
    return glass


def _build_model(pupil_d, wlwts, ref_wl=0):
    """Create an OpticalModel with correct API settings."""
    from rayoptics.environment import OpticalModel
    from rayoptics.raytr.opticalspec import PupilSpec, FieldSpec, WvlSpec

    opm = OpticalModel()
    opm.radius_mode = True  # interpret add_surface values as radii

    osp = opm.optical_spec
    osp.pupil = PupilSpec(osp, key=('object', 'epd'), value=pupil_d)
    osp.field_of_view = FieldSpec(osp, key=('object', 'angle'), value=[0.0])
    osp.spectral_region = WvlSpec(wlwts=wlwts, ref_wl=ref_wl)

    opm.seq_model.gaps[0].thi = 1e10  # object at infinity
    return opm


class RayOpticsTool(SimulationTool):
    name = "RayOptics"
    key = "rayoptics"
    layer = "optics"

    def validate_params(self, params: dict[str, Any]) -> dict[str, Any]:
        sim_type = params.get("simulation_type")
        if sim_type not in ("singlet_lens", "doublet", "spot_diagram"):
            raise ValueError("simulation_type must be one of: singlet_lens, doublet, spot_diagram")
        return params

    def run(self, params: dict[str, Any]) -> dict[str, Any]:
        params = self.validate_params(params)
        sim_type = params["simulation_type"]

        if sim_type == "singlet_lens":
            return self._run_singlet(params.get("singlet_lens", {}))
        elif sim_type == "doublet":
            return self._run_doublet(params.get("doublet", {}))
        elif sim_type == "spot_diagram":
            return self._run_spot_diagram(params.get("spot_diagram", {}))

    def _run_singlet(self, p: dict) -> dict[str, Any]:
        from rayoptics.raytr.trace import trace_base

        efl = p.get("efl", 100.0)
        fD = p.get("f_number", 5.0)
        wvl = p.get("wavelength", 587.56)
        pupil_d = efl / fD
        n_rays = int(p.get("n_rays", 21))

        opm = _build_model(pupil_d, [(wvl, 1.0)], ref_wl=0)
        sm = opm.seq_model
        osp = opm.optical_spec

        r1 = p.get("r1", efl * 0.9)
        r2 = p.get("r2", -efl * 0.9)
        thickness = p.get("thickness", 6.0)
        glass = p.get("glass", "N-BK7")
        nd, vd = _glass_to_numeric(glass) if isinstance(glass, str) else (glass, 64.17)

        sm.add_surface([r1, thickness, nd, vd])
        sm.add_surface([r2, efl - thickness / 2])
        opm.update_model()

        fld = osp.field_of_view.fields[0]
        wvl_val = osp.spectral_region.central_wvl

        ray_data = []
        for y_frac in np.linspace(-1, 1, n_rays):
            try:
                ray_pkg = trace_base(opm, [0.0, y_frac], fld, wvl_val)
                ray = ray_pkg[0]
                heights = [float(seg[0][1]) for seg in ray]
                positions = [float(seg[0][2]) for seg in ray]
                ray_data.append({"y_frac": float(y_frac), "heights": heights, "z_positions": positions})
            except Exception:
                continue

        surfaces = []
        for i, ifc in enumerate(sm.ifcs):
            surfaces.append({
                "index": i,
                "curvature": float(ifc.profile.cv) if hasattr(ifc, 'profile') else 0.0,
                "thickness": float(sm.gaps[i].thi) if i < len(sm.gaps) else 0.0,
            })

        return {
            "tool": "rayoptics",
            "simulation_type": "singlet_lens",
            "efl": efl,
            "f_number": fD,
            "wavelength": wvl,
            "n_rays": n_rays,
            "surfaces": surfaces,
            "rays": ray_data,
            "params": p,
        }

    def _run_doublet(self, p: dict) -> dict[str, Any]:
        from rayoptics.raytr.trace import trace_base

        efl = p.get("efl", 200.0)
        fD = p.get("f_number", 8.0)
        pupil_d = efl / fD
        n_rays = int(p.get("n_rays", 21))

        opm = _build_model(
            pupil_d,
            [(486.13, 0.5), (587.56, 1.0), (656.27, 0.5)],
            ref_wl=1,
        )
        sm = opm.seq_model
        osp = opm.optical_spec

        g1 = _glass_to_numeric(p.get("glass1", "N-BK7"))
        g2 = _glass_to_numeric(p.get("glass2", "N-SF2"))

        sm.add_surface([p.get("r1", 120.0), p.get("t1", 8.0), g1[0], g1[1]])
        sm.add_surface([p.get("r2", -80.0), p.get("t2", 3.0), g2[0], g2[1]])
        sm.add_surface([p.get("r3", -250.0), efl * 0.95])
        opm.update_model()

        fld = osp.field_of_view.fields[0]
        wvls = osp.spectral_region.wavelengths

        ray_data = []
        for wvl_val in wvls:
            for y_frac in np.linspace(-1, 1, n_rays):
                try:
                    ray_pkg = trace_base(opm, [0.0, y_frac], fld, wvl_val)
                    ray = ray_pkg[0]
                    heights = [float(seg[0][1]) for seg in ray]
                    positions = [float(seg[0][2]) for seg in ray]
                    ray_data.append({
                        "y_frac": float(y_frac),
                        "wavelength": float(wvl_val),
                        "heights": heights,
                        "z_positions": positions,
                    })
                except Exception:
                    continue

        return {
            "tool": "rayoptics",
            "simulation_type": "doublet",
            "efl": efl,
            "f_number": fD,
            "n_rays": n_rays,
            "wavelengths": [float(w) for w in wvls],
            "rays": ray_data,
            "params": p,
        }

    def _run_spot_diagram(self, p: dict) -> dict[str, Any]:
        from rayoptics.raytr.trace import trace_base

        efl = p.get("efl", 100.0)
        fD = p.get("f_number", 5.0)
        pupil_d = efl / fD
        n_rings = int(p.get("n_rings", 6))
        n_arms = int(p.get("n_arms", 6))

        opm = _build_model(pupil_d, [(587.56, 1.0)], ref_wl=0)
        sm = opm.seq_model
        osp = opm.optical_spec

        r1 = p.get("r1", efl * 0.9)
        r2 = p.get("r2", -efl * 0.9)
        thickness = p.get("thickness", 6.0)
        glass = p.get("glass", "N-BK7")
        nd, vd = _glass_to_numeric(glass) if isinstance(glass, str) else (glass, 64.17)

        sm.add_surface([r1, thickness, nd, vd])
        sm.add_surface([r2, efl - thickness / 2])
        opm.update_model()

        fld = osp.field_of_view.fields[0]
        wvl_val = osp.spectral_region.central_wvl

        x_spots = []
        y_spots = []
        for ring in range(1, n_rings + 1):
            rho = ring / n_rings
            for arm in range(n_arms):
                theta = 2 * np.pi * arm / n_arms
                px = rho * np.cos(theta)
                py = rho * np.sin(theta)
                try:
                    ray_pkg = trace_base(opm, [px, py], fld, wvl_val)
                    ray = ray_pkg[0]
                    x_spots.append(float(ray[-1][0][0]))
                    y_spots.append(float(ray[-1][0][1]))
                except Exception:
                    continue

        rms_radius = float(np.sqrt(np.mean(np.array(x_spots) ** 2 + np.array(y_spots) ** 2))) if x_spots else 0.0

        return {
            "tool": "rayoptics",
            "simulation_type": "spot_diagram",
            "efl": efl,
            "f_number": fD,
            "n_rings": n_rings,
            "n_arms": n_arms,
            "x_spots": x_spots,
            "y_spots": y_spots,
            "rms_radius_mm": rms_radius,
            "params": p,
        }

    def get_default_params(self) -> dict[str, Any]:
        return {
            "simulation_type": "singlet_lens",
            "singlet_lens": {
                "efl": 100.0,
                "f_number": 5.0,
                "wavelength": 587.56,
                "n_rays": 21,
            },
        }


@celery_app.task(name="tools.rayoptics_tool.run_rayoptics", bind=True)
def run_rayoptics(self, params: dict, project: str = "_default",
                  label: str | None = None) -> dict:
    tool = RayOpticsTool()
    self.update_state(state="PROGRESS", meta={"progress": 0.0, "message": "Starting RayOptics simulation"})

    try:
        result = tool.run(params)
    except Exception as e:
        raise

    self.update_state(state="PROGRESS", meta={"progress": 0.9, "message": "Saving results"})
    save_result(self.request.id, "rayoptics", result, project, label)
    return result
