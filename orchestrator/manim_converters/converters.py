"""All Manim converters — maps tool results to scene params.

Each converter class converts one tool's output format into params
compatible with a Manim scene generator. Converters are pure JSON->JSON
transforms that run in the orchestrator.
"""

from manim_converters import register_converter
from manim_converters.base import ManimConverter


# ---------------------------------------------------------------------------
# Astrophysics / GR
# ---------------------------------------------------------------------------

@register_converter("rebound")
class ReboundConverter(ManimConverter):
    def supported_scenes(self):
        return [
            {"scene_type": "orbital_animation", "label": "Orbital Animation", "description": "2D/3D orbit trails with planet markers"},
            {"scene_type": "precession_diagram", "label": "Precession Diagram", "description": "Precessing ellipse with arcsec annotation"},
        ]

    def convert(self, result, scene_type, options=None):
        if scene_type == "orbital_animation":
            positions = result.get("positions", {})
            names = result.get("names", list(positions.keys()))
            return {
                "simulation_type": "orbital_animation",
                "positions": positions,
                "names": names,
                "title": result.get("label", "N-Body Orbits"),
                "n_frames": 100,
            }
        elif scene_type == "precession_diagram":
            return {
                "simulation_type": "precession_diagram",
                "semi_major": result.get("semi_major", 1.0),
                "eccentricity": result.get("eccentricity", 0.2),
                "total_precession_arcsec": result.get("total_precession_arcsec", 43.0),
                "n_orbits": 5,
                "title": "Orbital Precession",
            }
        return {"simulation_type": scene_type}


@register_converter("einsteinpy")
class EinsteinPyConverter(ManimConverter):
    def supported_scenes(self):
        return [
            {"scene_type": "geodesic_visualization", "label": "Geodesic Paths", "description": "Geodesic paths on spacetime embedding"},
        ]

    def convert(self, result, scene_type, options=None):
        return {
            "simulation_type": "geodesic_visualization",
            "trajectories": result.get("trajectories", []),
            "metric_name": result.get("metric", "Schwarzschild"),
            "title": result.get("label", "Geodesics"),
        }


@register_converter("nrpy")
class NRPyConverter(ManimConverter):
    def supported_scenes(self):
        return [
            {"scene_type": "gravitational_wave_strain", "label": "GW Strain", "description": "Animated h+/hx strain waveform"},
        ]

    def convert(self, result, scene_type, options=None):
        return {
            "simulation_type": "gravitational_wave_strain",
            "times": result.get("times", []),
            "h_plus": result.get("h_plus", []),
            "h_cross": result.get("h_cross", []),
            "title": "Gravitational Wave Strain",
        }


@register_converter("einstein_toolkit")
class EinsteinToolkitConverter(ManimConverter):
    def supported_scenes(self):
        return [
            {"scene_type": "gravitational_wave_strain", "label": "GW Strain", "description": "Gravitational wave strain from NR"},
        ]

    def convert(self, result, scene_type, options=None):
        return {
            "simulation_type": "gravitational_wave_strain",
            "times": result.get("times", []),
            "h_plus": result.get("h_plus", result.get("strain_plus", [])),
            "h_cross": result.get("h_cross", result.get("strain_cross", [])),
            "title": "Einstein Toolkit — GW Strain",
        }


# ---------------------------------------------------------------------------
# Quantum
# ---------------------------------------------------------------------------

@register_converter("qutip")
class QutipConverter(ManimConverter):
    def supported_scenes(self):
        return [
            {"scene_type": "bloch_sphere", "label": "Bloch Sphere", "description": "Bloch sphere trajectory"},
            {"scene_type": "expectation_animation", "label": "Expectation Values", "description": "Animated expectation value time series"},
            {"scene_type": "energy_spectrum", "label": "Energy Spectrum", "description": "Energy level diagram"},
        ]

    def default_scene(self, result):
        if result.get("bloch") or result.get("system_type") == "qubit_rabi":
            return "bloch_sphere"
        return "expectation_animation"

    def convert(self, result, scene_type, options=None):
        if scene_type == "bloch_sphere":
            bloch = result.get("bloch", {})
            return {
                "simulation_type": "bloch_sphere",
                "trajectory_x": bloch.get("x", [0.0]),
                "trajectory_y": bloch.get("y", [0.0]),
                "trajectory_z": bloch.get("z", [1.0]),
            }
        elif scene_type == "expectation_animation":
            return {
                "simulation_type": "expectation_animation",
                "times": result.get("times", []),
                "expect_values": result.get("expect", {}),
                "labels": result.get("expect_labels", []),
                "title": "Quantum Expectation Values",
            }
        elif scene_type == "energy_spectrum":
            return {
                "simulation_type": "energy_spectrum",
                "energy_levels": result.get("eigenvalues", result.get("energy_levels", [])),
                "level_labels": result.get("level_labels", []),
                "transitions": result.get("transitions", []),
                "title": "Energy Spectrum",
            }
        return {"simulation_type": scene_type}


@register_converter("pyscf")
class PySCFConverter(ManimConverter):
    def supported_scenes(self):
        return [
            {"scene_type": "energy_spectrum", "label": "Energy Levels", "description": "Orbital energy level diagram"},
        ]

    def convert(self, result, scene_type, options=None):
        return {
            "simulation_type": "energy_spectrum",
            "energy_levels": result.get("orbital_energies", result.get("eigenvalues", [])),
            "level_labels": result.get("orbital_labels", []),
            "title": "Orbital Energy Levels",
        }


# ---------------------------------------------------------------------------
# Molecular dynamics
# ---------------------------------------------------------------------------

@register_converter("openmm")
class OpenMMConverter(ManimConverter):
    def supported_scenes(self):
        return [
            {"scene_type": "energy_evolution", "label": "Energy Plot", "description": "KE, PE, Total energy over time"},
            {"scene_type": "molecular_trajectory", "label": "Trajectory", "description": "Animated atom positions"},
        ]

    def convert(self, result, scene_type, options=None):
        if scene_type == "energy_evolution":
            return {
                "simulation_type": "energy_evolution",
                "times": result.get("times", []),
                "kinetic_energy": result.get("kinetic_energy", []),
                "potential_energy": result.get("potential_energy", []),
                "total_energy": result.get("total_energy", []),
                "title": "OpenMM Energy Evolution",
            }
        elif scene_type == "molecular_trajectory":
            return {
                "simulation_type": "molecular_trajectory",
                "frames": result.get("frames", result.get("trajectory", [])),
                "title": "Molecular Trajectory",
            }
        return {"simulation_type": scene_type}


@register_converter("gromacs")
class GromacsConverter(ManimConverter):
    def supported_scenes(self):
        return [
            {"scene_type": "energy_evolution", "label": "Energy Plot", "description": "Energy evolution from GROMACS"},
            {"scene_type": "molecular_trajectory", "label": "Trajectory", "description": "MD trajectory animation"},
        ]

    def convert(self, result, scene_type, options=None):
        if scene_type == "energy_evolution":
            return {
                "simulation_type": "energy_evolution",
                "times": result.get("times", []),
                "kinetic_energy": result.get("kinetic_energy", []),
                "potential_energy": result.get("potential_energy", []),
                "total_energy": result.get("total_energy", []),
                "title": "GROMACS Energy Evolution",
            }
        return {
            "simulation_type": "molecular_trajectory",
            "frames": result.get("frames", []),
            "title": "GROMACS Trajectory",
        }


@register_converter("namd")
class NAMDConverter(ManimConverter):
    def supported_scenes(self):
        return [
            {"scene_type": "energy_evolution", "label": "Energy Plot", "description": "Energy evolution from NAMD"},
        ]

    def convert(self, result, scene_type, options=None):
        return {
            "simulation_type": "energy_evolution",
            "times": result.get("times", []),
            "kinetic_energy": result.get("kinetic_energy", []),
            "potential_energy": result.get("potential_energy", []),
            "total_energy": result.get("total_energy", []),
            "title": "NAMD Energy Evolution",
        }


@register_converter("mdanalysis")
class MDAnalysisConverter(ManimConverter):
    def supported_scenes(self):
        return [
            {"scene_type": "contact_map_animation", "label": "Contact Map", "description": "Animated residue contact map"},
        ]

    def convert(self, result, scene_type, options=None):
        return {
            "simulation_type": "contact_map_animation",
            "contact_matrices": result.get("contact_matrices", result.get("contact_map", [])),
            "residue_labels": result.get("residue_labels", []),
            "title": "Contact Map",
        }


@register_converter("qmmm")
class QMMMConverter(ManimConverter):
    def supported_scenes(self):
        return [
            {"scene_type": "energy_evolution", "label": "Energy Plot", "description": "QM/MM energy evolution"},
        ]

    def convert(self, result, scene_type, options=None):
        return {
            "simulation_type": "energy_evolution",
            "times": result.get("times", []),
            "kinetic_energy": result.get("kinetic_energy", []),
            "potential_energy": result.get("potential_energy", []),
            "total_energy": result.get("total_energy", []),
            "title": "QM/MM Energy Evolution",
        }


# ---------------------------------------------------------------------------
# Biology
# ---------------------------------------------------------------------------

@register_converter("basico")
class BasiCOConverter(ManimConverter):
    def supported_scenes(self):
        return [
            {"scene_type": "concentration_time_course", "label": "Time Course", "description": "Species concentration curves"},
            {"scene_type": "reaction_network_graph", "label": "Reaction Network", "description": "Animated reaction network"},
        ]

    def convert(self, result, scene_type, options=None):
        if scene_type == "concentration_time_course":
            return {
                "simulation_type": "concentration_time_course",
                "times": result.get("times", []),
                "species": result.get("species", result.get("concentrations", {})),
                "title": "BasiCO Time Course",
            }
        return {
            "simulation_type": "reaction_network_graph",
            "species_nodes": result.get("species_names", []),
            "reactions": result.get("reactions", []),
            "title": "Reaction Network",
        }


@register_converter("tellurium")
class TelluriumConverter(ManimConverter):
    def supported_scenes(self):
        return [
            {"scene_type": "concentration_time_course", "label": "Time Course", "description": "SBML pathway time course"},
            {"scene_type": "reaction_network_graph", "label": "Reaction Network", "description": "Pathway network graph"},
        ]

    def convert(self, result, scene_type, options=None):
        if scene_type == "concentration_time_course":
            return {
                "simulation_type": "concentration_time_course",
                "times": result.get("times", []),
                "species": result.get("species", {}),
                "title": "Tellurium Time Course",
            }
        return {
            "simulation_type": "reaction_network_graph",
            "species_nodes": result.get("species_names", []),
            "reactions": result.get("reactions", []),
            "title": "Pathway Network",
        }


@register_converter("brian2")
class Brian2Converter(ManimConverter):
    def supported_scenes(self):
        return [
            {"scene_type": "spike_raster_animation", "label": "Spike Raster", "description": "Animated spike raster + voltage"},
        ]

    def convert(self, result, scene_type, options=None):
        return {
            "simulation_type": "spike_raster_animation",
            "spike_trains": result.get("spike_trains", {}),
            "voltage_trace": result.get("voltage_trace", {}),
            "t_max": result.get("t_max", result.get("duration", 100)),
            "title": "Brian2 Spike Raster",
        }


@register_converter("nest")
class NESTConverter(ManimConverter):
    def supported_scenes(self):
        return [
            {"scene_type": "spike_raster_animation", "label": "Spike Raster", "description": "Neural spike raster"},
        ]

    def convert(self, result, scene_type, options=None):
        return {
            "simulation_type": "spike_raster_animation",
            "spike_trains": result.get("spike_trains", {}),
            "voltage_trace": result.get("voltage_trace", {}),
            "t_max": result.get("t_max", 100),
            "title": "NEST Spike Raster",
        }


# ---------------------------------------------------------------------------
# Continuum mechanics / FEM / CFD
# ---------------------------------------------------------------------------

@register_converter("fenics")
class FenicsConverter(ManimConverter):
    def supported_scenes(self):
        return [
            {"scene_type": "field_heatmap_animation", "label": "Field Heatmap", "description": "Animated 2D field evolution"},
            {"scene_type": "mesh_deformation", "label": "Mesh Deformation", "description": "Animated mesh stretching"},
        ]

    def convert(self, result, scene_type, options=None):
        if scene_type == "mesh_deformation":
            return {
                "simulation_type": "mesh_deformation",
                "nodes_initial": result.get("nodes_initial", result.get("nodes", [])),
                "nodes_deformed": result.get("nodes_deformed", []),
                "elements": result.get("elements", result.get("cells", [])),
                "title": "FEniCS Mesh Deformation",
            }
        return {
            "simulation_type": "field_heatmap_animation",
            "frames": result.get("field_frames", result.get("frames", [])),
            "title": result.get("label", "FEniCS Field"),
            "field_name": result.get("field_name", "u"),
        }


@register_converter("elmer")
class ElmerConverter(ManimConverter):
    def supported_scenes(self):
        return [
            {"scene_type": "field_heatmap_animation", "label": "Field Heatmap", "description": "Elmer field evolution"},
            {"scene_type": "mesh_deformation", "label": "Mesh Deformation", "description": "Elmer mesh deformation"},
        ]

    def convert(self, result, scene_type, options=None):
        if scene_type == "mesh_deformation":
            return {
                "simulation_type": "mesh_deformation",
                "nodes_initial": result.get("nodes", []),
                "nodes_deformed": result.get("nodes_deformed", []),
                "elements": result.get("elements", []),
                "title": "Elmer Mesh",
            }
        return {
            "simulation_type": "field_heatmap_animation",
            "frames": result.get("field_frames", []),
            "title": "Elmer Field",
        }


@register_converter("firedrake")
class FiredrakeConverter(ManimConverter):
    def supported_scenes(self):
        return [
            {"scene_type": "field_heatmap_animation", "label": "Field Heatmap", "description": "Firedrake field evolution"},
            {"scene_type": "mesh_deformation", "label": "Mesh Deformation", "description": "Firedrake mesh deformation"},
        ]

    def convert(self, result, scene_type, options=None):
        if scene_type == "mesh_deformation":
            return {
                "simulation_type": "mesh_deformation",
                "nodes_initial": result.get("nodes", []),
                "nodes_deformed": result.get("nodes_deformed", []),
                "elements": result.get("elements", []),
                "title": "Firedrake Mesh",
            }
        return {
            "simulation_type": "field_heatmap_animation",
            "frames": result.get("field_frames", []),
            "title": "Firedrake Field",
        }


@register_converter("phiflow")
class PhiFlowConverter(ManimConverter):
    def supported_scenes(self):
        return [
            {"scene_type": "streamline_flow", "label": "Streamlines", "description": "Animated velocity streamlines"},
            {"scene_type": "field_heatmap_animation", "label": "Field Heatmap", "description": "Scalar field animation"},
        ]

    def convert(self, result, scene_type, options=None):
        if scene_type == "streamline_flow":
            return {
                "simulation_type": "streamline_flow",
                "velocity_field": result.get("velocity_field", None),
                "title": "PhiFlow Streamlines",
            }
        return {
            "simulation_type": "field_heatmap_animation",
            "frames": result.get("field_frames", []),
            "title": "PhiFlow Field",
        }


@register_converter("openfoam")
class OpenFOAMConverter(ManimConverter):
    def supported_scenes(self):
        return [
            {"scene_type": "streamline_flow", "label": "Streamlines", "description": "CFD velocity streamlines"},
            {"scene_type": "field_heatmap_animation", "label": "Field Heatmap", "description": "Pressure/velocity field"},
        ]

    def convert(self, result, scene_type, options=None):
        if scene_type == "streamline_flow":
            return {
                "simulation_type": "streamline_flow",
                "velocity_field": result.get("velocity_field", None),
                "title": "OpenFOAM Streamlines",
            }
        return {
            "simulation_type": "field_heatmap_animation",
            "frames": result.get("field_frames", []),
            "title": "OpenFOAM Field",
        }


@register_converter("su2")
class SU2Converter(ManimConverter):
    def supported_scenes(self):
        return [
            {"scene_type": "streamline_flow", "label": "Streamlines", "description": "SU2 flow streamlines"},
        ]

    def convert(self, result, scene_type, options=None):
        return {
            "simulation_type": "streamline_flow",
            "velocity_field": result.get("velocity_field", None),
            "title": "SU2 Flow Field",
        }


@register_converter("dedalus")
class DedalusConverter(ManimConverter):
    def supported_scenes(self):
        return [
            {"scene_type": "field_heatmap_animation", "label": "Field Heatmap", "description": "Spectral PDE field evolution"},
        ]

    def convert(self, result, scene_type, options=None):
        return {
            "simulation_type": "field_heatmap_animation",
            "frames": result.get("field_frames", result.get("frames", [])),
            "title": "Dedalus Field",
        }


@register_converter("gmsh")
class GmshConverter(ManimConverter):
    def supported_scenes(self):
        return [
            {"scene_type": "mesh_deformation", "label": "Mesh View", "description": "Mesh visualization"},
        ]

    def convert(self, result, scene_type, options=None):
        return {
            "simulation_type": "mesh_deformation",
            "nodes_initial": result.get("nodes", []),
            "nodes_deformed": [],
            "elements": result.get("elements", []),
            "title": "Gmsh Mesh",
        }


@register_converter("comsol")
class COMSOLConverter(ManimConverter):
    def supported_scenes(self):
        return [
            {"scene_type": "field_heatmap_animation", "label": "Field Heatmap", "description": "COMSOL field data"},
        ]

    def convert(self, result, scene_type, options=None):
        return {
            "simulation_type": "field_heatmap_animation",
            "frames": result.get("field_frames", []),
            "title": "COMSOL Field",
        }


# ---------------------------------------------------------------------------
# Physics
# ---------------------------------------------------------------------------

@register_converter("pybullet")
class PyBulletConverter(ManimConverter):
    def supported_scenes(self):
        return [
            {"scene_type": "rigid_body_animation", "label": "Rigid Body", "description": "Animated bodies with collisions"},
            {"scene_type": "mechanism_animation", "label": "Mechanism", "description": "Joint-link mechanism"},
        ]

    def convert(self, result, scene_type, options=None):
        if scene_type == "mechanism_animation":
            return {
                "simulation_type": "mechanism_animation",
                "joints": result.get("joints", []),
                "links": result.get("links", []),
                "motion_frames": result.get("motion_frames", []),
                "title": "Mechanism Animation",
            }
        return {
            "simulation_type": "rigid_body_animation",
            "bodies": result.get("bodies", []),
            "collisions": result.get("collisions", []),
            "title": "Rigid Body Simulation",
        }


# ---------------------------------------------------------------------------
# Chemistry
# ---------------------------------------------------------------------------

@register_converter("rdkit")
class RDKitConverter(ManimConverter):
    def supported_scenes(self):
        return [
            {"scene_type": "molecule_structure_2d", "label": "2D Structure", "description": "Molecular structure drawing"},
            {"scene_type": "descriptor_radar_chart", "label": "Descriptor Radar", "description": "Molecular descriptor chart"},
        ]

    def convert(self, result, scene_type, options=None):
        if scene_type == "descriptor_radar_chart":
            return {
                "simulation_type": "descriptor_radar_chart",
                "descriptors": result.get("descriptors", {}),
                "title": "Molecular Descriptors",
            }
        return {
            "simulation_type": "molecule_structure_2d",
            "atoms": result.get("atoms_2d", result.get("atoms", [])),
            "bonds": result.get("bonds", []),
            "title": result.get("smiles", "Molecule"),
        }


@register_converter("openbabel")
class OpenBabelConverter(ManimConverter):
    def supported_scenes(self):
        return [
            {"scene_type": "molecule_structure_2d", "label": "2D Structure", "description": "Molecular structure from Open Babel"},
        ]

    def convert(self, result, scene_type, options=None):
        return {
            "simulation_type": "molecule_structure_2d",
            "atoms": result.get("atoms", []),
            "bonds": result.get("bonds", []),
            "title": "Molecule Structure",
        }


@register_converter("cantera")
class CanteraConverter(ManimConverter):
    def supported_scenes(self):
        return [
            {"scene_type": "ignition_animation", "label": "Ignition Delay", "description": "Temperature spike + species"},
            {"scene_type": "flame_profile", "label": "Flame Profile", "description": "Flame temperature profile"},
        ]

    def default_scene(self, result):
        if result.get("flame_profile") or result.get("positions"):
            return "flame_profile"
        return "ignition_animation"

    def convert(self, result, scene_type, options=None):
        if scene_type == "flame_profile":
            return {
                "simulation_type": "flame_profile",
                "positions": result.get("positions", result.get("grid", [])),
                "temperature_profile": result.get("temperature_profile", result.get("T", [])),
                "title": "Flame Profile",
            }
        return {
            "simulation_type": "ignition_animation",
            "times": result.get("times", []),
            "temperature": result.get("temperature", result.get("T", [])),
            "title": "Ignition Delay",
        }


@register_converter("psi4")
class Psi4Converter(ManimConverter):
    def supported_scenes(self):
        return [
            {"scene_type": "sapt_decomposition", "label": "SAPT Decomposition", "description": "SAPT energy components"},
            {"scene_type": "energy_spectrum", "label": "Energy Levels", "description": "Orbital energy levels"},
        ]

    def default_scene(self, result):
        if result.get("sapt_components") or result.get("sapt"):
            return "sapt_decomposition"
        return "energy_spectrum"

    def convert(self, result, scene_type, options=None):
        if scene_type == "sapt_decomposition":
            sapt = result.get("sapt_components", result.get("sapt", {}))
            return {
                "simulation_type": "sapt_decomposition",
                "components": sapt,
                "title": "SAPT Energy Decomposition",
            }
        return {
            "simulation_type": "energy_spectrum",
            "energy_levels": result.get("orbital_energies", []),
            "title": "Psi4 Energy Levels",
        }


# ---------------------------------------------------------------------------
# Population genetics
# ---------------------------------------------------------------------------

@register_converter("msprime")
class MsprimeConverter(ManimConverter):
    def supported_scenes(self):
        return [
            {"scene_type": "allele_frequency_trajectory", "label": "Allele Freq", "description": "Allele frequency drift"},
            {"scene_type": "phylogenetic_tree_animation", "label": "Tree", "description": "Coalescent tree"},
        ]

    def convert(self, result, scene_type, options=None):
        if scene_type == "phylogenetic_tree_animation":
            return {
                "simulation_type": "phylogenetic_tree_animation",
                "nodes": result.get("tree_nodes", []),
                "edges": result.get("tree_edges", []),
                "title": "Coalescent Tree",
            }
        return {
            "simulation_type": "allele_frequency_trajectory",
            "generations": result.get("generations", []),
            "allele_freqs": result.get("allele_freqs", {}),
            "title": "Allele Frequencies",
        }


@register_converter("slim")
class SLiMConverter(ManimConverter):
    def supported_scenes(self):
        return [
            {"scene_type": "allele_frequency_trajectory", "label": "Allele Freq", "description": "Forward-time allele frequency"},
        ]

    def convert(self, result, scene_type, options=None):
        return {
            "simulation_type": "allele_frequency_trajectory",
            "generations": result.get("generations", []),
            "allele_freqs": result.get("allele_freqs", {}),
            "title": "SLiM Allele Frequencies",
        }


@register_converter("simupop")
class SimuPOPConverter(ManimConverter):
    def supported_scenes(self):
        return [
            {"scene_type": "allele_frequency_trajectory", "label": "Allele Freq", "description": "Population allele frequency"},
        ]

    def convert(self, result, scene_type, options=None):
        return {
            "simulation_type": "allele_frequency_trajectory",
            "generations": result.get("generations", []),
            "allele_freqs": result.get("allele_freqs", {}),
            "title": "simuPOP Allele Frequencies",
        }


@register_converter("tskit")
class TskitConverter(ManimConverter):
    def supported_scenes(self):
        return [
            {"scene_type": "phylogenetic_tree_animation", "label": "Tree Sequence", "description": "Animated tree growth"},
        ]

    def convert(self, result, scene_type, options=None):
        return {
            "simulation_type": "phylogenetic_tree_animation",
            "nodes": result.get("tree_nodes", result.get("nodes", [])),
            "edges": result.get("tree_edges", result.get("edges", [])),
            "title": "Tree Sequence",
        }


# ---------------------------------------------------------------------------
# Materials science
# ---------------------------------------------------------------------------

@register_converter("qe")
class QEConverter(ManimConverter):
    def supported_scenes(self):
        return [
            {"scene_type": "band_structure_animation", "label": "Band Structure", "description": "Electronic band structure"},
        ]

    def convert(self, result, scene_type, options=None):
        return {
            "simulation_type": "band_structure_animation",
            "k_points": result.get("k_points", []),
            "bands": result.get("bands", []),
            "k_labels": result.get("k_labels", []),
            "fermi_energy": result.get("fermi_energy", 0),
            "title": "QE Band Structure",
        }


@register_converter("lammps")
class LAMMPSConverter(ManimConverter):
    def supported_scenes(self):
        return [
            {"scene_type": "rdf_animation", "label": "RDF", "description": "Radial distribution function"},
            {"scene_type": "energy_evolution", "label": "Energy", "description": "Energy evolution"},
        ]

    def convert(self, result, scene_type, options=None):
        if scene_type == "energy_evolution":
            return {
                "simulation_type": "energy_evolution",
                "times": result.get("times", []),
                "kinetic_energy": result.get("kinetic_energy", []),
                "potential_energy": result.get("potential_energy", []),
                "total_energy": result.get("total_energy", []),
                "title": "LAMMPS Energy",
            }
        return {
            "simulation_type": "rdf_animation",
            "r_values": result.get("r", result.get("r_values", [])),
            "g_values": result.get("g", result.get("g_values", [])),
            "rdf_frames": result.get("rdf_frames", []),
            "title": "LAMMPS RDF",
        }


# ---------------------------------------------------------------------------
# Circuits / Control
# ---------------------------------------------------------------------------

@register_converter("control")
class ControlConverter(ManimConverter):
    def supported_scenes(self):
        return [
            {"scene_type": "bode_plot_animation", "label": "Bode Plot", "description": "Animated Bode magnitude/phase"},
        ]

    def convert(self, result, scene_type, options=None):
        return {
            "simulation_type": "bode_plot_animation",
            "frequencies": result.get("frequencies", result.get("omega", [])),
            "magnitude_db": result.get("magnitude_db", result.get("mag", [])),
            "phase_deg": result.get("phase_deg", result.get("phase", [])),
            "title": "Bode Plot",
        }


@register_converter("lcapy")
class LcapyConverter(ManimConverter):
    def supported_scenes(self):
        return [
            {"scene_type": "bode_plot_animation", "label": "Bode Plot", "description": "Transfer function Bode plot"},
            {"scene_type": "transient_waveform", "label": "Transient", "description": "Circuit waveforms"},
        ]

    def convert(self, result, scene_type, options=None):
        if scene_type == "transient_waveform":
            return {
                "simulation_type": "transient_waveform",
                "times": result.get("times", []),
                "signals": result.get("signals", result.get("waveforms", {})),
                "title": "Lcapy Transient",
            }
        return {
            "simulation_type": "bode_plot_animation",
            "frequencies": result.get("frequencies", []),
            "magnitude_db": result.get("magnitude_db", []),
            "phase_deg": result.get("phase_deg", []),
            "title": "Lcapy Bode Plot",
        }


@register_converter("pyspice")
class PySpiceConverter(ManimConverter):
    def supported_scenes(self):
        return [
            {"scene_type": "transient_waveform", "label": "Transient", "description": "Circuit transient waveforms"},
        ]

    def convert(self, result, scene_type, options=None):
        return {
            "simulation_type": "transient_waveform",
            "times": result.get("times", result.get("time", [])),
            "signals": result.get("signals", result.get("waveforms", {})),
            "title": "PySpice Transient",
        }


# ---------------------------------------------------------------------------
# Quantum computing
# ---------------------------------------------------------------------------

@register_converter("qiskit")
class QiskitConverter(ManimConverter):
    def supported_scenes(self):
        return [
            {"scene_type": "quantum_circuit_animation", "label": "Circuit", "description": "Gate-by-gate circuit animation"},
            {"scene_type": "vqe_convergence", "label": "VQE", "description": "VQE energy convergence"},
        ]

    def default_scene(self, result):
        if result.get("vqe_iterations") or result.get("energies"):
            return "vqe_convergence"
        return "quantum_circuit_animation"

    def convert(self, result, scene_type, options=None):
        if scene_type == "vqe_convergence":
            return {
                "simulation_type": "vqe_convergence",
                "iterations": result.get("vqe_iterations", result.get("iterations", [])),
                "energies": result.get("vqe_energies", result.get("energies", [])),
                "exact_energy": result.get("exact_energy"),
                "title": "Qiskit VQE Convergence",
            }
        return {
            "simulation_type": "quantum_circuit_animation",
            "n_qubits": result.get("n_qubits", 2),
            "gates": result.get("gates", result.get("circuit_gates", [])),
            "title": "Quantum Circuit",
        }


@register_converter("pennylane")
class PennyLaneConverter(ManimConverter):
    def supported_scenes(self):
        return [
            {"scene_type": "quantum_circuit_animation", "label": "Circuit", "description": "Quantum circuit animation"},
            {"scene_type": "vqe_convergence", "label": "VQE", "description": "VQE/QNN convergence"},
        ]

    def default_scene(self, result):
        if result.get("iterations") or result.get("energies"):
            return "vqe_convergence"
        return "quantum_circuit_animation"

    def convert(self, result, scene_type, options=None):
        if scene_type == "vqe_convergence":
            return {
                "simulation_type": "vqe_convergence",
                "iterations": result.get("iterations", []),
                "energies": result.get("energies", []),
                "exact_energy": result.get("exact_energy"),
                "title": "PennyLane Convergence",
            }
        return {
            "simulation_type": "quantum_circuit_animation",
            "n_qubits": result.get("n_qubits", 2),
            "gates": result.get("gates", []),
            "title": "PennyLane Circuit",
        }


# ---------------------------------------------------------------------------
# Math / Symbolic — map to existing math scenes
# ---------------------------------------------------------------------------

@register_converter("sympy")
class SympyConverter(ManimConverter):
    def supported_scenes(self):
        return [
            {"scene_type": "equation_animation", "label": "Equation", "description": "Animated equation rendering"},
        ]

    def convert(self, result, scene_type, options=None):
        expressions = result.get("latex", result.get("expressions", []))
        if isinstance(expressions, str):
            expressions = [expressions]
        return {
            "simulation_type": "equation_animation",
            "expressions": expressions,
            "animation_type": "transform",
        }


@register_converter("sagemath")
class SageMathConverter(ManimConverter):
    def supported_scenes(self):
        return [
            {"scene_type": "equation_animation", "label": "Equation", "description": "Math expression animation"},
        ]

    def convert(self, result, scene_type, options=None):
        expressions = result.get("latex", result.get("expressions", []))
        if isinstance(expressions, str):
            expressions = [expressions]
        return {
            "simulation_type": "equation_animation",
            "expressions": expressions,
            "animation_type": "write",
        }


@register_converter("lean4")
class Lean4Converter(ManimConverter):
    def supported_scenes(self):
        return [
            {"scene_type": "equation_animation", "label": "Proof Steps", "description": "Proof steps as equations"},
        ]

    def convert(self, result, scene_type, options=None):
        steps = result.get("proof_steps", result.get("steps", []))
        return {
            "simulation_type": "equation_animation",
            "expressions": steps if steps else ["\\text{Proof complete}"],
            "animation_type": "transform",
        }


@register_converter("gap")
class GAPConverter(ManimConverter):
    def supported_scenes(self):
        return [
            {"scene_type": "equation_animation", "label": "Group Elements", "description": "Group elements as equations"},
        ]

    def convert(self, result, scene_type, options=None):
        elements = result.get("elements", result.get("generators", []))
        if isinstance(elements, str):
            elements = [elements]
        return {
            "simulation_type": "equation_animation",
            "expressions": elements if elements else ["G"],
            "animation_type": "write",
        }


# ---------------------------------------------------------------------------
# Graph / Optimization — map to existing scenes
# ---------------------------------------------------------------------------

@register_converter("networkx")
class NetworkXConverter(ManimConverter):
    def supported_scenes(self):
        return [
            {"scene_type": "graph_animation", "label": "Graph Animation", "description": "Animated graph/network"},
        ]

    def convert(self, result, scene_type, options=None):
        return {
            "simulation_type": "graph_animation",
            "nodes": result.get("nodes", []),
            "edges": result.get("edges", []),
            "highlight_path": result.get("shortest_path", result.get("path", [])),
        }


@register_converter("pyomo")
class PyomoConverter(ManimConverter):
    def supported_scenes(self):
        return [
            {"scene_type": "function_plot", "label": "Convergence Plot", "description": "Optimization convergence"},
        ]

    def convert(self, result, scene_type, options=None):
        return {
            "simulation_type": "function_plot",
            "functions": ["lambda x: x"],  # placeholder
            "x_range": [-5, 5],
            "animate_draw": True,
        }


# ---------------------------------------------------------------------------
# Deferred stub converters
# ---------------------------------------------------------------------------

@register_converter("alphafold")
class AlphaFoldConverter(ManimConverter):
    def supported_scenes(self):
        return [
            {"scene_type": "molecule_structure_2d", "label": "Structure", "description": "Protein structure (deferred)"},
        ]

    def convert(self, result, scene_type, options=None):
        return {
            "simulation_type": "molecule_structure_2d",
            "atoms": result.get("atoms", []),
            "bonds": result.get("bonds", []),
            "title": "AlphaFold Structure",
        }


@register_converter("pyrosetta")
class PyRosettaConverter(ManimConverter):
    def supported_scenes(self):
        return [
            {"scene_type": "molecule_structure_2d", "label": "Structure", "description": "Protein model (deferred)"},
        ]

    def convert(self, result, scene_type, options=None):
        return {
            "simulation_type": "molecule_structure_2d",
            "atoms": result.get("atoms", []),
            "bonds": result.get("bonds", []),
            "title": "PyRosetta Structure",
        }
