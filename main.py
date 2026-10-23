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
from models import Machine

load_dotenv()

key = os.getenv("PASSWORD")

def startup_functions():
    destroy_all_sessions("/var/lib/libvirt/images/overlays/")

def shutdown_functions():
    #shutdown functions here
    pass

#Startup and shutdown actions
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
        return{"status": "success", "url": connection_link}
