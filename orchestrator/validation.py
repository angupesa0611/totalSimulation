"""Per-tool input validation — checks required params, value ranges, types before Celery submission."""

from db.registry_service import get_tool_registry


# Per-tool validation rules: {tool_key: {param: {type, required, min, max, choices}}}
TOOL_VALIDATORS = {
    "rebound": {
        "n_particles": {"type": "int", "required": False, "min": 1, "max": 10000},
        "dt": {"type": "float", "required": False, "min": 1e-10},
        "n_steps": {"type": "int", "required": False, "min": 1, "max": 1000000},
    },
    "qutip": {
        "n_times": {"type": "int", "required": False, "min": 2, "max": 100000},
    },
    "openmm": {
        "steps": {"type": "int", "required": False, "min": 1, "max": 10000000},
        "temperature": {"type": "float", "required": False, "min": 0},
        "dt": {"type": "float", "required": False, "min": 1e-15},
    },
    "pyscf": {
        "atom_coords": {"type": "str", "required": True},
        "basis": {"type": "str", "required": False},
    },
    "sympy": {
        "expression": {"type": "str", "required": False},
    },
    "matplotlib": {
        "plot_type": {"type": "str", "required": False,
                      "choices": ["line", "scatter", "bar", "histogram", "heatmap", "contour"]},
    },
}


def validate_params(tool: str, params: dict) -> list[str]:
    """
    Validate params for a tool. Returns list of error messages (empty = valid).
    Tools without specific validators are accepted as-is.
    """
    errors = []
    rules = TOOL_VALIDATORS.get(tool)
    if not rules:
        return errors  # No specific validation rules

    for param_name, rule in rules.items():
        value = params.get(param_name)

        # Check required
        if rule.get("required") and value is None:
            errors.append(f"Missing required parameter: {param_name}")
            continue

        if value is None:
            continue

        # Type check
        expected_type = rule.get("type")
        if expected_type == "int" and not isinstance(value, int):
            try:
                int(value)
            except (ValueError, TypeError):
                errors.append(f"Parameter '{param_name}' must be an integer, got {type(value).__name__}")
                continue

        if expected_type == "float" and not isinstance(value, (int, float)):
            try:
                float(value)
            except (ValueError, TypeError):
                errors.append(f"Parameter '{param_name}' must be a number, got {type(value).__name__}")
                continue

        if expected_type == "str" and not isinstance(value, str):
            errors.append(f"Parameter '{param_name}' must be a string, got {type(value).__name__}")
            continue

        # Range checks (for numeric values)
        if isinstance(value, (int, float)):
            if "min" in rule and value < rule["min"]:
                errors.append(f"Parameter '{param_name}' must be >= {rule['min']}, got {value}")
            if "max" in rule and value > rule["max"]:
                errors.append(f"Parameter '{param_name}' must be <= {rule['max']}, got {value}")

        # Choices check
        if "choices" in rule and value not in rule["choices"]:
            errors.append(
                f"Parameter '{param_name}' must be one of {rule['choices']}, got '{value}'"
            )

    return errors
