import json
import os
# SUPPORT MacOS, Unix based system and Windows

import time
import sys
import socket
import struct
if sys.platform == "win32":
    import win32file

CLIENT_ID = "ID_HERE"  # Your application's client ID
IPC_PATH = "/tmp/discord-ipc-0" if sys.platform != "win32" else r"\\.\pipe\discord-ipc-0"


# Change these values to match what you want to display
DETAILS = "Playing a Game"
STATE = "In the Menu"
LARGE_IMAGE_KEY = "game_logo"
LARGE_IMAGE_TEXT = "Game Logo"
SMALL_IMAGE_KEY = "status_icon"
SMALL_IMAGE_TEXT = "Online"
START_TIMESTAMP = int(time.time())
ACTIVITY_TYPE = 0  # 0 = Playing, 2 = Listening, 3 = Watching, 5 = Competing

def connect_to_ipc():
    try:
        if sys.platform == "win32":
            import win32pipe, win32file
            handle = win32file.CreateFile(IPC_PATH, win32file.GENERIC_READ | win32file.GENERIC_WRITE, 0, None, win32file.OPEN_EXISTING, 0, None)
            return handle
        else:
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            sock.connect(IPC_PATH)
            return sock
    except Exception as e:
        print(f"Failed to connect: {e}")
        return None

def send_payload(handle, opcode, payload):
    payload_json = json.dumps(payload).encode("utf-8")
    header = struct.pack("<II", opcode, len(payload_json))
    if sys.platform == "win32":
        win32file.WriteFile(handle, header + payload_json)
    else:
        handle.send(header + payload_json)

def read_response(handle):
    try:
        if sys.platform == "win32":
            header = win32file.ReadFile(handle, 8)
            opcode, length = struct.unpack("<II", header[1])
            payload = win32file.ReadFile(handle, length)
            return json.loads(payload[1].decode("utf-8"))
        else:
            header = handle.recv(8)
            opcode, length = struct.unpack("<II", header)
            payload = handle.recv(length)
            return json.loads(payload.decode("utf-8"))
    except Exception as e:
        print(f"Failed to read: {e}")
        return None

def set_rich_presence(handle):
    payload = {
        "cmd": "SET_ACTIVITY",
        "args": {
            "pid": os.getpid(),
            "activity": {
                "details": DETAILS,
                "state": STATE,
                "assets": {
                    "large_image": LARGE_IMAGE_KEY,
                    "large_text": LARGE_IMAGE_TEXT,
                    "small_image": SMALL_IMAGE_KEY,
                    "small_text": SMALL_IMAGE_TEXT,
                },
                "timestamps": {"start": START_TIMESTAMP},
                "type": ACTIVITY_TYPE, 
            },
        },
        "nonce": str(int(time.time())),
    }
    send_payload(handle, 1, payload)

def main():
    handle = connect_to_ipc()
    if not handle:
        return

    auth_payload = {"v": 1, "client_id": CLIENT_ID}
    send_payload(handle, 0, auth_payload)
    auth_response = read_response(handle)
    print("Auth response:", auth_response)

    set_rich_presence(handle)
    rp_response = read_response(handle)
    print("Rich Presence response:", rp_response)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        if sys.platform == "win32":
            handle.Close()
        else:
            handle.close()

if __name__ == "__main__":
    main()
