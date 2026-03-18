import json
import os
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


@app.task(name="tools.sagemath_tool.run_sagemath", bind=True)
def run_sagemath(self, params, project="_default", label=None):
    self.update_state(state="PROGRESS", meta={"progress": 0.0, "message": "Starting SageMath computation"})

    sim_type = params.get("simulation_type", "polynomial_algebra")

    try:
        if sim_type == "polynomial_algebra":
            result = _run_polynomial_algebra(params)
        elif sim_type == "number_theory":
            result = _run_number_theory(params)
        elif sim_type == "combinatorics":
            result = _run_combinatorics(params)
        elif sim_type == "differential_geometry":
            result = _run_differential_geometry(params)
        elif sim_type == "coding_theory":
            result = _run_coding_theory(params)
        else:
            raise ValueError(f"Unknown simulation_type: {sim_type}")
    except Exception as e:
        raise

    self.update_state(state="PROGRESS", meta={"progress": 0.9, "message": "Saving results"})
    _save_result(self.request.id, "sagemath", result, project, label)
    return result


def _run_polynomial_algebra(params):
    from sage.all import PolynomialRing, QQ, ZZ, GF, latex

    ring_name = params.get("ring", "QQ")
    poly_strs = params.get("polynomials", ["x^2 + y^2 - 1", "x - y"])
    operation = params.get("operation", "groebner")

    # Determine variables from polynomials
    var_names = set()
    for p in poly_strs:
        for ch in p:
            if ch.isalpha():
                var_names.add(ch)
    var_names = sorted(var_names) or ["x"]

    # Build ring
    if ring_name == "QQ":
        base = QQ
    elif ring_name == "ZZ":
        base = ZZ
    elif ring_name.startswith("GF("):
        p = int(ring_name[3:-1])
        base = GF(p)
    else:
        base = QQ

    R = PolynomialRing(base, var_names)
    gens = R.gens()
    local_dict = {name: gen for name, gen in zip(var_names, gens)}

    polys = [R(p) for p in poly_strs]

    if operation == "groebner":
        from sage.all import ideal
        I = R.ideal(polys)
        gb = I.groebner_basis()
        result_data = [str(g) for g in gb]
        result_latex = [str(latex(g)) for g in gb]
    elif operation == "factor":
        results = [(str(p.factor()), str(latex(p.factor()))) for p in polys]
        result_data = [r[0] for r in results]
        result_latex = [r[1] for r in results]
    elif operation == "gcd":
        from sage.all import gcd
        g = gcd(polys[0], polys[1]) if len(polys) >= 2 else polys[0]
        result_data = str(g)
        result_latex = str(latex(g))
    elif operation == "resultant":
        if len(polys) >= 2 and len(gens) >= 1:
            res = polys[0].resultant(polys[1], gens[0])
            result_data = str(res)
            result_latex = str(latex(res))
        else:
            result_data = "Need 2 polynomials"
            result_latex = result_data
    else:
        raise ValueError(f"Unknown operation: {operation}")

    return {
        "tool": "sagemath",
        "simulation_type": "polynomial_algebra",
        "ring": ring_name,
        "polynomials": poly_strs,
        "operation": operation,
        "result": result_data,
        "result_latex": result_latex,
    }


def _run_number_theory(params):
    from sage.all import Integer, factor, euler_phi, is_prime, continued_fraction, latex

    number = Integer(params.get("number", 60))
    operation = params.get("operation", "factor")

    if operation == "factor":
        f = factor(number)
        result_data = str(f)
        result_latex = str(latex(f))
    elif operation == "primality":
        result_data = bool(is_prime(number))
        result_latex = f"\\text{{{number} is {'prime' if result_data else 'composite'}}}"
    elif operation == "euler_phi":
        phi = euler_phi(number)
        result_data = int(phi)
        result_latex = f"\\phi({number}) = {phi}"
    elif operation == "continued_fraction":
        cf = continued_fraction(number)
        result_data = str(cf)
        result_latex = str(latex(cf))
    else:
        raise ValueError(f"Unknown operation: {operation}")

    return {
        "tool": "sagemath",
        "simulation_type": "number_theory",
        "number": int(number),
        "operation": operation,
        "result": result_data,
        "result_latex": result_latex,
    }


def _run_combinatorics(params):
    from sage.all import Partitions, Permutations, binomial, latex

    n = params.get("n", 5)
    k = params.get("k", 3)
    operation = params.get("operation", "partitions")

    if operation == "partitions":
        parts = list(Partitions(n))
        result_data = {
            "count": len(parts),
            "partitions": [list(p) for p in parts[:50]],  # limit output
        }
        result_latex = f"|P({n})| = {len(parts)}"
    elif operation == "permutations":
        perms = Permutations(n)
        count = perms.cardinality()
        result_data = {
            "count": int(count),
            "sample": [list(p) for p in list(perms)[:20]],
        }
        result_latex = f"|S_{n}| = {count}"
    elif operation == "graphs":
        from sage.all import graphs
        g_list = list(graphs(n))[:20]
        result_data = {
            "count": len(g_list),
            "graphs": [{"vertices": g.order(), "edges": g.size()} for g in g_list],
        }
        result_latex = f"\\text{{Graphs on {n} vertices: {len(g_list)}+}}"
    elif operation == "lattice":
        result_data = {
            "binomial": int(binomial(n, k)),
        }
        result_latex = f"\\binom{{{n}}}{{{k}}} = {binomial(n, k)}"
    else:
        raise ValueError(f"Unknown operation: {operation}")

    return {
        "tool": "sagemath",
        "simulation_type": "combinatorics",
        "n": n,
        "k": k,
        "operation": operation,
        "result": result_data,
        "result_latex": result_latex,
    }


def _run_differential_geometry(params):
    from sage.all import Manifold, latex

    manifold_dim = params.get("manifold_dim", 2)
    compute = params.get("compute", "christoffel")

    M = Manifold(manifold_dim, "M", structure="Riemannian")
    chart = M.chart("x y" if manifold_dim == 2 else "x y z")

    # Default: sphere metric
    metric_data = params.get("metric")
    g = M.metric("g")

    if metric_data and isinstance(metric_data, list):
        coords = list(chart[:])
        for i in range(manifold_dim):
            for j in range(i, manifold_dim):
                idx = i * manifold_dim + j
                if idx < len(metric_data) and metric_data[idx]:
                    from sage.all import SR
                    g[i, j] = SR(metric_data[idx])
    else:
        # Default: Euclidean metric
        for i in range(manifold_dim):
            g[i, i] = 1

    result_data = {}
    result_latex = {}

    if compute == "christoffel":
        nabla = g.connection()
        coeffs = []
        for i in range(manifold_dim):
            for j in range(manifold_dim):
                for k in range(manifold_dim):
                    val = nabla.coef()[[i, j, k]]
                    if val != 0:
                        coeffs.append(f"Gamma^{i}_{j}{k} = {val}")
        result_data = coeffs if coeffs else ["All Christoffel symbols vanish (flat metric)"]
        result_latex = str(latex(nabla.coef()))

    elif compute == "riemann":
        R = g.riemann()
        result_data = str(R.display())
        result_latex = str(latex(R))

    elif compute == "ricci":
        Ric = g.ricci()
        result_data = str(Ric.display())
        result_latex = str(latex(Ric))

    elif compute == "scalar_curvature":
        S = g.ricci_scalar()
        result_data = str(S.display())
        result_latex = str(latex(S))
    else:
        raise ValueError(f"Unknown compute: {compute}")

    return {
        "tool": "sagemath",
        "simulation_type": "differential_geometry",
        "manifold_dim": manifold_dim,
        "compute": compute,
        "result": result_data,
        "result_latex": result_latex,
    }


def _run_coding_theory(params):
    from sage.all import codes, GF, latex

    code_type = params.get("code_type", "linear")
    n = params.get("n", 7)
    k = params.get("k", 4)
    field_size = params.get("field_size", 2)

    F = GF(field_size)

    if code_type == "linear":
        from sage.all import random_matrix
        G = random_matrix(F, k, n)
        C = codes.LinearCode(G)
    elif code_type == "bch":
        C = codes.BCHCode(F, n, k)
    elif code_type == "reed_solomon":
        C = codes.ReedSolomonCode(GF(field_size), n, k)
    else:
        raise ValueError(f"Unknown code_type: {code_type}")

    result_data = {
        "length": C.length(),
        "dimension": C.dimension(),
        "minimum_distance": int(C.minimum_distance()) if C.length() <= 32 else "N/A (too large)",
        "generator_matrix": str(C.generator_matrix()),
    }

    return {
        "tool": "sagemath",
        "simulation_type": "coding_theory",
        "code_type": code_type,
        "n": n,
        "k": k,
        "field_size": field_size,
        "result": result_data,
        "result_latex": str(latex(C.generator_matrix())),
    }
