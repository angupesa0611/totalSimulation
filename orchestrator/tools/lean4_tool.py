"""Lean 4 — interactive theorem prover and proof assistant.

Simulation types:
  - verify_statement: Verify a Lean 4 statement/proof
  - check_proof: Check a proof (alias for verify_statement)
  - type_check: Type-check an expression using #check
"""

import os
import subprocess
import tempfile
from typing import Any

from celery_app import app as celery_app
from tools.base import SimulationTool
from results import save_result


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


class Lean4Tool(SimulationTool):
    name = "Lean 4"
    key = "lean4"
    layer = "mathematics"

    SIMULATION_TYPES = {"verify_statement", "check_proof", "type_check"}

    def validate_params(self, params: dict[str, Any]) -> dict[str, Any]:
        sim_type = params.get("simulation_type", "verify_statement")
        if sim_type not in self.SIMULATION_TYPES:
            raise ValueError(f"Unknown simulation_type: {sim_type}. Supported: {self.SIMULATION_TYPES}")
        if not params.get("lean_code"):
            raise ValueError("lean_code is required")
        params.setdefault("simulation_type", sim_type)
        params.setdefault("timeout_s", 60)
        return params

    def run(self, params: dict[str, Any]) -> dict[str, Any]:
        params = self.validate_params(params)
        sim_type = params["simulation_type"]
        lean_code = params["lean_code"]
        timeout_s = params.get("timeout_s", 60)

        if sim_type == "verify_statement":
            result = self._verify_statement(lean_code, timeout_s)
        elif sim_type == "check_proof":
            result = self._check_proof(lean_code, timeout_s)
        elif sim_type == "type_check":
            result = self._type_check(lean_code, timeout_s)

        result["tool"] = "lean4"
        result["simulation_type"] = sim_type
        return result

    def _verify_statement(self, lean_code, timeout_s):
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

    def _check_proof(self, lean_code, timeout_s):
        return self._verify_statement(lean_code, timeout_s)

    def _type_check(self, lean_code, timeout_s):
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

    def get_default_params(self) -> dict[str, Any]:
        return {
            "simulation_type": "verify_statement",
            "lean_code": "#check Nat.add_comm",
            "timeout_s": 60,
        }


@celery_app.task(name="tools.lean4_tool.run_lean4", bind=True)
def run_lean4(self, params: dict, project: str = "_default",
              label: str | None = None) -> dict:
    tool = Lean4Tool()

    self.update_state(state="PROGRESS", meta={"progress": 0.0, "message": "Starting Lean 4 verification"})

    try:
        sim_type = params.get("simulation_type", "verify_statement")
        self.update_state(state="PROGRESS", meta={"progress": 0.1, "message": f"Running {sim_type}"})
        result = tool.run(params)
    except Exception as e:
        raise

    self.update_state(state="PROGRESS", meta={"progress": 0.9, "message": "Saving results"})
    save_result(self.request.id, "lean4", result, project, label)

    return result
