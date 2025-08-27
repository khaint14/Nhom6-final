import asyncio
import json
import re
from datetime import datetime
import uuid

# =====================
# Dữ liệu chuyến chung
# =====================
trips = {
    'BINH DINH -> HCM': {'total_seats': 20, 'booked_seats': {}},
    'HCM -> BINH DINH': {'total_seats': 20, 'booked_seats': {}},
    'DAK LAK -> HCM': {'total_seats': 20, 'booked_seats': {}},
    'HCM -> DAK LAK': {'total_seats': 20, 'booked_seats': {}},
}

# =====================
# Helper gửi/nhận JSON
# =====================
async def send_json(writer, obj):
    data = json.dumps(obj) + "\n"
    writer.write(data.encode("utf-8"))
    await writer.drain()
    
async def recv_json(reader, buffer):
    while "\n" not in buffer:
        chunk = await reader.read(4096)
        if not chunk:
            return None, buffer
        buffer += chunk.decode("utf-8")
    line, rest = buffer.split("\n", 1)
    return json.loads(line), rest

# =====================
# Validate
# =====================
def is_valid_phone(phone):
    return bool(re.match(r'^\d{10}$', phone))

def is_valid_name(name):
    return bool(re.match(r'^[A-Za-z\s]{2,}$', name))

def generate_ticket_id():
    return str(uuid.uuid4())[:8]

def handle_client(sock, addr):
    buffer = ""
    client_id = str(uuid.uuid4())  # ID duy nhất cho client
    print(f"[+] Client {addr} kết nối với ID {client_id}")

    try:
        while True:
            req, buffer = recv_json(sock, buffer)
            if req is None:
                if buffer == "":
                    break
                else:
                    continue

            cmd = req.get("command")
        #xu ly dieu kien
            

    except Exception as e:
        print(f"[!] Lỗi với client {addr}: {e}")
    finally:
        sock.close()
        print(f"[-] Client {addr} ngắt kết nối")