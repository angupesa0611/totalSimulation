"""Scene registry — maps simulation_type to generator functions."""

SCENE_REGISTRY = {}


def register_scene(sim_type):
    """Decorator to register a scene generator for a simulation_type."""
    def decorator(fn):
        SCENE_REGISTRY[sim_type] = fn
        return fn
    return decorator


def get_scene_generator(sim_type):
    """Return the generator function for a simulation_type, or None."""
    return SCENE_REGISTRY.get(sim_type)


# Import all scene modules to trigger @register_scene decorators
from scenes import math_scenes     # noqa: F401, E402
from scenes import quantum_scenes  # noqa: F401, E402
from scenes import astro_scenes    # noqa: F401, E402
from scenes import molecular_scenes  # noqa: F401, E402
from scenes import biology_scenes  # noqa: F401, E402
from scenes import continuum_scenes  # noqa: F401, E402
from scenes import physics_scenes  # noqa: F401, E402
from scenes import chemistry_scenes  # noqa: F401, E402
from scenes import popgen_scenes   # noqa: F401, E402
from scenes import materials_scenes  # noqa: F401, E402
from scenes import circuit_scenes  # noqa: F401, E402
from scenes import qc_scenes       # noqa: F401, E402
