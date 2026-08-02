import sys
from pathlib import Path
import subprocess

def printError(message: str):
    print(message, file=sys.stderr)

def makeDisk(source_path: str, session_id: str) -> Path:
    source = Path(source_path).resolve()

    if not source.is_file():
        raise FileNotFoundError(f"Source image not found: {source}")

    overlay_directory = Path("/var/lib/libvirt/images/overlays")
    destination = overlay_directory / f"{session_id}_{source.name}"

    subprocess.run(["qemu-img",
                    "create",
                    "-f", "qcow2",
                    "-b", str(source),
                    "-F", "qcow2",
                    str(destination)
                    ],
                    check=True)

    return destination

makeDisk(sys.argv[1], sys.argv[2])
