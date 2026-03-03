from .rebound_tool import REBOUNDTool
from .qutip_tool import QuTiPTool
from .pyscf_tool import PySCFTool
from .mdanalysis_tool import MDAnalysisTool
from .pybullet_tool import PyBulletTool
from .einsteinpy_tool import EinsteinPyTool
from .nrpy_tool import NRPyTool
from .basico_tool import BasicoTool
from .tellurium_tool import TelluriumTool
from .brian2_tool import Brian2Tool
from .msprime_tool import MsprimeTool
from .rdkit_tool import RDKitTool
from .cantera_tool import CanteraTool
from .sympy_tool import SymPyTool
from .gmsh_tool import GmshTool
from .lcapy_tool import LcapyTool
from .pennylane_tool import PennyLaneTool
from .matplotlib_tool import MatplotlibTool
from .control_tool import ControlTool
from .pyomo_tool import PyomoTool
from .networkx_tool import NetworkXTool
from .phiflow_tool import PhiFlowTool
from .vtk_tool import VTKTool
from .tskit_tool import TreeSequenceTool
from .simupop_tool import SimuPOPTool

TOOL_INSTANCES = {
    "rebound": REBOUNDTool(),
    "qutip": QuTiPTool(),
    "pyscf": PySCFTool(),
    "mdanalysis": MDAnalysisTool(),
    "pybullet": PyBulletTool(),
    "einsteinpy": EinsteinPyTool(),
    "nrpy": NRPyTool(),
    "basico": BasicoTool(),
    "tellurium": TelluriumTool(),
    "brian2": Brian2Tool(),
    "msprime": MsprimeTool(),
    "rdkit": RDKitTool(),
    "cantera": CanteraTool(),
    "sympy": SymPyTool(),
    "gmsh": GmshTool(),
    "lcapy": LcapyTool(),
    "pennylane": PennyLaneTool(),
    "matplotlib": MatplotlibTool(),
    "control": ControlTool(),
    "pyomo": PyomoTool(),
    "networkx": NetworkXTool(),
    "phiflow": PhiFlowTool(),
    "vtk": VTKTool(),
    "tskit": TreeSequenceTool(),
    "simupop": SimuPOPTool(),
}
