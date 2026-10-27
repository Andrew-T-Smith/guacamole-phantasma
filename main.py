from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from orchestrator import spawn_session, destroy_all_sessions
from guac_utils import generate_vm_guacamole_link
from contextlib import asynccontextmanager
import uuid
import os
from dotenv import load_dotenv
from sqlmodel import Session, select
from database import engine
from models import Machine, MachineCreate, MachineRename

load_dotenv()

key = os.getenv("PASSWORD")

def startup_functions():
    destroy_all_sessions("/var/lib/libvirt/images/overlays/")

def shutdown_functions():
    # shutdown functions here
    pass

# Startup and shutdown actions
@asynccontextmanager
async def lifespan(app: FastAPI):
    startup_functions()
    yield
    shutdown_functions()

app = FastAPI(lifespan=lifespan)

@app.get("/", response_class=HTMLResponse)
def root():
    with open("index.html", "r") as file:
        return file.read()

@app.get("/api/machines/")
def get_machines():
    with Session(engine) as session:
        statement = select(Machine)
        machines = session.exec(statement).all()

        return [
            {
                "id": m.id,
                "name": m.name,
                "display_name": m.display_name
            }
            for m in machines
        ]

@app.post("/api/launch/id/{machine_id}")
def launch_vm(machine_id: int):
    with Session(engine) as session:
        machine = session.get(Machine, machine_id)

        if not machine:
            raise HTTPException(status_code=404, detail=f"Machine '{machine_id}' not found.")

        session_uuid = str(uuid.uuid4())
        session_details = spawn_session(session_uuid, machine.overlay_path, machine.template_xml_path, machine.name)

        connection_link = generate_vm_guacamole_link("admin", session_details["vm_name"], session_details["vnc_port"], bytes.fromhex(key), bytes.fromhex(key), "http://192.168.1.177:7654/guacamole/#/?data=")
        return {"url": connection_link}

# Create a new machine definition
@app.post("/api/machines/", status_code=201)
def create_machine(machine_in: MachineCreate):
    # Validate that the passed paths are valid files
    if not os.path.isfile(machine_in.overlay_path):
        raise HTTPException(status_code=400, detail=f"Image '{machine_in.overlay_path}' not found.")
    if not os.path.isfile(machine_in.template_xml_path):
        raise HTTPException(status_code=400, detail=f"Template '{machine_in.template_xml_path}' not found.")

    with Session(engine) as session:
        # Ensure a machine with the same name does not already exist
        existing = session.exec(select(Machine).where(Machine.name == machine_in.name)).first()
        if existing:
            raise HTTPException(status_code=409, detail=f"Machine '{machine_in.name}' already exists.")

        # Convert the client input into a database row, then insert it
        machine = Machine.model_validate(machine_in)
        session.add(machine)
        session.commit()
        # Reload from the database so machine.id holds the value it assigned
        session.refresh(machine)

        # Paths are left out of the response on purpose
        return {
            "id": machine.id,
            "name": machine.name,
            "display_name": machine.display_name
        }

# Remove a machine definition
@app.delete("/api/machines/{machine_id}", status_code=204)
def delete_machine(machine_id: int):
    with Session(engine) as session:
        machine = session.get(Machine, machine_id)

        if not machine:
            raise HTTPException(status_code=404, detail=f"Machine '{machine_id}' not found.")

        # Only the database row is removed; the image and template files are left alone
        session.delete(machine)
        session.commit()

# Rename a machine's display name
@app.patch("/api/machines/{machine_id}", status_code=200)
def rename_machine_display_name(machine_id: int, rename_in: MachineRename):
    with Session(engine) as session:
        machine = session.get(Machine, machine_id)

        if not machine:
            raise HTTPException(status_code=404, detail=f"Machine '{machine_id}' not found.")

        machine.display_name = rename_in.display_name
        session.add(machine)
        session.commit()
        session.refresh(machine)

        return {
            "id": machine.id,
            "name": machine.name,
            "display_name": machine.display_name
        }
