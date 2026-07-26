import sys
from pathlib import Path
import subprocess

def printError(message):
    print(message, file=sys.stderr)

def makeDisk(source, ID):
    file_path = Path(source)

    if file_path.is_file() == False:
        printError("Input file does not exist")
        exit(1)

    print("The file exists")
    print(file_path.resolve())

    subprocess.run(["qemu-img",
                    "create",
                    "-f", "qcow2",
                    "-b", file_path.resolve(),
                    "-F", "qcow2",
                    "/var/lib/libvirt/images/overlays/" + ID + "_" + file_path.name
                   ])


makeDisk(sys.argv[1], sys.argv[2])
