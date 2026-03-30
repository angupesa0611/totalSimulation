from typing import Any
import numpy as np
from celery_app import app as celery_app
from tools.base import SimulationTool
from results import save_result


class PySCFTool(SimulationTool):
    name = "PySCF"
    key = "pyscf"
    layer = "electronic"

    METHODS = {"hf", "dft", "mp2", "ccsd"}
    XC_FUNCTIONALS = {"b3lyp", "pbe", "pbe0", "lda", "m06-2x"}
    BASIS_SETS = {"sto-3g", "6-31g", "6-31g*", "6-311g**", "cc-pvdz", "cc-pvtz", "aug-cc-pvdz"}

    def validate_params(self, params: dict[str, Any]) -> dict[str, Any]:
        if "atom_coords" not in params or not params["atom_coords"]:
            raise ValueError("atom_coords is required (e.g. 'H 0 0 0; H 0 0 0.74')")

        method = params.get("method", "hf").lower()
        if method not in self.METHODS:
            raise ValueError(f"Unknown method: {method}. Supported: {self.METHODS}")

        params.setdefault("basis", "sto-3g")
        params.setdefault("method", "hf")
        params.setdefault("charge", 0)
        params.setdefault("spin", 0)
        params.setdefault("xc_functional", "b3lyp")
        return params

    def run(self, params: dict[str, Any]) -> dict[str, Any]:
        params = self.validate_params(params)

        from pyscf import gto, scf, dft, mp, cc

        # Build molecule
        mol = gto.Mole()
        mol.atom = params["atom_coords"]
        mol.basis = params["basis"]
        mol.charge = params["charge"]
        mol.spin = params["spin"]
        mol.build()

        method = params["method"].lower()
        xc = params.get("xc_functional", "b3lyp")

        # Run calculation based on method
        if method == "hf":
            if mol.spin == 0:
                mf = scf.RHF(mol)
            else:
                mf = scf.UHF(mol)
            mf.kernel()
            total_energy = float(mf.e_tot)
            orbital_energies = mf.mo_energy.tolist() if isinstance(mf.mo_energy, np.ndarray) else [e.tolist() for e in mf.mo_energy]
            mo_occ = mf.mo_occ.tolist() if isinstance(mf.mo_occ, np.ndarray) else [o.tolist() for o in mf.mo_occ]

        elif method == "dft":
            if mol.spin == 0:
                mf = dft.RKS(mol)
            else:
                mf = dft.UKS(mol)
            mf.xc = xc
            mf.kernel()
            total_energy = float(mf.e_tot)
            orbital_energies = mf.mo_energy.tolist() if isinstance(mf.mo_energy, np.ndarray) else [e.tolist() for e in mf.mo_energy]
            mo_occ = mf.mo_occ.tolist() if isinstance(mf.mo_occ, np.ndarray) else [o.tolist() for o in mf.mo_occ]

        elif method == "mp2":
            if mol.spin == 0:
                mf = scf.RHF(mol).run()
            else:
                mf = scf.UHF(mol).run()
            mp2_obj = mp.MP2(mf).run()
            total_energy = float(mp2_obj.e_tot)
            orbital_energies = mf.mo_energy.tolist() if isinstance(mf.mo_energy, np.ndarray) else [e.tolist() for e in mf.mo_energy]
            mo_occ = mf.mo_occ.tolist() if isinstance(mf.mo_occ, np.ndarray) else [o.tolist() for o in mf.mo_occ]

        elif method == "ccsd":
            if mol.spin == 0:
                mf = scf.RHF(mol).run()
            else:
                mf = scf.UHF(mol).run()
            cc_obj = cc.CCSD(mf).run()
            total_energy = float(cc_obj.e_tot)
            orbital_energies = mf.mo_energy.tolist() if isinstance(mf.mo_energy, np.ndarray) else [e.tolist() for e in mf.mo_energy]
            mo_occ = mf.mo_occ.tolist() if isinstance(mf.mo_occ, np.ndarray) else [o.tolist() for o in mf.mo_occ]

        # Mulliken charges
        mulliken_charges = []
        try:
            pop = mf.mulliken_pop(verbose=0)
            mulliken_charges = pop[1].tolist()
        except Exception:
            pass

        # Dipole moment
        dipole = []
        try:
            dip = mf.dip_moment(verbose=0)
            dipole = dip.tolist() if isinstance(dip, np.ndarray) else list(dip)
        except Exception:
            pass

        # Atom labels
        atom_labels = [mol.atom_symbol(i) for i in range(mol.natm)]

        return {
            "tool": "pyscf",
            "method": method,
            "basis": params["basis"],
            "xc_functional": xc if method == "dft" else None,
            "total_energy": total_energy,
            "orbital_energies": orbital_energies,
            "mo_occ": mo_occ,
            "mulliken_charges": mulliken_charges,
            "dipole_moment": dipole,
            "atom_labels": atom_labels,
            "n_atoms": mol.natm,
            "n_electrons": mol.nelectron,
            "charge": params["charge"],
            "spin": params["spin"],
        }

    def get_default_params(self) -> dict[str, Any]:
        return {
            "atom_coords": "H 0 0 0; H 0 0 0.74",
            "basis": "sto-3g",
            "method": "hf",
            "charge": 0,
            "spin": 0,
        }


@celery_app.task(name="tools.pyscf_tool.run_pyscf", bind=True)
def run_pyscf(self, params: dict, project: str = "_default",
              label: str | None = None) -> dict:
    tool = PySCFTool()

    self.update_state(state="PROGRESS", meta={"progress": 0.0, "message": "Setting up PySCF calculation"})

    try:
        self.update_state(state="PROGRESS", meta={"progress": 0.1, "message": f"Running {params.get('method', 'hf').upper()} calculation"})
        result = tool.run(params)
    except Exception as e:
        raise

    self.update_state(state="PROGRESS", meta={"progress": 0.9, "message": "Saving results"})
    save_result(self.request.id, "pyscf", result, project, label)

    return result
