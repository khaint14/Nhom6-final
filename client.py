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
        self.root.title("H? th?ng Ð?t Vé Xe (Client2)")
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


if __name__ == "__main__":
    root = tk.Tk()
    style = ttk.Style(root)
    style.theme_use('clam')
    app = TicketBookingClient(root)
    root.mainloop()
