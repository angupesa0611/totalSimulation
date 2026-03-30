import time
from typing import Any
from celery_app import app as celery_app
from tools.base import SimulationTool
from results import save_result


class PyomoTool(SimulationTool):
    name = "Pyomo"
    key = "pyomo"
    layer = "engineering"

    SIMULATION_TYPES = {"linear_program", "mixed_integer", "nonlinear"}
    AVAILABLE_SOLVERS = {"glpk", "highs", "cbc", "ipopt"}

    def validate_params(self, params: dict[str, Any]) -> dict[str, Any]:
        sim_type = params.get("simulation_type", "linear_program")
        if sim_type not in self.SIMULATION_TYPES:
            raise ValueError(f"Unknown simulation_type: {sim_type}. Supported: {self.SIMULATION_TYPES}")

        solver = params.get("solver", "glpk")
        if solver not in self.AVAILABLE_SOLVERS:
            raise ValueError(f"Unknown solver: {solver}. Available: {self.AVAILABLE_SOLVERS}")

        params.setdefault("simulation_type", sim_type)
        params.setdefault("variables", [])
        params.setdefault("constraints", [])
        params.setdefault("solver", solver)

        # Normalize split objective fields from frontend
        if isinstance(params.get("objective"), str) or "sense" in params:
            expr = params.get("objective", "0")
            if isinstance(expr, dict):
                expr = expr.get("expression", "0")
            sense = params.pop("sense", "minimize")
            params["objective"] = {"expression": expr, "sense": sense}
        params.setdefault("objective", {"expression": "0", "sense": "minimize"})

        return params

    def run(self, params: dict[str, Any]) -> dict[str, Any]:
        params = self.validate_params(params)
        return self._solve_optimization(params)

    def _eval_expression(self, expr_str, namespace):
        """Evaluate a mathematical expression in a sandboxed namespace.

        Security: __builtins__ is set to {} to prevent access to dangerous
        Python builtins. The namespace only contains Pyomo variable objects
        and the pyo module. This is the standard pattern for evaluating
        user-provided mathematical optimization expressions.
        """
        return eval(expr_str, {"__builtins__": {}}, namespace)  # noqa: S307

    def _solve_optimization(self, params):
        import pyomo.environ as pyo

        model = pyo.ConcreteModel()

        # Define variables
        domain_map = {
            "reals": pyo.Reals,
            "integers": pyo.Integers,
            "binary": pyo.Binary,
            "NonNegativeReals": pyo.NonNegativeReals,
            "nonnegativereals": pyo.NonNegativeReals,
            "NonNegativeIntegers": pyo.NonNegativeIntegers,
            "nonnegativeintegers": pyo.NonNegativeIntegers,
        }

        var_objects = {}
        for var_def in params["variables"]:
            name = var_def["name"]
            domain = domain_map.get(var_def.get("domain", "reals"), pyo.Reals)
            lower = var_def.get("lower", None)
            upper = var_def.get("upper", None)

            if domain == pyo.Binary:
                var = pyo.Var(domain=pyo.Binary)
            else:
                var = pyo.Var(domain=domain, bounds=(lower, upper))

            setattr(model, name, var)
            var_objects[name] = getattr(model, name)

        # Build namespace for expression evaluation (sandboxed)
        ns = {name: var for name, var in var_objects.items()}
        ns["pyo"] = pyo

        # Define objective
        obj_expr = params["objective"]["expression"]
        sense_str = params["objective"].get("sense", "minimize")
        sense = pyo.minimize if sense_str == "minimize" else pyo.maximize

        model.obj = pyo.Objective(expr=self._eval_expression(obj_expr, ns), sense=sense)

        # Define constraints
        for i, con_def in enumerate(params["constraints"]):
            expr_str = con_def["expression"]
            con_name = con_def.get("name", f"c{i}")
            con_expr = self._eval_expression(expr_str, ns)
            setattr(model, con_name, pyo.Constraint(expr=con_expr))

        # Solve
        solver_name = params.get("solver", "glpk")
        solver = pyo.SolverFactory(solver_name)

        start_time = time.time()
        results = solver.solve(model, tee=False)
        solver_time = time.time() - start_time

        # Extract results
        status_str = str(results.solver.termination_condition)
        status_map = {
            "optimal": "optimal",
            "infeasible": "infeasible",
            "unbounded": "unbounded",
        }
        status = status_map.get(status_str, status_str)

        variable_values = {}
        for name, var in var_objects.items():
            val = pyo.value(var, exception=False)
            variable_values[name] = float(val) if val is not None else None

        optimal_value = None
        try:
            optimal_value = float(pyo.value(model.obj))
        except Exception:
            pass

        # Constraint slacks
        constraint_slacks = {}
        for con_def in params["constraints"]:
            con_name = con_def.get("name", "")
            if con_name and hasattr(model, con_name):
                con = getattr(model, con_name)
                try:
                    slack = float(con.lslack()) if con.has_lb() else float(con.uslack())
                except Exception:
                    slack = None
                constraint_slacks[con_name] = slack

        return {
            "tool": "pyomo",
            "simulation_type": params["simulation_type"],
            "status": status,
            "optimal_value": optimal_value,
            "variable_values": variable_values,
            "constraint_slacks": constraint_slacks,
            "solver": solver_name,
            "solver_time_s": solver_time,
        }

    def get_default_params(self) -> dict[str, Any]:
        return {
            "simulation_type": "linear_program",
            "variables": [
                {"name": "x1", "lower": 0, "upper": 1, "domain": "binary"},
                {"name": "x2", "lower": 0, "upper": 1, "domain": "binary"},
                {"name": "x3", "lower": 0, "upper": 1, "domain": "binary"},
            ],
            "objective": {"expression": "10*x1 + 20*x2 + 15*x3", "sense": "maximize"},
            "constraints": [
                {"name": "weight", "expression": "5*x1 + 8*x2 + 6*x3 <= 12"},
            ],
            "solver": "glpk",
        }


@celery_app.task(name="tools.pyomo_tool.run_pyomo", bind=True)
def run_pyomo(self, params: dict, project: str = "_default",
              label: str | None = None) -> dict:
    tool = PyomoTool()

    self.update_state(state="PROGRESS", meta={"progress": 0.0, "message": "Starting Pyomo optimization"})

    try:
        sim_type = params.get("simulation_type", "linear_program")
        self.update_state(state="PROGRESS", meta={"progress": 0.1, "message": f"Solving {sim_type}"})
        result = tool.run(params)
    except Exception as e:
        raise

    self.update_state(state="PROGRESS", meta={"progress": 0.9, "message": "Saving results"})
    save_result(self.request.id, "pyomo", result, project, label)

    return result
