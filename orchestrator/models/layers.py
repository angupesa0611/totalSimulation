from pydantic import BaseModel


class ToolConfig(BaseModel):
    name: str
    key: str
    description: str
    layer: str
    queue: str


class LayerConfig(BaseModel):
    name: str
    key: str
    description: str
    tools: list[ToolConfig]


class PresetInfo(BaseModel):
    key: str
    tool: str
    label: str
    description: str
    example_file: str
