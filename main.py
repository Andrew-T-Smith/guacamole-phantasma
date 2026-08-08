from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from orchestrator import spawn_session
from orchestrator import destroy_all_sessions
from guac_utils import generate_vm_guacamole_link
from contextlib import asynccontextmanager
import uuid
import os
from dotenv import load_dotenv


#Placeholder
def startup_functions():
    destroy_all_sessions("/var/lib/libvirt/images/overlays/")

def shutdown_functions():
    #my code here
    pass

@asynccontextmanager
async def lifespan(app: FastAPI):
    startup_functions()
    yield
    shutdown_functions()

app = FastAPI(lifespan=lifespan)


@app.get("/")
async def root():
    session_uuid = str(uuid.uuid4())
    print(session_uuid)
    session_details = spawn_session(session_uuid, "/var/lib/libvirt/images/masters/Windows-XP-SP3-Clean-Install.qcow2", "/var/lib/libvirt/images/templates/Windows-XP-SP3-Clean-Install.xml", "Windows-XP-hardcoded-test")

    connection_link = generate_vm_guacamole_link("admin", session_details["vm_name"], session_details["vnc_port"], bytes.fromhex(key), bytes.fromhex(key), "http://192.168.1.177:7654/guacamole/#/?data=")

    return RedirectResponse(url=connection_link)


load_dotenv()

key = os.getenv("PASSWORD")
