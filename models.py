from sqlmodel import Field, SQLModel, create_engine

class Machine(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    display_name: str | None = None
    template_xml_path: str
    overlay_path: str

# Fields the client supplies when creating a machine (no id, the database assigns it)
class MachineCreate(SQLModel):
    name: str
    display_name: str | None = None
    template_xml_path: str
    overlay_path: str

# The new display name when renaming a machine (None clears it)
class MachineRename(SQLModel):
    display_name: str | None = None
