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
            if cmd == "get_client_id": #xu li dieu kien lan 1 
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

            elif cmd == "book_seat": #xu li dieu kien lan 2
                trip_id = req.get("trip_id")
                seat_num = req.get("seat_num")
                user_info = req.get("user_info", {})
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(f"[{timestamp}] Client {client_id} ({addr}) đặt ghế {seat_num} trên chuyến {trip_id}")

                if trip_id not in trips:
                    await send_json(writer, {"status": "error", "message": "Chuyến không tồn tại"})
                    print(f"[{timestamp}] Client {client_id} ({addr}) lỗi: Chuyến {trip_id} không tồn tại")
                elif not is_valid_name(user_info.get("name", "")):
                    await send_json(writer, {"status": "error", "message": "Tên không hợp lệ"})
                    print(f"[{timestamp}] Client {client_id} ({addr}) lỗi: Tên không hợp lệ")
                elif not is_valid_phone(user_info.get("phone", "")):
                    await send_json(writer, {"status": "error", "message": "SĐT không hợp lệ"})
                    print(f"[{timestamp}] Client {client_id} ({addr}) lỗi: SĐT không hợp lệ")
                elif seat_num < 1 or seat_num > trips[trip_id]['total_seats']:
                    await send_json(writer, {"status": "error", "message": "Số ghế không hợp lệ"})
                    print(f"[{timestamp}] Client {client_id} ({addr}) lỗi: Ghế {seat_num} không hợp lệ")
                elif str(seat_num) in trips[trip_id]['booked_seats']:
                    await send_json(writer, {"status": "error", "message": "Ghế đã được đặt"})
                    print(f"[{timestamp}] Client {client_id} ({addr}) lỗi: Ghế {seat_num} trên chuyến {trip_id} đã được đặt")
                else:
                    tid = generate_ticket_id()
                    trips[trip_id]['booked_seats'][str(seat_num)] = {
                        "user_info": user_info,
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "ticket_id": tid,
                        "owner_id": client_id
                    }
                    await send_json(writer, {"status": "success", "message": f"Đặt vé thành công! Mã vé: {tid}"})
                    print(f"[{timestamp}] Client {client_id} ({addr}) đặt ghế {seat_num} trên chuyến {trip_id} thành công, mã vé: {tid}")

            elif cmd == "get_booking_info": # xu li dieu kien lan 3 
                trip_id = req.get("trip_id")
                seat_num = req.get("seat_num")
                if trip_id in trips and str(seat_num) in trips[trip_id]['booked_seats']:
                    await send_json(writer, {"status": "success", "info": trips[trip_id]['booked_seats'][str(seat_num)]})
                else:
                    await send_json(writer, {"status": "error", "message": "Không tìm thấy thông tin vé"})

            elif cmd == "cancel_booking":
                trip_id = req.get("trip_id")
                seat_num = req.get("seat_num")
                ticket_id = req.get("ticket_id")
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(f"[{timestamp}] Client {client_id} ({addr}) hủy ghế {seat_num} trên chuyến {trip_id}, mã vé: {ticket_id}")
                if trip_id in trips and str(seat_num) in trips[trip_id]['booked_seats']:
                    booking = trips[trip_id]['booked_seats'][str(seat_num)]
                    if booking['ticket_id'] != ticket_id:
                        await send_json(writer, {"status": "error", "message": "Mã vé sai"})
                        print(f"[{timestamp}] Client {client_id} ({addr}) lỗi: Mã vé sai cho ghế {seat_num} trên chuyến {trip_id}")
                    elif booking['owner_id'] != client_id:
                        await send_json(writer, {"status": "error", "message": "Bạn không thể hủy vé của người khác"})
                        print(f"[{timestamp}] Client {client_id} ({addr}) lỗi: Không thể hủy vé của người khác cho ghế {seat_num} trên chuyến {trip_id}")
                    else:
                        del trips[trip_id]['booked_seats'][str(seat_num)]
                        await send_json(writer, {"status": "success", "message": "Hủy vé thành công"})
                        print(f"[{timestamp}] Client {client_id} ({addr}) hủy ghế {seat_num} trên chuyến {trip_id} thành công")
                else:
                    await send_json(writer, {"status": "error", "message": "Không tìm thấy vé"})
                    print(f"[{timestamp}] Client {client_id} ({addr}) lỗi: Không tìm thấy vé cho ghế {seat_num} trên chuyến {trip_id}")

            else:
                await send_json(writer, {"status": "error", "message": "Lệnh không hợp lệ"})
                print(f"[{timestamp}] Client {client_id} ({addr}) lỗi: Lệnh không hợp lệ - {cmd}")

    except Exception as e:
        print(f"[!] Lỗi với client {addr}: {e}")
    finally:
        sock.close()
        print(f"[-] Client {addr} ngắt kết nối")