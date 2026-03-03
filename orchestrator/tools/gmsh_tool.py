import os
from typing import Any
import numpy as np
from celery_app import app as celery_app
from tools.base import SimulationTool
from results import save_result
from config import settings


class GmshTool(SimulationTool):
    name = "Gmsh"
    key = "gmsh"
    layer = "mathematics"

    SIMULATION_TYPES = {"box_mesh", "cylinder_mesh", "sphere_mesh", "custom_geo"}

    def validate_params(self, params: dict[str, Any]) -> dict[str, Any]:
        sim_type = params.get("simulation_type", "box_mesh")
        if sim_type not in self.SIMULATION_TYPES:
            raise ValueError(f"Unknown simulation_type: {sim_type}. Supported: {self.SIMULATION_TYPES}")

        params.setdefault("simulation_type", sim_type)
        params.setdefault("mesh_size", 0.1)
        params.setdefault("dimension", 3)
        params.setdefault("element_order", 1)
        params.setdefault("output_format", "msh")
        return params

    def run(self, params: dict[str, Any]) -> dict[str, Any]:
        params = self.validate_params(params)
        sim_type = params["simulation_type"]

        if sim_type == "box_mesh":
            return self._run_box_mesh(params)
        elif sim_type == "cylinder_mesh":
            return self._run_cylinder_mesh(params)
        elif sim_type == "sphere_mesh":
            return self._run_sphere_mesh(params)
        elif sim_type == "custom_geo":
            return self._run_custom_geo(params)

    def _init_gmsh(self):
        import gmsh
        if gmsh.isInitialized():
            gmsh.finalize()
        gmsh.initialize()
        gmsh.option.setNumber("General.Terminal", 0)
        return gmsh

    def _extract_mesh_data(self, gmsh_mod, dim, max_nodes=2000, max_elements=2000):
        """Extract mesh data from Gmsh model, downsampled for JSON output."""
        import gmsh

        node_tags, node_coords, _ = gmsh_mod.mesh.getNodes()
        n_nodes = len(node_tags)

        # Reshape coordinates to (N, 3)
        coords = np.array(node_coords).reshape(-1, 3)

        # Get elements
        elem_types, elem_tags, elem_node_tags = gmsh_mod.mesh.getElements(dim)

        n_elements = sum(len(tags) for tags in elem_tags)

        # Downsample nodes for output
        step_n = max(1, n_nodes // max_nodes)
        nodes_out = []
        for i in range(0, n_nodes, step_n):
            nodes_out.append({
                "id": int(node_tags[i]),
                "x": float(coords[i, 0]),
                "y": float(coords[i, 1]),
                "z": float(coords[i, 2]),
            })

        # Downsample elements
        elements_out = []
        elem_count = 0
        for etype, etags, enodes in zip(elem_types, elem_tags, elem_node_tags):
            props = gmsh_mod.mesh.getElementProperties(etype)
            etype_name = props[0]
            nodes_per_elem = props[3]
            for j in range(len(etags)):
                if elem_count % max(1, n_elements // max_elements) == 0:
                    start = j * nodes_per_elem
                    end = start + nodes_per_elem
                    elements_out.append({
                        "id": int(etags[j]),
                        "type": etype_name,
                        "node_ids": [int(n) for n in enodes[start:end]],
                    })
                elem_count += 1

        # Compute bounds
        bounds = {
            "min": [float(coords[:, 0].min()), float(coords[:, 1].min()), float(coords[:, 2].min())],
            "max": [float(coords[:, 0].max()), float(coords[:, 1].max()), float(coords[:, 2].max())],
        }

        # Mesh quality
        quality = []
        for etype in elem_types:
            gmsh_mod.mesh.setOrder(1)  # ensure quality is computed on linear mesh
            try:
                q = gmsh_mod.mesh.getElementQualities(list(range(1, n_elements + 1)), "minSICN")
                quality.extend(q)
            except Exception:
                pass

        mesh_quality = {}
        if quality:
            q_arr = np.array(quality)
            q_arr = q_arr[np.isfinite(q_arr)]
            if len(q_arr) > 0:
                mesh_quality = {
                    "min_quality": float(q_arr.min()),
                    "avg_quality": float(q_arr.mean()),
                }

        # Determine element type name
        elem_type_name = "unknown"
        if elem_types:
            props = gmsh_mod.mesh.getElementProperties(elem_types[0])
            elem_type_name = props[0]

        return {
            "n_nodes": n_nodes,
            "n_elements": n_elements,
            "dimension": dim,
            "element_type": elem_type_name,
            "nodes": nodes_out,
            "elements": elements_out,
            "bounds": bounds,
            "mesh_quality": mesh_quality,
        }

    def _export_msh(self, gmsh_mod, job_id):
        """Save .msh file for FEniCS coupling."""
        import gmsh

        results_dir = os.path.join(settings.results_dir, "_default")
        os.makedirs(results_dir, exist_ok=True)
        mesh_path = os.path.join(results_dir, f"{job_id}.msh")
        gmsh_mod.write(mesh_path)
        return mesh_path

    def _run_box_mesh(self, params):
        import gmsh

        g = self._init_gmsh()

        lx = params.get("lx", 1.0)
        ly = params.get("ly", 1.0)
        lz = params.get("lz", 0.0)
        mesh_size = params["mesh_size"]
        dim = params["dimension"]

        if dim == 2 or lz == 0:
            # 2D rectangle
            gmsh.model.occ.addRectangle(0, 0, 0, lx, ly)
            gmsh.model.occ.synchronize()
            gmsh.option.setNumber("Mesh.CharacteristicLengthMax", mesh_size)
            gmsh.model.mesh.generate(2)
            mesh_dim = 2
        else:
            # 3D box
            gmsh.model.occ.addBox(0, 0, 0, lx, ly, lz)
            gmsh.model.occ.synchronize()
            gmsh.option.setNumber("Mesh.CharacteristicLengthMax", mesh_size)
            gmsh.model.mesh.generate(3)
            mesh_dim = 3

        if params["element_order"] > 1:
            gmsh.model.mesh.setOrder(params["element_order"])

        result = self._extract_mesh_data(gmsh.model, mesh_dim)
        result["tool"] = "gmsh"
        result["simulation_type"] = "box_mesh"
        result["mesh_file_path"] = ""

        gmsh.finalize()
        return result

    def _run_cylinder_mesh(self, params):
        import gmsh

        g = self._init_gmsh()

        radius = params.get("radius", 0.5)
        length = params.get("length", 2.0)
        mesh_size = params["mesh_size"]

        gmsh.model.occ.addCylinder(0, 0, 0, length, 0, 0, radius)
        gmsh.model.occ.synchronize()
        gmsh.option.setNumber("Mesh.CharacteristicLengthMax", mesh_size)
        gmsh.model.mesh.generate(3)

        if params["element_order"] > 1:
            gmsh.model.mesh.setOrder(params["element_order"])

        result = self._extract_mesh_data(gmsh.model, 3)
        result["tool"] = "gmsh"
        result["simulation_type"] = "cylinder_mesh"
        result["mesh_file_path"] = ""

        gmsh.finalize()
        return result

    def _run_sphere_mesh(self, params):
        import gmsh

        g = self._init_gmsh()

        radius = params.get("radius", 1.0)
        mesh_size = params["mesh_size"]

        gmsh.model.occ.addSphere(0, 0, 0, radius)
        gmsh.model.occ.synchronize()
        gmsh.option.setNumber("Mesh.CharacteristicLengthMax", mesh_size)
        gmsh.model.mesh.generate(3)

        if params["element_order"] > 1:
            gmsh.model.mesh.setOrder(params["element_order"])

        result = self._extract_mesh_data(gmsh.model, 3)
        result["tool"] = "gmsh"
        result["simulation_type"] = "sphere_mesh"
        result["mesh_file_path"] = ""

        gmsh.finalize()
        return result

    def _run_custom_geo(self, params):
        import gmsh
        import tempfile

        g = self._init_gmsh()

        geo_script = params.get("geo_script", "")
        if not geo_script:
            raise ValueError("geo_script is required for custom_geo simulation type")

        dim = params.get("dimension", 3)

        # Write geo script to temp file and load
        with tempfile.NamedTemporaryFile(mode="w", suffix=".geo", delete=False) as f:
            f.write(geo_script)
            f.flush()
            gmsh.open(f.name)

        os.unlink(f.name)

        gmsh.model.mesh.generate(dim)

        if params["element_order"] > 1:
            gmsh.model.mesh.setOrder(params["element_order"])

        result = self._extract_mesh_data(gmsh.model, dim)
        result["tool"] = "gmsh"
        result["simulation_type"] = "custom_geo"
        result["mesh_file_path"] = ""

        gmsh.finalize()
        return result

    def get_default_params(self) -> dict[str, Any]:
        return {
            "simulation_type": "box_mesh",
            "lx": 1.0,
            "ly": 0.5,
            "lz": 0.2,
            "mesh_size": 0.05,
            "dimension": 3,
            "element_order": 1,
            "output_format": "msh",
        }


@celery_app.task(name="tools.gmsh_tool.run_gmsh", bind=True)
def run_gmsh(self, params: dict, project: str = "_default",
             label: str | None = None) -> dict:
    tool = GmshTool()

    self.update_state(state="PROGRESS", meta={"progress": 0.0, "message": "Starting Gmsh mesh generation"})

    try:
        sim_type = params.get("simulation_type", "box_mesh")
        self.update_state(state="PROGRESS", meta={"progress": 0.1, "message": f"Generating {sim_type}"})
        result = tool.run(params)
    except Exception as e:
        self.update_state(state="FAILURE", meta={"message": str(e)})
        raise

    # Export .msh file for FEniCS coupling
    self.update_state(state="PROGRESS", meta={"progress": 0.8, "message": "Exporting mesh file"})
    try:
        mesh_path = tool._export_msh(None, self.request.id)
        result["mesh_file_path"] = mesh_path
    except Exception:
        pass

    self.update_state(state="PROGRESS", meta={"progress": 0.9, "message": "Saving results"})
    save_result(self.request.id, "gmsh", result, project, label)

    return result
