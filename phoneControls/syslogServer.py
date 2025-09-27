import socket
import re
import time
import json
import os

# Config
SYSLOG_PORT = 5514
RAW_LOG_FILE = os.path.join("syslog", "call_log.txt")
STATUS_LOG_FILE = os.path.join("syslog", "cid_status.json")

# Ensure log directory exists
os.makedirs("syslog", exist_ok=True)

# Clear raw log on startup
with open(RAW_LOG_FILE, "w") as f:
    f.write("")

# State: track all CIDs and their status
cid_status = {}
transfer_in_progress = False

# Load existing CID data if available
if os.path.exists(STATUS_LOG_FILE):
    try:
        with open(STATUS_LOG_FILE, "r") as f:
            cid_status = json.load(f)
    except Exception as e:
        print(f"[ERROR] Failed to load existing cid_status.json: {e}")
        cid_status = {}

def log_raw(message, timestamp):
    with open(RAW_LOG_FILE, "a") as f:
        f.write(json.dumps({ "raw": message, "time": timestamp }) + "\n")

def write_status_log():
    with open(STATUS_LOG_FILE, "w") as f:
        json.dump(cid_status, f, indent=2)

def classify_short_calls():
    for cid, call in cid_status.items():
        if call.get("status") not in ["Outgoing", "Missed", "DND"] and "duration" in call:
            dur = call["duration"]
            if 18 <= dur <= 22:
                call["status"] = "Missed"
                print(f"[CID CLASSIFIED] cid={cid} marked as Missed (duration={dur}s)")
            elif 3 <= dur <= 7:
                call["status"] = "DND"
                print(f"[CID CLASSIFIED] cid={cid} marked as DND (duration={dur}s)")

def extract_cid_allocation(message):
    patterns = [
        r"alloc new cid:(\d+)",
        r"SIP_MSG_ALLOC_CID, cid=(\d+)",
        r"request new callid\[(\d+)\]"
    ]
    for pattern in patterns:
        match = re.search(pattern, message)
        if match:
            return match.group(1)
    return None

def extract_cid_release(message):
    match = re.search(r"call released! cid (\d+)", message)
    return match.group(1) if match else None

def extract_number(message):
    num_match = re.search(r'(?:Number|FromNumber|num|remoteNum)\[\+?(\d+)\]', message)
    if num_match:
        raw = num_match.group(1)
        return raw  # preserve "0" for special handling
    return None

def extract_name(message):
    display_match = re.search(r'display_name\s*:\s*([^\r\n]+)', message)
    if display_match:
        return display_match.group(1).strip()

    hdrs_match = re.search(r'P-Asserted-Identity="([^"]+)"', message)
    if hdrs_match:
        return hdrs_match.group(1).strip()

    full_match = re.search(r'FullName=([^\s]+)', message)
    if full_match:
        return full_match.group(1).strip()

    from_match = re.search(r'From:\s*"([^"]+)"', message)
    if from_match:
        return from_match.group(1).strip()

    return None

def format_number(raw):
    digits = re.sub(r"\D", "", raw)
    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]
    if len(digits) == 10:
        return f"+1 ({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    return raw  # fallback if not 10 digits

def handle_syslog(message, epoch, timestamp):
    global transfer_in_progress

    log_raw(message, timestamp)

    # Detect transfer initiation
    if "Softkey press" in message and "Transfer" in message:
        transfer_in_progress = True
        print("[TRANSFER] Transfer initiated")

    # CID allocation
    cid_alloc = extract_cid_allocation(message)
    if cid_alloc:
        if transfer_in_progress:
            print(f"[TRANSFER] Skipping CID {cid_alloc} (transfer context)")
            transfer_in_progress = False
            return
        if cid_alloc not in cid_status:
            cid_status[cid_alloc] = {
                "cid": cid_alloc,
                "start_time": timestamp,
                "start_epoch": epoch,
                "status": "Ongoing"
            }
            print(f"[CID CREATED] cid={cid_alloc}")
        return  # Wait for enrichment before writing

    # CID release
    cid_release = extract_cid_release(message)
    if cid_release and cid_release in cid_status:
        call = cid_status[cid_release]
        if "end_time" not in call:
            call["end_time"] = timestamp
            call["duration"] = int(epoch - call["start_epoch"])
            call["status"] = "Completed"
            print(f"[CID COMPLETED] cid={cid_release}")
        write_status_log()
        return

    # Enrich with name/number
    name = extract_name(message)
    number = extract_number(message)

    for cid, call in cid_status.items():
        if call.get("status") == "Ongoing":
            if number:
                if number == "0" and "number" not in call and "name" not in call:
                    call["number"] = "Uninitialized"
                    call["name"] = "Call Initiated"
                    call["status"] = "Outgoing"
                    call["end_time"] = timestamp
                    call["duration"] = int(epoch - call["start_epoch"])
                    print(f"[CID FLAGGED] cid={cid} marked as Outgoing (number=0)")
                elif "number" not in call:
                    call["number"] = format_number(number)
                    print(f"[CID {cid}] Number detected: {call['number']}")
            if name and "name" not in call:
                call["name"] = name
                print(f"[CID {cid}] Name detected: {name}")

    write_status_log()
    classify_short_calls()

def start_syslog_server():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("", SYSLOG_PORT))
    print(f"[SYSLOG] Listening on UDP port {SYSLOG_PORT}...")

    while True:
        data, addr = sock.recvfrom(4096)
        message = data.decode(errors="ignore").strip()
        epoch = time.time()
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        handle_syslog(message, epoch, timestamp)

if __name__ == "__main__":
    start_syslog_server()
