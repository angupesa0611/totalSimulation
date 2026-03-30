from typing import Any
import numpy as np
from celery_app import app as celery_app
from tools.base import SimulationTool
from results import save_result


def _smiles_to_pyscf_coords(smiles: str, optimize: bool = True) -> str | None:
    """Convert SMILES string to PySCF-compatible atom_coords string.

    Pipeline helper for RDKit→PySCF coupling.
    Returns format: "C 0.0 0.0 0.0; H 0.0 0.0 1.09; ..."
    """
    from rdkit import Chem
    from rdkit.Chem import AllChem

    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None

    mol = Chem.AddHs(mol)
    result = AllChem.EmbedMolecule(mol, AllChem.ETKDGv3())
    if result != 0:
        # Retry with random coordinates
        result = AllChem.EmbedMolecule(mol, AllChem.ETKDGv3(), randomSeed=42)
        if result != 0:
            return None

    if optimize:
        AllChem.MMFFOptimizeMolecule(mol, maxIters=200)

    conf = mol.GetConformer()
    atoms = []
    for i in range(mol.GetNumAtoms()):
        symbol = mol.GetAtomWithIdx(i).GetSymbol()
        pos = conf.GetAtomPosition(i)
        atoms.append(f"{symbol} {pos.x:.6f} {pos.y:.6f} {pos.z:.6f}")

    return "; ".join(atoms)


class RDKitTool(SimulationTool):
    name = "RDKit"
    key = "rdkit"
    layer = "chemistry"

    SIMULATION_TYPES = {"descriptors", "conformer_3d", "fingerprint", "similarity"}
    FINGERPRINT_TYPES = {"morgan", "rdkit", "maccs"}

    def validate_params(self, params: dict[str, Any]) -> dict[str, Any]:
        sim_type = params.get("simulation_type", "descriptors")
        if sim_type not in self.SIMULATION_TYPES:
            raise ValueError(f"Unknown simulation_type: {sim_type}. Supported: {self.SIMULATION_TYPES}")

        if "smiles" not in params or not params["smiles"]:
            raise ValueError("smiles is required (e.g. 'CC(=O)Oc1ccccc1C(=O)O' for aspirin)")

        params.setdefault("simulation_type", sim_type)
        params.setdefault("n_conformers", 1)
        params.setdefault("optimize_conformer", True)
        params.setdefault("fingerprint_type", "morgan")
        params.setdefault("fingerprint_radius", 2)

        if sim_type == "similarity":
            if "smiles_list" not in params or not params["smiles_list"]:
                raise ValueError("smiles_list is required for similarity comparison")

        fp_type = params.get("fingerprint_type", "morgan")
        if fp_type not in self.FINGERPRINT_TYPES:
            raise ValueError(f"Unknown fingerprint_type: {fp_type}. Supported: {self.FINGERPRINT_TYPES}")

        return params

    def run(self, params: dict[str, Any]) -> dict[str, Any]:
        params = self.validate_params(params)
        sim_type = params["simulation_type"]

        if sim_type == "descriptors":
            return self._run_descriptors(params)
        elif sim_type == "conformer_3d":
            return self._run_conformer_3d(params)
        elif sim_type == "fingerprint":
            return self._run_fingerprint(params)
        elif sim_type == "similarity":
            return self._run_similarity(params)

    def _run_descriptors(self, params):
        from rdkit import Chem
        from rdkit.Chem import Descriptors, rdMolDescriptors

        smiles = params["smiles"]
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            raise ValueError(f"Invalid SMILES: {smiles}")

        # Generate PySCF coords for coupling
        atom_coords_pyscf = _smiles_to_pyscf_coords(
            smiles, optimize=params.get("optimize_conformer", True)
        )

        return {
            "tool": "rdkit",
            "simulation_type": "descriptors",
            "smiles": smiles,
            "molecular_weight": float(Descriptors.MolWt(mol)),
            "logp": float(Descriptors.MolLogP(mol)),
            "hbd": int(rdMolDescriptors.CalcNumHBD(mol)),
            "hba": int(rdMolDescriptors.CalcNumHBA(mol)),
            "tpsa": float(Descriptors.TPSA(mol)),
            "rotatable_bonds": int(rdMolDescriptors.CalcNumRotatableBonds(mol)),
            "ring_count": int(rdMolDescriptors.CalcNumRings(mol)),
            "formula": rdMolDescriptors.CalcMolFormula(mol),
            "atom_coords_pyscf": atom_coords_pyscf,
        }

    def _run_conformer_3d(self, params):
        from rdkit import Chem
        from rdkit.Chem import AllChem

        smiles = params["smiles"]
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            raise ValueError(f"Invalid SMILES: {smiles}")

        mol = Chem.AddHs(mol)
        n_conformers = min(params.get("n_conformers", 1), 10)
        optimize = params.get("optimize_conformer", True)

        # Generate conformers
        ps = AllChem.ETKDGv3()
        ps.numThreads = 1
        cids = AllChem.EmbedMultipleConfs(mol, numConfs=n_conformers, params=ps)
        if len(cids) == 0:
            raise ValueError(f"Could not generate 3D conformers for: {smiles}")

        conformers = []
        best_energy = float("inf")
        best_coords = None

        for cid in cids:
            if optimize:
                res = AllChem.MMFFOptimizeMolecule(mol, confId=cid, maxIters=200)

            # Get energy
            ff = AllChem.MMFFGetMoleculeForceField(mol, AllChem.MMFFGetMoleculeProperties(mol), confId=cid)
            energy = float(ff.CalcEnergy()) if ff else 0.0

            # Get coordinates
            conf = mol.GetConformer(cid)
            atoms = []
            for i in range(mol.GetNumAtoms()):
                symbol = mol.GetAtomWithIdx(i).GetSymbol()
                pos = conf.GetAtomPosition(i)
                atoms.append(f"{symbol} {pos.x:.6f} {pos.y:.6f} {pos.z:.6f}")

            coords_str = "; ".join(atoms)

            # XYZ block
            xyz_lines = [f"{mol.GetNumAtoms()}", f"Conformer {cid} E={energy:.4f}"]
            for i in range(mol.GetNumAtoms()):
                symbol = mol.GetAtomWithIdx(i).GetSymbol()
                pos = conf.GetAtomPosition(i)
                xyz_lines.append(f"{symbol} {pos.x:.6f} {pos.y:.6f} {pos.z:.6f}")
            xyz_block = "\n".join(xyz_lines)

            conformers.append({
                "energy": energy,
                "atom_coords_pyscf": coords_str,
                "xyz_block": xyz_block,
            })

            if energy < best_energy:
                best_energy = energy
                best_coords = coords_str

        return {
            "tool": "rdkit",
            "simulation_type": "conformer_3d",
            "smiles": smiles,
            "n_conformers": len(conformers),
            "conformers": conformers,
            "atom_coords_pyscf": best_coords,
        }

    def _run_fingerprint(self, params):
        from rdkit import Chem
        from rdkit.Chem import AllChem, rdMolDescriptors

        smiles = params["smiles"]
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            raise ValueError(f"Invalid SMILES: {smiles}")

        fp_type = params.get("fingerprint_type", "morgan")
        radius = params.get("fingerprint_radius", 2)

        if fp_type == "morgan":
            fp = AllChem.GetMorganFingerprintAsBitVect(mol, radius, nBits=2048)
        elif fp_type == "rdkit":
            fp = Chem.RDKFingerprint(mol)
        elif fp_type == "maccs":
            fp = rdMolDescriptors.GetMACCSKeysFingerprint(mol)

        bits_on = list(fp.GetOnBits())
        density = len(bits_on) / fp.GetNumBits()

        return {
            "tool": "rdkit",
            "simulation_type": "fingerprint",
            "smiles": smiles,
            "fingerprint_type": fp_type,
            "bits_on": bits_on,
            "n_bits": fp.GetNumBits(),
            "density": density,
        }

    def _run_similarity(self, params):
        from rdkit import Chem
        from rdkit.Chem import AllChem, DataStructs

        query_smiles = params["smiles"]
        query_mol = Chem.MolFromSmiles(query_smiles)
        if query_mol is None:
            raise ValueError(f"Invalid query SMILES: {query_smiles}")

        radius = params.get("fingerprint_radius", 2)
        query_fp = AllChem.GetMorganFingerprintAsBitVect(query_mol, radius, nBits=2048)

        targets = params.get("smiles_list", [])
        scores = []
        valid_targets = []

        for target_smiles in targets:
            target_mol = Chem.MolFromSmiles(target_smiles)
            if target_mol is None:
                scores.append(0.0)
                valid_targets.append(target_smiles)
                continue
            target_fp = AllChem.GetMorganFingerprintAsBitVect(target_mol, radius, nBits=2048)
            score = float(DataStructs.TanimotoSimilarity(query_fp, target_fp))
            scores.append(score)
            valid_targets.append(target_smiles)

        return {
            "tool": "rdkit",
            "simulation_type": "similarity",
            "query": query_smiles,
            "targets": valid_targets,
            "similarity_scores": scores,
        }

    def get_default_params(self) -> dict[str, Any]:
        return {
            "simulation_type": "descriptors",
            "smiles": "CC(=O)Oc1ccccc1C(=O)O",
            "n_conformers": 1,
            "optimize_conformer": True,
            "fingerprint_type": "morgan",
            "fingerprint_radius": 2,
        }


@celery_app.task(name="tools.rdkit_tool.run_rdkit", bind=True)
def run_rdkit(self, params: dict, project: str = "_default",
              label: str | None = None) -> dict:
    tool = RDKitTool()

    self.update_state(state="PROGRESS", meta={"progress": 0.0, "message": "Starting RDKit analysis"})

    try:
        sim_type = params.get("simulation_type", "descriptors")
        self.update_state(state="PROGRESS", meta={"progress": 0.1, "message": f"Running {sim_type}"})
        result = tool.run(params)
    except Exception as e:
        raise

    self.update_state(state="PROGRESS", meta={"progress": 0.9, "message": "Saving results"})
    save_result(self.request.id, "rdkit", result, project, label)

    return result
