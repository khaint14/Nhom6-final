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