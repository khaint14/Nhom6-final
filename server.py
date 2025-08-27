import asyncio
import json
from lib2to3.pgen2.token import ASYNC
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

async def handle_client(sock, addr):
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
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            #xu ly dieu kien
            if cmd == "get_client_id":
                await send_json(writer, {"status": "success", "client_id": client_id})

            elif cmd == "view_trips":
                available = {
                    t: info['total_seats'] - len(info['booked_seats'])
                    for t, info in trips.items()
                }
                await send_json(writer, {"status": "success", "trips": available})

            elif cmd == "get_seats":
                trip_id = req.get("trip_id")
                only_mine = req.get("only_mine", False)
                if trip_id in trips:
                    if only_mine:
                        booked = {int(s): info for s, info in trips[trip_id]['booked_seats'].items()
                                  if info['owner_id'] == client_id}
                    else:
                        booked = {int(s): info for s, info in trips[trip_id]['booked_seats'].items()}
                    await send_json(writer, {"status": "success", "booked_seats": booked})
                else:
                    await send_json(writer, {"status": "error", "message": "Chuyến không tồn tại"})    
            

    except Exception as e:
        print(f"[!] Lỗi với client {addr}: {e}")
    finally:
        sock.close()
        print(f"[-] Client {addr} ngắt kết nối")