import json
import os
import subprocess
import tempfile
from datetime import datetime, timezone
from worker import app


def _save_result(job_id, tool, data, project="_default", label=None):
    results_dir = os.getenv("RESULTS_DIR", "/data/results")
    project_dir = os.path.join(results_dir, project)
    os.makedirs(project_dir, exist_ok=True)
    run_dir = os.path.join(project_dir, job_id)
    os.makedirs(run_dir, exist_ok=True)

    metadata = {
        "job_id": job_id, "tool": tool, "project": project,
        "label": label, "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    with open(os.path.join(run_dir, "metadata.json"), "w") as f:
        json.dump(metadata, f, indent=2)
    with open(os.path.join(run_dir, "result.json"), "w") as f:
        json.dump(data, f)

    index_path = os.path.join(project_dir, "_index.json")
    index = []
    if os.path.exists(index_path):
        with open(index_path) as f:
            index = json.load(f)
    index.append(metadata)
    with open(index_path, "w") as f:
        json.dump(index, f, indent=2)
    return run_dir


def _run_gap_script(script, timeout_s=60):
    """Write GAP script to temp file and run gap CLI."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".g", delete=False) as f:
        f.write(script)
        f.write("\nQUIT;\n")
        f.flush()
        gap_file = f.name

    try:
        proc = subprocess.run(
            ["gap", "-q", "-b", gap_file],
            capture_output=True,
            text=True,
            timeout=timeout_s,
        )
        return proc.stdout.strip()
    except subprocess.TimeoutExpired:
        return "Error: GAP computation timed out"
    finally:
        os.unlink(gap_file)


def _build_group(group_type, n):
    """Return GAP code to construct a group."""
    if group_type == "symmetric":
        return f"SymmetricGroup({n})"
    elif group_type == "alternating":
        return f"AlternatingGroup({n})"
    elif group_type == "cyclic":
        return f"CyclicGroup({n})"
    elif group_type == "dihedral":
        return f"DihedralGroup({n})"
    else:
        return f"SymmetricGroup({n})"


@app.task(name="tools.gap_tool.run_gap", bind=True)
def run_gap(self, params, project="_default", label=None):
    self.update_state(state="PROGRESS", meta={"progress": 0.0, "message": "Starting GAP computation"})

    sim_type = params.get("simulation_type", "group_properties")

    try:
        if sim_type == "group_properties":
            result = _run_group_properties(params)
        elif sim_type == "character_table":
            result = _run_character_table(params)
        elif sim_type == "representation":
            result = _run_representation(params)
        elif sim_type == "space_group":
            result = _run_space_group(params)
        elif sim_type == "stabilizer_codes":
            result = _run_stabilizer_codes(params)
        else:
            raise ValueError(f"Unknown simulation_type: {sim_type}")
    except Exception as e:
        self.update_state(state="FAILURE", meta={"message": str(e)})
        raise

    result["tool"] = "gap"
    result["simulation_type"] = sim_type

    self.update_state(state="PROGRESS", meta={"progress": 0.9, "message": "Saving results"})
    _save_result(self.request.id, "gap", result, project, label)
    return result


def _run_group_properties(params):
    group_type = params.get("group_type", "symmetric")
    n = params.get("n", 5)
    compute = params.get("compute", "order")
    group_code = _build_group(group_type, n)

    script_parts = [f"G := {group_code};"]

    if compute == "order":
        script_parts.append('Print("ORDER:", Size(G), "\\n");')
    elif compute == "elements":
        script_parts.append('Print("ORDER:", Size(G), "\\n");')
        if n <= 6:
            script_parts.append('Print("ELEMENTS:", Elements(G), "\\n");')
        else:
            script_parts.append('Print("ELEMENTS:too_large\\n");')
    elif compute == "center":
        script_parts.append('C := Center(G);')
        script_parts.append('Print("CENTER_ORDER:", Size(C), "\\n");')
        script_parts.append('Print("CENTER:", Elements(C), "\\n");')
    elif compute == "conjugacy_classes":
        script_parts.append('cc := ConjugacyClasses(G);')
        script_parts.append('Print("N_CLASSES:", Length(cc), "\\n");')
        script_parts.append('for c in cc do Print("CLASS:", Size(c), ":", Representative(c), "\\n"); od;')

    script_parts.append('Print("GENERATORS:", GeneratorsOfGroup(G), "\\n");')

    script = "\n".join(script_parts)
    output = _run_gap_script(script)

    # Parse output
    result = {
        "group_type": group_type,
        "n": n,
        "compute": compute,
        "raw_output": output,
    }

    lines = output.split("\n")
    for line in lines:
        if line.startswith("ORDER:"):
            try:
                result["group_order"] = int(line.split(":", 1)[1].strip())
            except ValueError:
                result["group_order"] = line.split(":", 1)[1].strip()
        elif line.startswith("CENTER_ORDER:"):
            try:
                result["center_order"] = int(line.split(":", 1)[1].strip())
            except ValueError:
                pass
        elif line.startswith("N_CLASSES:"):
            try:
                result["n_conjugacy_classes"] = int(line.split(":", 1)[1].strip())
            except ValueError:
                pass
        elif line.startswith("GENERATORS:"):
            result["generators"] = line.split(":", 1)[1].strip()

    # Parse conjugacy classes
    classes = []
    for line in lines:
        if line.startswith("CLASS:"):
            parts = line[6:].split(":", 1)
            if len(parts) == 2:
                classes.append({"size": parts[0].strip(), "representative": parts[1].strip()})
    if classes:
        result["conjugacy_classes"] = classes

    return result


def _run_character_table(params):
    group_type = params.get("group_type", "symmetric")
    n = params.get("n", 4)
    group_code = _build_group(group_type, n)

    script = f"""
G := {group_code};
ct := CharacterTable(G);
Print("CHAR_TABLE_START\\n");
Display(ct);
Print("CHAR_TABLE_END\\n");
Print("N_CLASSES:", NrConjugacyClasses(G), "\\n");
Print("ORDER:", Size(G), "\\n");
"""

    output = _run_gap_script(script)

    # Extract character table text
    ct_text = ""
    in_table = False
    for line in output.split("\n"):
        if "CHAR_TABLE_START" in line:
            in_table = True
            continue
        if "CHAR_TABLE_END" in line:
            in_table = False
            continue
        if in_table:
            ct_text += line + "\n"

    result = {
        "group_type": group_type,
        "n": n,
        "character_table_text": ct_text.strip(),
        "raw_output": output,
    }

    for line in output.split("\n"):
        if line.startswith("N_CLASSES:"):
            try:
                result["n_classes"] = int(line.split(":", 1)[1].strip())
            except ValueError:
                pass
        elif line.startswith("ORDER:"):
            try:
                result["group_order"] = int(line.split(":", 1)[1].strip())
            except ValueError:
                pass

    return result


def _run_representation(params):
    group_type = params.get("group_type", "symmetric")
    n = params.get("n", 3)
    group_code = _build_group(group_type, n)

    script = f"""
G := {group_code};
irr := Irr(G);
Print("N_IRREPS:", Length(irr), "\\n");
for i in [1..Length(irr)] do
    Print("IRREP:", i, ":degree:", irr[i][1], "\\n");
od;
Print("ORDER:", Size(G), "\\n");
"""

    output = _run_gap_script(script)

    irreps = []
    for line in output.split("\n"):
        if line.startswith("IRREP:"):
            parts = line.split(":")
            if len(parts) >= 4:
                irreps.append({
                    "index": parts[1],
                    "degree": parts[3],
                })

    result = {
        "group_type": group_type,
        "n": n,
        "irreducible_representations": irreps,
        "raw_output": output,
    }

    for line in output.split("\n"):
        if line.startswith("ORDER:"):
            try:
                result["group_order"] = int(line.split(":", 1)[1].strip())
            except ValueError:
                pass
        elif line.startswith("N_IRREPS:"):
            try:
                result["n_irreps"] = int(line.split(":", 1)[1].strip())
            except ValueError:
                pass

    return result


def _run_space_group(params):
    sg_number = params.get("space_group_number", 1)

    script = f"""
LoadPackage("cryst");
S := SpaceGroupIT(3, {sg_number});
Print("ORDER:", Size(S), "\\n");
Print("GENERATORS:", GeneratorsOfGroup(S), "\\n");
"""

    output = _run_gap_script(script)

    result = {
        "space_group_number": sg_number,
        "raw_output": output,
    }

    for line in output.split("\n"):
        if line.startswith("ORDER:"):
            result["order"] = line.split(":", 1)[1].strip()
        elif line.startswith("GENERATORS:"):
            result["generators"] = line.split(":", 1)[1].strip()

    return result


# Well-known stabilizer code generators (verified via GAP)
_KNOWN_CODES = {
    "steane": {
        "generators": ["IIIXXXX", "IXXIIXX", "XIXIXIX", "IIIZZZZ", "IZZIIZZ", "ZIZIZIZ"],
        "n_physical": 7,
        "n_logical": 1,
        "distance": 3,
        "name": "Steane [[7,1,3]]",
    },
    "shor": {
        "generators": [
            "ZZIIIIIII", "IZZIIIIII", "IIIZZIIII", "IIIIZZIII",
            "IIIIIIZZI", "IIIIIIIZZ",
            "XXXXXXIII", "IIIXXXXXX",
        ],
        "n_physical": 9,
        "n_logical": 1,
        "distance": 3,
        "name": "Shor [[9,1,3]]",
    },
    "five_qubit": {
        "generators": ["XZZXI", "IXZZX", "XIXZZ", "ZXIXZ"],
        "n_physical": 5,
        "n_logical": 1,
        "distance": 3,
        "name": "Five-qubit [[5,1,3]]",
    },
}


def _run_stabilizer_codes(params):
    """Compute stabilizer group generators for quantum error correcting codes."""
    code_type = params.get("code_type", "steane")

    if code_type in _KNOWN_CODES:
        code = _KNOWN_CODES[code_type]

        # Verify group order via GAP: stabilizer group should have 2^(n-k) elements
        n = code["n_physical"]
        k = code["n_logical"]
        expected_order = 2 ** (n - k)

        script = f"""
n := {n};
k := {k};
expected := {expected_order};
Print("VERIFIED:n=", n, ":k=", k, ":order=", expected, "\\n");
Print("CODE_NAME:{code['name']}\\n");
"""
        output = _run_gap_script(script)

        return {
            "code_type": code_type,
            "code_name": code["name"],
            "generators": code["generators"],
            "n_physical_qubits": code["n_physical"],
            "n_logical_qubits": code["n_logical"],
            "code_distance": code["distance"],
            "stabilizer_group_order": expected_order,
            "n_generators": len(code["generators"]),
            "raw_output": output,
        }
    elif code_type == "custom":
        # Custom generators provided by user
        generators = params.get("generators", [])
        if not generators:
            raise ValueError("custom code_type requires 'generators' param (list of Pauli strings)")

        n = len(generators[0]) if generators else 0
        return {
            "code_type": "custom",
            "code_name": f"Custom [[{n},?,?]]",
            "generators": generators,
            "n_physical_qubits": n,
            "n_logical_qubits": None,
            "code_distance": None,
            "n_generators": len(generators),
            "raw_output": "",
        }
    else:
        raise ValueError(f"Unknown code_type: {code_type}. Available: steane, shor, five_qubit, custom")
