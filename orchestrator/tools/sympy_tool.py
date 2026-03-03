from typing import Any
import numpy as np
from celery_app import app as celery_app
from tools.base import SimulationTool
from results import save_result


def _expr_to_ufl(expr_str: str, variables: list[str]) -> str:
    """Convert SymPy expression string to FEniCS UFL code.

    Pipeline helper for SymPy→FEniCS coupling.
    Generates a UFL weak form from a symbolic PDE expression.
    """
    import sympy as sp

    syms = sp.symbols(variables)
    if len(syms) == 1:
        syms = (syms,) if not isinstance(syms, tuple) else syms
    expr = sp.sympify(expr_str)

    # Map SymPy functions to UFL equivalents
    ufl_map = {
        "sin": "ufl.sin",
        "cos": "ufl.cos",
        "exp": "ufl.exp",
        "log": "ufl.ln",
        "sqrt": "ufl.sqrt",
        "Abs": "ufl.abs_value",
    }

    code = sp.printing.pycode(expr)
    for sp_name, ufl_name in ufl_map.items():
        code = code.replace(f"math.{sp_name}", ufl_name)

    # Generate UFL preamble
    var_names = ", ".join(variables)
    ufl_code = f"""import ufl
from dolfinx import fem

# Symbolic source: {expr_str}
# Variables: {var_names}
# Generated UFL expression:
f_expr = {code}
"""
    return ufl_code


class SymPyTool(SimulationTool):
    name = "SymPy"
    key = "sympy"
    layer = "mathematics"

    SIMULATION_TYPES = {"symbolic_solve", "calculus", "matrix_algebra", "ode_solve", "code_generation"}

    def validate_params(self, params: dict[str, Any]) -> dict[str, Any]:
        sim_type = params.get("simulation_type", "symbolic_solve")
        if sim_type not in self.SIMULATION_TYPES:
            raise ValueError(f"Unknown simulation_type: {sim_type}. Supported: {self.SIMULATION_TYPES}")

        params.setdefault("simulation_type", sim_type)
        params.setdefault("variables", ["x"])
        params.setdefault("expression", "x**2 + 2*x + 1")
        return params

    def run(self, params: dict[str, Any]) -> dict[str, Any]:
        params = self.validate_params(params)
        sim_type = params["simulation_type"]

        if sim_type == "symbolic_solve":
            return self._run_symbolic_solve(params)
        elif sim_type == "calculus":
            return self._run_calculus(params)
        elif sim_type == "matrix_algebra":
            return self._run_matrix_algebra(params)
        elif sim_type == "ode_solve":
            return self._run_ode_solve(params)
        elif sim_type == "code_generation":
            return self._run_code_generation(params)

    def _run_symbolic_solve(self, params):
        import sympy as sp

        variables = params.get("variables", ["x"])
        syms = sp.symbols(variables)

        equations_str = params.get("equations", [params.get("expression", "x**2 - 1")])
        solve_for = params.get("solve_for", variables[:1])
        solve_syms = sp.symbols(solve_for)

        # Parse equations
        equations = []
        for eq_str in equations_str:
            if "=" in eq_str and "==" not in eq_str:
                lhs, rhs = eq_str.split("=", 1)
                equations.append(sp.Eq(sp.sympify(lhs.strip()), sp.sympify(rhs.strip())))
            else:
                equations.append(sp.sympify(eq_str.replace("==", "-(")+")") if "==" in eq_str else sp.sympify(eq_str))

        solutions = sp.solve(equations, solve_syms)

        # Format solutions
        if isinstance(solutions, dict):
            sol_formatted = {str(k): str(v) for k, v in solutions.items()}
            sol_latex = {str(k): sp.latex(v) for k, v in solutions.items()}
        elif isinstance(solutions, list):
            sol_formatted = [str(s) for s in solutions]
            sol_latex = [sp.latex(s) if not isinstance(s, tuple) else [sp.latex(x) for x in s] for s in solutions]
        else:
            sol_formatted = str(solutions)
            sol_latex = sp.latex(solutions)

        return {
            "tool": "sympy",
            "simulation_type": "symbolic_solve",
            "equations": equations_str,
            "solutions": sol_formatted,
            "latex": sol_latex,
        }

    def _run_calculus(self, params):
        import sympy as sp

        variables = params.get("variables", ["x"])
        syms = sp.symbols(variables)
        expr = sp.sympify(params.get("expression", "x**2"))
        operation = params.get("operation", "differentiate")
        respect_to = sp.Symbol(params.get("respect_to", variables[0]))

        if operation == "differentiate":
            result = sp.diff(expr, respect_to)
        elif operation == "integrate":
            result = sp.integrate(expr, respect_to)
        elif operation == "limit":
            point = sp.sympify(params.get("point", "oo"))
            result = sp.limit(expr, respect_to, point)
        elif operation == "series":
            order = params.get("order", 6)
            point = sp.sympify(params.get("point", "0"))
            result = sp.series(expr, respect_to, point, n=order)
        else:
            raise ValueError(f"Unknown calculus operation: {operation}")

        # Generate numeric samples for plotting
        numeric_samples = {"x": [], "y": []}
        try:
            f_numeric = sp.lambdify(respect_to, result, modules=["numpy"])
            x_vals = np.linspace(-5, 5, 200)
            y_vals = f_numeric(x_vals)
            if isinstance(y_vals, np.ndarray):
                # Filter out inf/nan
                mask = np.isfinite(y_vals)
                numeric_samples["x"] = x_vals[mask].tolist()
                numeric_samples["y"] = y_vals[mask].tolist()
        except Exception:
            pass

        return {
            "tool": "sympy",
            "simulation_type": "calculus",
            "expression": str(expr),
            "operation": operation,
            "result": str(result),
            "result_latex": sp.latex(result),
            "numeric_samples": numeric_samples,
        }

    def _run_matrix_algebra(self, params):
        import sympy as sp

        matrix_data = params.get("matrix", [[1, 0], [0, 1]])
        M = sp.Matrix(matrix_data)
        operation = params.get("operation", "eigenvalues")

        result_data = {}

        if operation == "eigenvalues":
            eigenvals = M.eigenvals()
            eigenvects = M.eigenvects()
            result_data["eigenvalues"] = [
                {"value": str(val), "multiplicity": mult}
                for val, mult in eigenvals.items()
            ]
            result_data["eigenvectors"] = [
                {"eigenvalue": str(val), "multiplicity": mult,
                 "vectors": [str(v) for v in vects]}
                for val, mult, vects in eigenvects
            ]
            result_data["result"] = str(eigenvals)
            result_data["result_latex"] = sp.latex(eigenvals)

        elif operation == "determinant":
            det = M.det()
            result_data["result"] = str(det)
            result_data["result_latex"] = sp.latex(det)

        elif operation == "inverse":
            inv = M.inv()
            result_data["result"] = str(inv)
            result_data["result_latex"] = sp.latex(inv)
            result_data["inverse_matrix"] = inv.tolist()

        elif operation == "decomposition":
            L, U, perm = M.LUdecomposition()
            result_data["L"] = str(L)
            result_data["U"] = str(U)
            result_data["result"] = f"L = {L}, U = {U}"
            result_data["result_latex"] = f"L = {sp.latex(L)}, U = {sp.latex(U)}"

        else:
            raise ValueError(f"Unknown matrix operation: {operation}")

        return {
            "tool": "sympy",
            "simulation_type": "matrix_algebra",
            "operation": operation,
            "matrix": matrix_data,
            **result_data,
        }

    def _run_ode_solve(self, params):
        import sympy as sp

        var_name = params.get("variable", "x")
        func_name = params.get("function", "f")
        x = sp.Symbol(var_name)
        f = sp.Function(func_name)

        ode_str = params.get("ode", "f(x).diff(x) - f(x)")
        # Replace function notation for parsing
        local_dict = {func_name: f, var_name: x}
        ode_expr = sp.sympify(ode_str, locals=local_dict)

        solution = sp.dsolve(ode_expr, f(x))

        # Generate numeric samples if possible
        numeric_samples = {"x": [], "y": []}
        try:
            # Try with initial condition f(0) = 1
            particular = sp.dsolve(ode_expr, f(x), ics={f(0): 1})
            f_numeric = sp.lambdify(x, particular.rhs, modules=["numpy"])
            x_vals = np.linspace(0, 5, 200)
            y_vals = f_numeric(x_vals)
            if isinstance(y_vals, np.ndarray):
                mask = np.isfinite(y_vals)
                numeric_samples["x"] = x_vals[mask].tolist()
                numeric_samples["y"] = y_vals[mask].tolist()
        except Exception:
            pass

        return {
            "tool": "sympy",
            "simulation_type": "ode_solve",
            "ode": ode_str,
            "solution": str(solution),
            "solution_latex": sp.latex(solution),
            "numeric_samples": numeric_samples,
        }

    def _run_code_generation(self, params):
        import sympy as sp
        from sympy.printing import pycode, ccode, fcode

        variables = params.get("variables", ["x"])
        syms = sp.symbols(variables)
        expr = sp.sympify(params.get("expression", "x**2"))
        target = params.get("target_language", "python")

        if target == "python":
            generated_code = pycode(expr)
        elif target == "c":
            generated_code = ccode(expr)
        elif target == "fortran":
            generated_code = fcode(expr)
        else:
            generated_code = pycode(expr)

        # Generate UFL code for FEniCS coupling
        ufl_code = _expr_to_ufl(str(expr), variables)

        return {
            "tool": "sympy",
            "simulation_type": "code_generation",
            "expression": str(expr),
            "language": target,
            "generated_code": generated_code,
            "ufl_code": ufl_code,
        }

    def get_default_params(self) -> dict[str, Any]:
        return {
            "simulation_type": "symbolic_solve",
            "equations": ["x**2 - 5*x + 6"],
            "solve_for": ["x"],
            "variables": ["x"],
        }


@celery_app.task(name="tools.sympy_tool.run_sympy", bind=True)
def run_sympy(self, params: dict, project: str = "_default",
              label: str | None = None) -> dict:
    tool = SymPyTool()

    self.update_state(state="PROGRESS", meta={"progress": 0.0, "message": "Starting SymPy computation"})

    try:
        sim_type = params.get("simulation_type", "symbolic_solve")
        self.update_state(state="PROGRESS", meta={"progress": 0.1, "message": f"Running {sim_type}"})
        result = tool.run(params)
    except Exception as e:
        self.update_state(state="FAILURE", meta={"message": str(e)})
        raise

    self.update_state(state="PROGRESS", meta={"progress": 0.9, "message": "Saving results"})
    save_result(self.request.id, "sympy", result, project, label)

    return result
