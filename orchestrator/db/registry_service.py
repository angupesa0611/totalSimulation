"""In-memory registry cache loaded from PostgreSQL.

Hot-path reads hit memory (same speed as hardcoded dicts).
DB only hit on startup and cache invalidation.
"""

import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from db.engine import sync_session_factory
from db.models.registry import (
    Layer, Tool, Preset, Coupling, Pipeline, PipelineStep,
    PipelinePreset, CouplingPreset,
)

logger = logging.getLogger(__name__)

# --- Cache storage ---
_tool_registry: dict[str, dict] = {}
_layers: dict[str, dict] = {}
_presets: dict[str, dict] = {}
_couplings: dict[str, dict] = {}
_pipelines: dict[str, dict] = {}
_pipeline_presets: dict[str, dict] = {}
_coupling_presets: dict[str, dict] = {}
_loaded: bool = False


def load_cache() -> None:
    """Load entire registry from DB into memory cache."""
    global _tool_registry, _layers, _presets, _couplings
    global _pipelines, _pipeline_presets, _coupling_presets, _loaded

    session: Session = sync_session_factory()
    try:
        # Layers with tools eagerly loaded
        layers_q = session.execute(
            select(Layer).options(selectinload(Layer.tools)).order_by(Layer.sort_order)
        )
        layers_rows = layers_q.scalars().all()

        new_layers: dict[str, dict] = {}
        new_tools: dict[str, dict] = {}
        layer_key_by_id: dict[int, str] = {}

        for layer in layers_rows:
            layer_key_by_id[layer.id] = layer.key
            tool_keys = []
            for tool in layer.tools:
                if tool.enabled:
                    tool_keys.append(tool.key)
                # Always include in tool_registry (even disabled — callers check enabled)
                new_tools[tool.key] = {
                    "name": tool.name,
                    "description": tool.description,
                    "layer": layer.key,
                    "queue": tool.queue,
                    "task": tool.task,
                    "enabled": tool.enabled,
                    "deferred": tool.deferred,
                    "container_service": tool.container_service,
                }

            new_layers[layer.key] = {
                "name": layer.name,
                "description": layer.description,
                "tools": tool_keys,
                "enabled": layer.enabled,
            }

        # Presets
        presets_q = session.execute(select(Preset).options(selectinload(Preset.tool)))
        new_presets: dict[str, dict] = {}
        for preset in presets_q.scalars().all():
            new_presets[preset.key] = {
                "tool": preset.tool.key,
                "label": preset.label,
                "description": preset.description,
                "example_file": preset.example_file,
                "enabled": preset.enabled,
            }

        # Couplings
        couplings_q = session.execute(
            select(Coupling)
            .options(selectinload(Coupling.from_tool), selectinload(Coupling.to_tool))
        )
        new_couplings: dict[str, dict] = {}
        for coup in couplings_q.scalars().all():
            entry: dict[str, Any] = {
                "from": coup.from_tool.key,
                "to": coup.to_tool.key,
                "type": coup.coupling_type,
                "description": coup.description,
                "default_param_map": coup.default_param_map or {},
                "enabled": coup.enabled,
                "deferred": coup.deferred,
            }
            if coup.coupling_tool:
                entry["tool"] = coup.coupling_tool
            new_couplings[coup.key] = entry

        # Pipelines with steps
        pipelines_q = session.execute(
            select(Pipeline).options(
                selectinload(Pipeline.steps).selectinload(PipelineStep.tool)
            )
        )
        new_pipelines: dict[str, dict] = {}
        for pipe in pipelines_q.scalars().all():
            steps_list = []
            for step in sorted(pipe.steps, key=lambda s: s.step_order):
                step_dict: dict[str, Any] = {
                    "tool": step.tool.key,
                    "params": step.params or {},
                }
                if step.label:
                    step_dict["label"] = step.label
                if step.param_map:
                    step_dict["param_map"] = step.param_map
                steps_list.append(step_dict)
            new_pipelines[pipe.key] = {
                "label": pipe.label,
                "description": pipe.description,
                "steps": steps_list,
                "enabled": pipe.enabled,
            }

        # Pipeline presets
        pp_q = session.execute(
            select(PipelinePreset).options(selectinload(PipelinePreset.pipeline))
        )
        new_pp: dict[str, dict] = {}
        for pp in pp_q.scalars().all():
            new_pp[pp.key] = {
                "pipeline": pp.pipeline.key,
                "label": pp.label,
                "example_file": pp.example_file,
                "enabled": pp.enabled,
            }

        # Coupling presets
        cp_q = session.execute(select(CouplingPreset))
        new_cp: dict[str, dict] = {}
        for cp in cp_q.scalars().all():
            new_cp[cp.key] = {
                "coupling": cp.key.replace("coupling_", "", 1) if cp.key.startswith("coupling_") else cp.key,
                "label": cp.label,
                "from": cp.from_tool_key,
                "to": cp.to_tool_key,
                "example_file": cp.example_file,
                "enabled": cp.enabled,
            }

        # Swap caches atomically
        _tool_registry = new_tools
        _layers = new_layers
        _presets = new_presets
        _couplings = new_couplings
        _pipelines = new_pipelines
        _pipeline_presets = new_pp
        _coupling_presets = new_cp
        _loaded = True

        logger.info(
            "Registry cache loaded: %d layers, %d tools, %d presets, "
            "%d couplings, %d pipelines, %d pipeline presets, %d coupling presets",
            len(new_layers), len(new_tools), len(new_presets),
            len(new_couplings), len(new_pipelines), len(new_pp), len(new_cp),
        )
    finally:
        session.close()


def invalidate_cache() -> None:
    """Reload the entire cache from DB."""
    load_cache()


def _ensure_loaded() -> None:
    """Lazy-load on first access if not yet loaded."""
    if not _loaded:
        load_cache()


# --- Public accessors (identical dict shapes to config.py) ---

def get_tool_registry() -> dict[str, dict]:
    _ensure_loaded()
    return _tool_registry


def get_layers() -> dict[str, dict]:
    _ensure_loaded()
    return _layers


def get_presets() -> dict[str, dict]:
    _ensure_loaded()
    return _presets


def get_couplings() -> dict[str, dict]:
    _ensure_loaded()
    return _couplings


def get_pipelines() -> dict[str, dict]:
    _ensure_loaded()
    return _pipelines


def get_pipeline_presets() -> dict[str, dict]:
    _ensure_loaded()
    return _pipeline_presets


def get_coupling_presets() -> dict[str, dict]:
    _ensure_loaded()
    return _coupling_presets


# --- Admin mutations ---

def toggle_tool(tool_key: str, enabled: bool) -> bool:
    """Toggle a tool's enabled state. Returns True if found."""
    session: Session = sync_session_factory()
    try:
        tool = session.execute(
            select(Tool).where(Tool.key == tool_key)
        ).scalar_one_or_none()
        if not tool:
            return False
        tool.enabled = enabled
        session.commit()
        invalidate_cache()
        return True
    finally:
        session.close()


def toggle_layer(layer_key: str, enabled: bool) -> bool:
    """Toggle a layer's enabled state. Returns True if found."""
    session: Session = sync_session_factory()
    try:
        layer = session.execute(
            select(Layer).where(Layer.key == layer_key)
        ).scalar_one_or_none()
        if not layer:
            return False
        layer.enabled = enabled
        session.commit()
        invalidate_cache()
        return True
    finally:
        session.close()


def toggle_coupling(coupling_key: str, enabled: bool) -> bool:
    """Toggle a coupling's enabled state. Returns True if found."""
    session: Session = sync_session_factory()
    try:
        coupling = session.execute(
            select(Coupling).where(Coupling.key == coupling_key)
        ).scalar_one_or_none()
        if not coupling:
            return False
        coupling.enabled = enabled
        session.commit()
        invalidate_cache()
        return True
    finally:
        session.close()


def toggle_pipeline(pipeline_key: str, enabled: bool) -> bool:
    """Toggle a pipeline's enabled state. Returns True if found."""
    session: Session = sync_session_factory()
    try:
        pipeline = session.execute(
            select(Pipeline).where(Pipeline.key == pipeline_key)
        ).scalar_one_or_none()
        if not pipeline:
            return False
        pipeline.enabled = enabled
        session.commit()
        invalidate_cache()
        return True
    finally:
        session.close()
