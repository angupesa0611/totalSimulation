"""Seed registry tables from config.py hardcoded dicts.

Used by Alembic data migration 0002 and for manual re-seeding.
"""

import logging
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def seed_registry(session: Session) -> dict:
    """Insert all layers, tools, presets, couplings, pipelines from config.py into DB.

    Returns summary counts.
    """
    # Import config dicts — these are the canonical source for initial data
    from config import (
        TOOL_REGISTRY, LAYERS, PRESETS, COUPLINGS, PIPELINES,
        PIPELINE_PRESETS, COUPLING_PRESETS,
    )
    from docker_manager import TOOL_CONTAINER_MAP
    from db.models.registry import (
        Layer, Tool, Preset, Coupling, Pipeline, PipelineStep,
        PipelinePreset, CouplingPreset,
    )

    counts = {}

    # 1. Layers
    layer_db_map = {}  # key -> Layer ORM instance
    for sort_idx, (key, layer_data) in enumerate(LAYERS.items()):
        layer = Layer(
            key=key,
            name=layer_data["name"],
            description=layer_data["description"],
            enabled=True,
            sort_order=sort_idx,
        )
        session.add(layer)
        layer_db_map[key] = layer
    session.flush()  # Generate IDs
    counts["layers"] = len(layer_db_map)

    # 2. Tools
    tool_db_map = {}  # key -> Tool ORM instance
    for key, tool_data in TOOL_REGISTRY.items():
        layer_key = tool_data["layer"]
        layer_obj = layer_db_map.get(layer_key)
        if not layer_obj:
            logger.warning("Tool '%s' references unknown layer '%s', skipping", key, layer_key)
            continue
        tool = Tool(
            key=key,
            name=tool_data["name"],
            description=tool_data["description"],
            layer_id=layer_obj.id,
            queue=tool_data["queue"],
            task=tool_data["task"],
            enabled=True,
            deferred=tool_data.get("deferred", False),
            container_service=TOOL_CONTAINER_MAP.get(key),
        )
        session.add(tool)
        tool_db_map[key] = tool
    session.flush()
    counts["tools"] = len(tool_db_map)

    # 3. Presets
    preset_count = 0
    for key, preset_data in PRESETS.items():
        tool_key = preset_data["tool"]
        tool_obj = tool_db_map.get(tool_key)
        if not tool_obj:
            logger.warning("Preset '%s' references unknown tool '%s', skipping", key, tool_key)
            continue
        preset = Preset(
            key=key,
            tool_id=tool_obj.id,
            label=preset_data["label"],
            description=preset_data["description"],
            example_file=preset_data["example_file"],
            enabled=True,
        )
        session.add(preset)
        preset_count += 1
    session.flush()
    counts["presets"] = preset_count

    # 4. Couplings
    coupling_db_map = {}  # key -> Coupling ORM instance
    coupling_count = 0
    for key, coup_data in COUPLINGS.items():
        from_tool = tool_db_map.get(coup_data["from"])
        to_tool = tool_db_map.get(coup_data["to"])
        if not from_tool or not to_tool:
            logger.warning("Coupling '%s' references unknown tool, skipping", key)
            continue
        coupling = Coupling(
            key=key,
            from_tool_id=from_tool.id,
            to_tool_id=to_tool.id,
            coupling_type=coup_data["type"],
            description=coup_data.get("description"),
            default_param_map=coup_data.get("default_param_map"),
            enabled=True,
            deferred=coup_data.get("deferred", False),
            coupling_tool=coup_data.get("tool"),
        )
        session.add(coupling)
        coupling_db_map[key] = coupling
        coupling_count += 1
    session.flush()
    counts["couplings"] = coupling_count

    # 5. Pipelines + steps
    pipeline_db_map = {}  # key -> Pipeline ORM instance
    pipeline_count = 0
    step_count = 0
    for key, pipe_data in PIPELINES.items():
        pipeline = Pipeline(
            key=key,
            label=pipe_data["label"],
            description=pipe_data["description"],
            enabled=True,
        )
        session.add(pipeline)
        session.flush()
        pipeline_db_map[key] = pipeline
        pipeline_count += 1

        for i, step_data in enumerate(pipe_data["steps"]):
            tool_key = step_data["tool"]
            tool_obj = tool_db_map.get(tool_key)
            if not tool_obj:
                logger.warning("Pipeline step references unknown tool '%s', skipping", tool_key)
                continue
            step = PipelineStep(
                pipeline_id=pipeline.id,
                step_order=i,
                tool_id=tool_obj.id,
                label=step_data.get("label"),
                params=step_data.get("params"),
                param_map=step_data.get("param_map"),
            )
            session.add(step)
            step_count += 1
    session.flush()
    counts["pipelines"] = pipeline_count
    counts["pipeline_steps"] = step_count

    # 6. Pipeline presets
    pp_count = 0
    for key, pp_data in PIPELINE_PRESETS.items():
        pipe_key = pp_data["pipeline"]
        pipeline_obj = pipeline_db_map.get(pipe_key)
        if not pipeline_obj:
            logger.warning("Pipeline preset '%s' references unknown pipeline '%s', skipping", key, pipe_key)
            continue
        pp = PipelinePreset(
            key=key,
            pipeline_id=pipeline_obj.id,
            label=pp_data["label"],
            example_file=pp_data["example_file"],
            enabled=True,
        )
        session.add(pp)
        pp_count += 1
    session.flush()
    counts["pipeline_presets"] = pp_count

    # 7. Coupling presets
    cp_count = 0
    for key, cp_data in COUPLING_PRESETS.items():
        coupling_key = cp_data["coupling"]
        coupling_obj = coupling_db_map.get(coupling_key)
        if not coupling_obj:
            logger.warning("Coupling preset '%s' references unknown coupling '%s', skipping", key, coupling_key)
            continue
        cp = CouplingPreset(
            key=key,
            coupling_id=coupling_obj.id,
            label=cp_data["label"],
            from_tool_key=cp_data["from"],
            to_tool_key=cp_data["to"],
            example_file=cp_data["example_file"],
            enabled=True,
        )
        session.add(cp)
        cp_count += 1
    session.flush()
    counts["coupling_presets"] = cp_count

    session.commit()
    logger.info("Registry seeded: %s", counts)
    return counts
