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


@app.task(name="tools.lean4_tool.run_lean4", bind=True)
def run_lean4(self, params, project="_default", label=None):
    self.update_state(state="PROGRESS", meta={"progress": 0.0, "message": "Starting Lean 4 verification"})

    sim_type = params.get("simulation_type", "verify_statement")
    lean_code = params.get("lean_code", "")
    timeout_s = params.get("timeout_s", 60)

    if not lean_code:
        raise ValueError("lean_code is required")

    try:
        if sim_type == "verify_statement":
            result = _verify_statement(lean_code, timeout_s)
        elif sim_type == "check_proof":
            result = _check_proof(lean_code, timeout_s)
        elif sim_type == "type_check":
            result = _type_check(lean_code, timeout_s)
        else:
            raise ValueError(f"Unknown simulation_type: {sim_type}")
    except Exception as e:
        raise

    result["tool"] = "lean4"
    result["simulation_type"] = sim_type

    self.update_state(state="PROGRESS", meta={"progress": 0.9, "message": "Saving results"})
    _save_result(self.request.id, "lean4", result, project, label)
    return result


def _run_lean(lean_code, timeout_s):
    """Write Lean 4 code to temp file and run lean CLI."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".lean", delete=False) as f:
        f.write(lean_code)
        f.flush()
        lean_file = f.name

    try:
        proc = subprocess.run(
            ["lean", lean_file],
            capture_output=True,
            text=True,
            timeout=timeout_s,
        )
        return {
            "stdout": proc.stdout,
            "stderr": proc.stderr,
            "returncode": proc.returncode,
        }
    except subprocess.TimeoutExpired:
        return {
            "stdout": "",
            "stderr": f"Lean verification timed out after {timeout_s}s",
            "returncode": -1,
        }
    finally:
        os.unlink(lean_file)


def _verify_statement(lean_code, timeout_s):
    result = _run_lean(lean_code, timeout_s)

    verified = result["returncode"] == 0 and "error" not in result["stderr"].lower()

    messages = []
    errors = []

    for line in result["stderr"].split("\n"):
        line = line.strip()
        if not line:
            continue
        if "error" in line.lower():
            errors.append(line)
        elif "warning" in line.lower() or "info" in line.lower():
            messages.append(line)

    if result["stdout"].strip():
        messages.append(result["stdout"].strip())

    return {
        "verified": verified,
        "messages": messages,
        "errors": errors,
        "proof_term": result["stdout"].strip() if verified else "",
    }


def _check_proof(lean_code, timeout_s):
    return _verify_statement(lean_code, timeout_s)


def _type_check(lean_code, timeout_s):
    # Wrap in #check if not already
    if not lean_code.strip().startswith("#check"):
        lean_code = f"#check {lean_code}"

    result = _run_lean(lean_code, timeout_s)

    verified = result["returncode"] == 0
    messages = [result["stdout"].strip()] if result["stdout"].strip() else []
    errors = [result["stderr"].strip()] if result["stderr"].strip() and "error" in result["stderr"].lower() else []

    return {
        "verified": verified,
        "messages": messages,
        "errors": errors,
        "proof_term": "",
    }
