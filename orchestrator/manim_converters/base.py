"""Base class for tool result to Manim scene params conversion."""


class ManimConverter:
    """Base class for tool result -> Manim scene params conversion.

    Each converter maps one tool's output to one or more Manim scene types.
    The convert() method returns a dict compatible with run_manim params.
    """

    def supported_scenes(self) -> list[dict]:
        """Return list of {scene_type, label, description} this converter supports."""
        raise NotImplementedError

    def convert(self, result: dict, scene_type: str, options: dict = None) -> dict:
        """Convert tool result to Manim task params.

        Returns a dict compatible with run_manim params:
        {"simulation_type": "...", ...scene-specific params...}
        """
        raise NotImplementedError

    def default_scene(self, result: dict) -> str:
        """Return the default scene_type for a given result."""
        scenes = self.supported_scenes()
        return scenes[0]["scene_type"] if scenes else None
