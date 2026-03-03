from abc import ABC, abstractmethod
from typing import Any, Generator


class SimulationTool(ABC):
    """Abstract base class for all simulation tools."""

    name: str
    key: str
    layer: str

    @abstractmethod
    def validate_params(self, params: dict[str, Any]) -> dict[str, Any]:
        """Validate and normalize input parameters. Returns cleaned params."""
        ...

    @abstractmethod
    def run(self, params: dict[str, Any]) -> dict[str, Any]:
        """Run the simulation synchronously. Returns result data dict."""
        ...

    def stream(self, params: dict[str, Any]) -> Generator[dict[str, Any], None, None]:
        """Yield intermediate results for streaming. Default: no streaming."""
        yield from ()

    def get_default_params(self) -> dict[str, Any]:
        """Return default parameters for this tool."""
        return {}
