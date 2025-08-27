import socket
import json
import tkinter as tk
from tkinter import messagebox, ttk
import re
import pyperclip

SERVER_HOST = 'localhost'
SERVER_PORT = 5555

def send_json(sock, obj):
    data = json.dumps(obj) + '\n'
    sock.sendall(data.encode('utf-8'))

def recv_json(sock, buffer):
    while '\n' not in buffer:
        chunk = sock.recv(4096).decode('utf-8')
        if not chunk:
            return None, buffer
        buffer += chunk
    line, rest = buffer.split('\n', 1)
    return json.loads(line), rest


class TicketBookingClient:
    def __init__(self, root):
        self.root = root
        self.root.title("H? th?ng �?t V� Xe (Client2)")
        self.root.geometry("900x650")
        self.root.configure(bg="#f6f8fa")
        self.buffer = ''
        self.client_id = None

        self.connect_to_server()
        self.get_client_id()
        self.selected_trip = None
        self.seat_rects = {}

        self.setup_ui()
        self.view_trips()

    # ket noi sever
    def connect_to_server(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((SERVER_HOST, SERVER_PORT))
        except Exception as e:
            messagebox.showerror("Lỗi kết nối", f"Không thể kết nối server: {e}")
            self.root.quit()

    def get_client_id(self):
        send_json(self.sock, {"command": "get_client_id"})
        resp, self.buffer = recv_json(self.sock, self.buffer)
        if resp and resp.get("status") == "success":
            self.client_id = resp["client_id"]

    def refresh_all(self):
        self.view_trips()
        if self.selected_trip:
            self.display_seats()


    def setup_ui(self):
        top = ttk.Frame(self.root, padding=12)
        top.pack(fill='x')
        ttk.Label(top, text="HỆ THỐNG ĐẶT VÉ XE", font=("Helvetica", 18, "bold")).pack(side='left')
        ttk.Button(top, text="Cập nhật", command=self.refresh_all).pack(side='right', padx=4)
        ttk.Button(top, text="Thoát", command=self.quit).pack(side='right', padx=4)

        main = ttk.Frame(self.root, padding=12)
        main.pack(fill='both', expand=True)

        # Left: trips
        left = ttk.Frame(main)
        left.pack(side='left', fill='y', padx=(0,12))

        ttk.Label(left, text="Danh sách chuyến", font=("Helvetica", 12, "bold")).pack(pady=(0,6))
        self.trip_tree = ttk.Treeview(left, columns=("trip","free"), show='headings', height=12)
        self.trip_tree.heading('trip', text='Chuyến')
        self.trip_tree.heading('free', text='Ghế trống')
        self.trip_tree.column('trip', width=260)
        self.trip_tree.column('free', width=80, anchor='center')
        self.trip_tree.pack(fill='y')
        self.trip_tree.bind('<<TreeviewSelect>>', self.on_trip_select)

        # Remove "Add trip" and "Delete trip" buttons → user only view/select
        ttk.Button(left, text="Xem vé", command=self.view_all_bookings).pack(pady=8)

        # Right: seat map
        right = ttk.Frame(main)
        right.pack(side='left', fill='both', expand=True)

        self.seat_label = ttk.Label(right, text="Sơ đồ ghế (chọn chuyến)", font=("Helvetica", 14, "bold"))
        self.seat_label.pack(pady=6)

        canvas_frame = ttk.Frame(right)
        canvas_frame.pack(fill='both', expand=True)
        self.canvas = tk.Canvas(canvas_frame, bg='white', height=420)
        self.canvas.pack(side='left', fill='both', expand=True, padx=(0,6))
        self.info_area = tk.Text(canvas_frame, width=36, state='disabled', wrap='word')
        self.info_area.pack(side='right', fill='y')

        status = ttk.Frame(right, padding=6)
        status.pack(fill='x', pady=6)
        ttk.Label(status, text="■ Ghế trống", foreground='green').pack(side='left', padx=6)
        ttk.Label(status, text="■ Ghế đã đặt", foreground='red').pack(side='left', padx=6)

    def send_request(self, request):
        try:
            send_json(self.sock, request)
            obj, self.buffer = recv_json(self.sock, self.buffer)
            return obj
        except Exception as e:
            messagebox.showerror("Lỗi", f"Lỗi khi giao tiếp server: {e}")
            return {'status':'error','message':str(e)}

    def view_trips(self):
        resp = self.send_request({'command':'view_trips'})
        if resp.get('status') == 'success':
            server_trips = resp.get('trips', {})
            for it in self.trip_tree.get_children():
                self.trip_tree.delete(it)
            for trip_id, free in server_trips.items():
                self.trip_tree.insert('', 'end', values=(trip_id, free))
        else:
            messagebox.showerror("Lỗi", resp.get('message','Không xác định'))


if __name__ == "__main__":
    root = tk.Tk()
    style = ttk.Style(root)
    style.theme_use('clam')
    app = TicketBookingClient(root)
    root.mainloop()
