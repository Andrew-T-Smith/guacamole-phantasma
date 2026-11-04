import os
from dotenv import load_dotenv

load_dotenv()

# Hex key shared with Guacamole's JSON auth extension
PASSWORD = os.getenv("PASSWORD")

# Paths
OVERLAY_DIR = os.environ["OVERLAY_DIR"]
MASTERS_DIR = os.environ["MASTERS_DIR"]
TEMPLATES_DIR = os.environ["TEMPLATES_DIR"]

# Database (SQLAlchemy URL)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///database.db")

# libvirt connection
LIBVIRT_URI = os.getenv("LIBVIRT_URI", "qemu:///system")

# Guacamole (browser-facing URL, without the "/#/?data=" suffix)
GUAC_URL = os.environ["GUAC_URL"]
GUAC_USER = os.getenv("GUAC_USER", "admin")

# Host that Guacamole connects to for the VM's VNC port
VNC_HOST = os.environ["VNC_HOST"]
