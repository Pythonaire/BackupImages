import paramiko
import subprocess
import socket
import time
from datetime import datetime
import psutil
import os
import re
import logging
import concurrent.futures
import multiprocessing
from .library import JSONFile

# Server settings
SERVER_IP = "192.168.1.30"
BACKUP_DIR = "/mnt/HDD"
START_PORT = 19000  # Starting port
MAX_PORT = 19010   # Stop after this port (optional, or you can keep going indefinitely)
MAX_RETRIES = 3  # Maximum retries for failures
SYSJSON = JSONFile("UNIX_System.json")

logging.basicConfig(level=logging.INFO, format="[%(module)s] %(message)s")

# Shared port tracker (starting value at START_PORT)
port_tracker = multiprocessing.Value("i", START_PORT)
port_lock = multiprocessing.Lock()  # Ensures only one process updates the port at a time

def read_system():
    return SYSJSON.readJson()

def detect_disks(ssh):
    """Detect available disks on the client."""
    try:
        stdin, stdout, stderr = ssh.exec_command('''
            DISK=$(/bin/findmnt -n -o SOURCE /boot 2>/dev/null || /bin/findmnt -n -o SOURCE /boot/firmware 2>/dev/null);
            if echo "$DISK" | grep -q '^/dev/nvme'; then
                echo "$DISK" | sed -E 's/p[0-9]+$//';
            elif echo "$DISK" | grep -q '^/dev/mmcblk'; then
                echo "$DISK" | sed -E 's/p[0-9]+$//';
            elif echo "$DISK" | grep -q '^/dev/sd'; then
                echo "$DISK" | sed -E 's/[0-9]+$//';
            else
                echo "$DISK";
            fi
            ''')
        disks = stdout.read().decode().strip().split("\n")
        return disks[0] if disks else None
    except Exception as e:
        logging.error(f"[ERROR] Failed to detect disks: {e}")
        return None

def add_system(ip, user):
    prepared = False
    try:
        if ping_host(ip):
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(ip, username=user, key_filename='/home/pwiechmann/.ssh/id_rsa')
            hostname = get_hostname(ssh)
            prepared = True
    except Exception as e:
        logging.error(f"[Error] Cant act as {user} with {ip}: {e}, key exchanged ?") 
        prepared = False
    if prepared:
        data = SYSJSON.readJson()
        disk = detect_disks(ssh)
        new_entry = {'ip': ip, 'hostname': hostname, 'user': user, 'disk': disk}
        if data:
            if new_entry not in data:
                data.append(new_entry)
        else:
            data = [{'ip': ip, 'hostname':hostname, 'user': user, 'disk': disk }]
        SYSJSON.writeJson(data)

def remove_system(ip):
    lst = SYSJSON.readJson()
    lst = [item for item in lst if item["ip"] != ip]
    SYSJSON.writeJson(lst)


def ping_host(ip):
    """Ping the host and check if it's online."""
    try:
        # -W 1 means ping timeout 1 second
        subprocess.run(["ping", "-c", "1", "-W", "1", ip], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return True
    except subprocess.CalledProcessError:
        return False

def is_client_online(ip, timeout=2):
    """Check if the client is online by pinging it."""
    is_online = False
    for attempt in range(2):
        try:
            socket.setdefaulttimeout(timeout)
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((ip, 22))
            is_online = True
            break
        except (socket.timeout, ConnectionRefusedError):
            logging.warning(f"[WARNING] {ip} is offline (Attempt {attempt+1}/{2})...")
            time.sleep(5)
            is_online = False
    return is_online
    
def get_hostname(ssh):
    try:
        stdin, stdout, stderr = ssh.exec_command("hostname")
        hostname = stdout.read().decode().strip()
        return hostname
    except Exception as e:
        logging.error(f"[ERROR] Failed to detect hostname: {e}")
        return None
    
def get_backup_files():
    if not os.path.exists(BACKUP_DIR):  # Check if directory exists
        return []
    backup_files = os.listdir(BACKUP_DIR)
    pattern = re.compile(r"(?P<hostname>.+)-(?P<time>\d{2}_\d{2}_\d{4})\.img\.gz$")
    backups = []
    for file in backup_files:
        if not file.endswith(".img.gz"):  # Ignore non-backup files early
            continue
        match = pattern.match(file)
        if match:
            backups.append({
                "hostname": match.group("hostname"),
                "time": match.group("time"),
                "filename": file
            })
    return backups  # Returns an empty list if no valid backup files exist

def is_netcat_server_running(port):
    """Check if a netcat server is running and listening on the given port."""
    for conn in psutil.net_connections(kind="inet"):
        if conn.raddr and len(conn.raddr) > 1:  # Ensure raddr is not empty
            if conn.raddr[1] == port and conn.status == psutil.CONN_LISTEN:
                return True
    return False

def is_netcat_client_connected(port):
    """Check if a netcat client is connected to the specified port."""
    for conn in psutil.net_connections(kind="inet"):
        if conn.status == psutil.CONN_ESTABLISHED and conn.raddr:
            if conn.laddr.port == port:  # Check the local listening port
                return True
    return False

def start_netcat_session(port, client_ssh, client_ip, client_hostname, client_disk):
    """Start a netcat server and client session on the given port."""
    try:
        # Start server-side netcat
        now = datetime.now().strftime("%d_%m_%Y")
        """Start netcat listener on the backup server to receive the image."""
        backup_file = f"{BACKUP_DIR}/{str(client_hostname)}-{str(now)}.img.gz"
        cmd = f"sudo nc -l -p {port} | dd bs=512 of={backup_file} && echo DONE > {backup_file}.done"
        logging.info(f"[SERVER] Listening for backup from {client_hostname}...")
        process = subprocess.Popen(cmd, shell=True)
        # Start client-side netcat (for example, connecting to a remote address)
        """Start the backup process on the client over SSH."""
        backup_cmd = f"bash -c 'sudo dd if={client_disk} bs=512 | gzip --fast | nc -q 10 {BACKUP_SERVER_IP} {port}'"
        logging.info(f"[CLIENT {client_ip}] Starting backup: {backup_cmd}")
        stdin, stdout, stderr = client_ssh.exec_command(backup_cmd)
        if wait_for_completion(client_hostname):
            logging.info(f"[SUCCESS] Backup for {client_hostname} completed.")
            try:
                # Wait for the netcat session to complete
                process.wait(timeout=2)  # Adjust timeout as necessary
                # Check the process status
                if process.returncode == 0:
                    logging.info(f"[SUCCESS] Session for {client_hostname} cleared.")
                    finished = True
                else:
                    logging.warning(f"[Warning] Session for {client_hostname} not closed, need to force it.")
                    finished = False
            except subprocess.TimeoutExpired:
                logging.error(f"[ERROR] Netcat session timed out.")
                finished = False
            finally:
                if process.returncode != 0:
                    process.terminate()  # Terminate the process to ensure port is freed
                    logging.warning(f"[Warning] The process on Port {port} need to be terminated to free the resources.")
                finished = True
    except Exception as e:
        logging.error(f"[Error] Backup for {client_hostname} failed")
        finished = False
    return finished

def wait_for_completion(hostname):
    """Wait until the .done file is created, meaning netcat has finished."""
    now = datetime.now().strftime("%d_%m_%Y")
    done_file = f"{BACKUP_DIR}/{str(hostname)}-{str(now)}.img.gz.done"
    # Ensure old done file is removed before starting
    if os.path.isfile(done_file):
        os.remove(done_file)
    while True:
        if os.path.isfile(done_file):
            os.remove(done_file)  # Cleanup
            return True
        time.sleep(5)  # Check every 5 seconds

def start_parallel_backup(client_lst):
    with concurrent.futures.ProcessPoolExecutor(max_workers=len(client_lst)) as executor:
        results = executor.map(run_backup, client_lst)
    # Convert results to a list to trigger execution and catch errors early
    return list(results)


def get_next_available_port():
    """Atomically get the next available netcat port."""
    with port_lock:  # Ensure only one process modifies the port at a time
        port = port_tracker.value
        port_tracker.value += 1  # Increment for next process
    return port


def run_backup(client):
    logging.info(f"[*] Starting parallel backup...")
    client_ip, client_user, client_disk, client_hostname  = client["ip"], client["user"], client["disk"], client["hostname"]
    logging.info(f"[INFO] Checking if {client_ip} is online...")
    if not ping_host(client_ip):
        logging.error(f"[ERROR] {client_ip} is offline. Skipping.")
        return
    try:
        client_ssh = paramiko.SSHClient()
        client_ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        logging.info(f"[INFO] Connecting to {client_ip} via SSH...")
        client_ssh.connect(client_ip, username=client_user,key_filename='/home/pwiechmann/.ssh/id_rsa')
        while True:
            port = get_next_available_port()  # Get next available port atomically
            logging.info(f"[INFO] Attempting netcat session on port {port}...")
            if is_netcat_server_running(port) or is_netcat_client_connected(port):
                logging.warning(f"[WARNING] Port {port} is in use. Trying next port...")
                time.sleep(1)  # Avoid spamming CPU
                continue  # Try next port
            logging.info(f"[INFO] Starting netcat session on port {port}...")
            results = start_netcat_session(port, client_ssh, client_ip, client_hostname, client_disk)
            time.sleep(2)  # Allow netcat to end
            if results == True:
                break  # Exit loop once a working session is created
            else:
                logging.warning(f"[WARNING] Netcat session failed on port {port}. Trying next port...")
                time.sleep(1)
    finally:
        try:
            client_ssh.close()
        except NameError:
            pass  # If client_ssh was never created, ignore closing