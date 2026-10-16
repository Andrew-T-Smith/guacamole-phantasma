from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from orchestrator import spawn_session
from orchestrator import destroy_all_sessions
from guac_utils import generate_vm_guacamole_link
from contextlib import asynccontextmanager
import uuid
import os
from dotenv import load_dotenv
import yaml
import json
from fastapi.responses import HTMLResponse
from fastapi import HTTPException


#Placeholder
def startup_functions():
    destroy_all_sessions("/var/lib/libvirt/images/overlays/")

def shutdown_functions():
    #my code here
    pass

def read_machine_yaml():
    with open("machines.yml", "r") as file:
        data = yaml.safe_load(file)

    return data

@asynccontextmanager
async def lifespan(app: FastAPI):
    startup_functions()
    yield
    shutdown_functions()

app = FastAPI(lifespan=lifespan)

@app.get("/", response_class=HTMLResponse)
async def root():
    with open("index.html", "r") as file:
        return file.read()
#    session_uuid = str(uuid.uuid4())
#    print(session_uuid)
#    session_details = spawn_session(session_uuid, "/var/lib/libvirt/images/masters/Windows-XP-SP3-Clean-Install.qcow2", "/var/lib/libvirt/images/templates/Windows-XP-SP3-Clean-Install.xml", "Windows-XP-hardcoded-test")

#    connection_link = generate_vm_guacamole_link("admin", session_details["vm_name"], session_details["vnc_port"], bytes.fromhex(key), bytes.fromhex(key), "http://192.168.1.177:7654/guacamole/#/?data=")

#    return RedirectResponse(url=connection_link)


load_dotenv()

key = os.getenv("PASSWORD")

@app.get("/api/machines/")
async def getMachines():
    return read_machine_yaml()

@app.post("/api/launch/{machine_name}")
async def launch_vm(machine_name: str):
    machines = read_machine_yaml()

    target_machine_info = None

    for machine in machines['machines']:
        if machine['name'] == machine_name:
            target_machine_info = machine

    if target_machine_info is not None:
        session_uuid = str(uuid.uuid4())
        session_details = spawn_session(session_uuid, target_machine_info['overlay'], target_machine_info['template'], target_machine_info['name'])

        connection_link = generate_vm_guacamole_link("admin", session_details["vm_name"], session_details["vnc_port"], bytes.fromhex(key), bytes.fromhex(key), "http://192.168.1.177:7654/guacamole/#/?data=")
        return{"status": "success", "url": connection_link}
    else:
        raise HTTPException(status_code=404, detail=f"Machine '{machine_name}' not found.")
