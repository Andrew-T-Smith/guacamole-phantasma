import sys
from pathlib import Path
import subprocess
import uuid
import libvirt
import xml.etree.ElementTree as ET

#Prints passed string to stderr
def printError(message: str):
    print(message, file=sys.stderr)


#Makes a disk overlay based on the passed in source path and session ID
def make_disk(source_path: str, session_id: str) -> Path:
    source = Path(source_path).resolve()

    if not source.is_file():
        raise FileNotFoundError(f"Source image not found: {source}")

    overlay_directory = Path("/var/lib/libvirt/images/overlays")
    destination = overlay_directory / f"{session_id}_{source.name}"

    #Ensure the directory exists
    overlay_directory.mkdir(parents=True, exist_ok=True)

    subprocess.run(["qemu-img",
                    "create",
                    "-f", "qcow2",
                    "-b", str(source),
                    "-F", "qcow2",
                    str(destination)
                    ],
                    check=True)

    return destination


#Makes an XML based on some parameters and a given template XML
def make_domain_xml_from_template(xml_template_path: str, vm_name: str, hdd_overlay_path: str | Path) -> str:
    xml_path = Path(xml_template_path).resolve()

    if not xml_path.is_file():
        raise FileNotFoundError(f"Source xml not found: {xml_template_path}")

    content = xml_path.read_text()

    final_payload = content.format(
        vm_name=vm_name,
        vm_uuid=str(uuid.uuid4()),
        vm_overlay_path=str(hdd_overlay_path)
        )

    return final_payload

#Gets the port number from a VM XML
def get_port_from_vm(vm_domain) -> int:
    xml_desc = vm_domain.XMLDesc(0)
    root = ET.fromstring(xml_desc)
    graphics = root.find("./devices/graphics[@type='vnc']")

    if graphics is not None:
        port = graphics.get("port")
        if port and port != "-1":
            return int(port)

    raise RuntimeError("VNC graphics port could not be found in active domain")

#Starts a VM from a passed in XML
def start_VM(xml_contents: str, vm_name: str):
    try:
        conn = libvirt.open("qemu:///system")
    except libvirt.libvirtError as e:
        printError(f"Failed to connect to the hypervisor: {e}")
        raise

    try:
        print(f"Starting domain '{vm_name}'")
        dom = conn.createXML(xml_contents, 0)

        if dom is None:
            printError("Failed to make domain")
            raise RuntimeError(f"Failed to create the domain '{vm_name}'")
        else:
            print(f"Domain '{vm_name}' created")
            return get_port_from_vm(dom)
    finally:
        conn.close()


#Creates VM files and starts the VM
def spawn_session(session_id : str, backing_path: str | Path, template_xml_path: str | Path, base_machine_name: str) -> dict:
    #Create the overlay disk
    overlay_path = make_disk(backing_path, session_id)

    #Generate the VM XML from the template
    session_vm_name = "tmp__" + base_machine_name + "__" + session_id
    session_xml = make_domain_xml_from_template(template_xml_path, session_vm_name, overlay_path)

    #Start the virtual machine
    spawned_vm_vnc_port_number = start_VM(session_xml, session_vm_name)
    print("started on port")
    print(spawned_vm_vnc_port_number)

    #Return information that is useful to the server
    return {
        "session_id": session_id,
        "vm_name": session_vm_name,
        "vnc_port": spawned_vm_vnc_port_number,
        "overlay_path": overlay_path
    }


#Stops the VM and deletes the overlay file
def destroy_session(session_vm_name: str, session_overlay_path: Path | str) -> bool:
    try:
        conn = libvirt.open("qemu:///system")
    except libvirt.libvirtError as e:
        printError(f"Failed to connect to the hypervisor: {e}")
        raise

    try:
        print(f"Stopping the domain '{session_vm_name}'")
        dom = conn.lookupByName(session_vm_name)
        dom.destroy()
        print(f"Domain destroyed")
    except libvirt.libvirtError:
        printError(f"Domain '{session_vm_name}' failed to destroy")
    finally:
        conn.close()

    overlay = Path(session_overlay_path)
    try:
        if overlay.exists():
            overlay.unlink()
    except Exception as e:
        printError(f"An unknown error occured deleting the overlay file '{overlay}': {e}")
        return False

    return True


#Stops all sessions. Sessions are determined by having the VM name prefix.
def destroy_all_sessions(overlay_folder_path: Path | str):
    #Establish a connection to the hypervisor
    try:
        conn = libvirt.open("qemu:///system")
    except libvirt.libvirtError as e:
        printError(f"Failed to connect to the hypervisor: {e}")
        raise

    try:
        #Get a list of all running VMs and destroy those with the VM prefix
        domains = conn.listAllDomains()
        for domain in domains:
            if domain.name().startswith("tmp__"):
                print(f"Destroying domain {domain.name()}")
                domain.destroy()

        #Empty the overlay directory
        overlays = Path(overlay_folder_path)
        if overlays.exists():
            for file in overlays.iterdir():
                if file.is_file() and file.name.endswith(".qcow2"):
                    file.unlink()
    except libvirt.libvirtError as e:
        printError(f"Failed to communicate with the hypervisor or run operation on it: {e}")
    except FileNotFoundError as e:
        printError(f"File not found: {e}")
    finally:
        conn.close()
