"""Registry schema ORM models — tools, layers, presets, couplings, pipelines."""

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base


class Layer(Base):
    __tablename__ = "layers"
    __table_args__ = {"schema": "registry"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    tools: Mapped[list["Tool"]] = relationship(back_populates="layer")


class Tool(Base):
    __tablename__ = "tools"
    __table_args__ = {"schema": "registry"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    layer_id: Mapped[int] = mapped_column(ForeignKey("registry.layers.id"), nullable=False)
    queue: Mapped[str] = mapped_column(String(100), nullable=False)
    task: Mapped[str] = mapped_column(String(200), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    deferred: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    container_service: Mapped[str | None] = mapped_column(String(100), nullable=True)

    layer: Mapped["Layer"] = relationship(back_populates="tools")
    presets: Mapped[list["Preset"]] = relationship(back_populates="tool")


class Preset(Base):
    __tablename__ = "presets"
    __table_args__ = {"schema": "registry"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    key: Mapped[str] = mapped_column(String(150), unique=True, nullable=False, index=True)
    tool_id: Mapped[int] = mapped_column(ForeignKey("registry.tools.id"), nullable=False)
    label: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    example_file: Mapped[str] = mapped_column(String(200), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")

    tool: Mapped["Tool"] = relationship(back_populates="presets")


class Coupling(Base):
    __tablename__ = "couplings"
    __table_args__ = {"schema": "registry"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    key: Mapped[str] = mapped_column(String(150), unique=True, nullable=False, index=True)
    from_tool_id: Mapped[int] = mapped_column(ForeignKey("registry.tools.id"), nullable=False)
    to_tool_id: Mapped[int] = mapped_column(ForeignKey("registry.tools.id"), nullable=False)
    coupling_type: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    default_param_map: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    deferred: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    # Some couplings reference a different tool (e.g. qmmm_concurrent -> tool: "qmmm")
    coupling_tool: Mapped[str | None] = mapped_column(String(100), nullable=True)

    from_tool: Mapped["Tool"] = relationship(foreign_keys=[from_tool_id])
    to_tool: Mapped["Tool"] = relationship(foreign_keys=[to_tool_id])


class Pipeline(Base):
    __tablename__ = "pipelines"
    __table_args__ = {"schema": "registry"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    key: Mapped[str] = mapped_column(String(150), unique=True, nullable=False, index=True)
    label: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")

    steps: Mapped[list["PipelineStep"]] = relationship(
        back_populates="pipeline", order_by="PipelineStep.step_order"
    )


class PipelineStep(Base):
    __tablename__ = "pipeline_steps"
    __table_args__ = {"schema": "registry"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pipeline_id: Mapped[int] = mapped_column(ForeignKey("registry.pipelines.id", ondelete="CASCADE"), nullable=False)
    step_order: Mapped[int] = mapped_column(Integer, nullable=False)
    tool_id: Mapped[int] = mapped_column(ForeignKey("registry.tools.id"), nullable=False)
    label: Mapped[str | None] = mapped_column(String(200), nullable=True)
    params: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    param_map: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    pipeline: Mapped["Pipeline"] = relationship(back_populates="steps")
    tool: Mapped["Tool"] = relationship()


class PipelinePreset(Base):
    __tablename__ = "pipeline_presets"
    __table_args__ = {"schema": "registry"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    key: Mapped[str] = mapped_column(String(150), unique=True, nullable=False, index=True)
    pipeline_id: Mapped[int] = mapped_column(ForeignKey("registry.pipelines.id"), nullable=False)
    label: Mapped[str] = mapped_column(String(200), nullable=False)
    example_file: Mapped[str] = mapped_column(String(200), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")

    pipeline: Mapped["Pipeline"] = relationship()


class CouplingPreset(Base):
    __tablename__ = "coupling_presets"
    __table_args__ = {"schema": "registry"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    key: Mapped[str] = mapped_column(String(150), unique=True, nullable=False, index=True)
    coupling_id: Mapped[int] = mapped_column(ForeignKey("registry.couplings.id"), nullable=False)
    label: Mapped[str] = mapped_column(String(200), nullable=False)
    from_tool_key: Mapped[str] = mapped_column(String(100), nullable=False)
    to_tool_key: Mapped[str] = mapped_column(String(100), nullable=False)
    example_file: Mapped[str] = mapped_column(String(200), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")

    coupling: Mapped["Coupling"] = relationship()
