import socket
import uuid
import json
import argparse
import tkinter as tk
from tkinter import ttk
from threading import Thread


class TableClient:
    def __init__(self, host, port, num_rows):
        self.host = host
        self.port = port

        self.id = str(uuid.uuid4())

        self.start_index = 0
        self.num_rows = num_rows
        self.table_len = num_rows

        self.first_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.first_socket.connect((self.host, self.port))
        except Exception as e:
            print(f"Error connecting to server: {e}")

        self.first_socket.sendall(json.dumps({self.id: ("FIRST", self.num_rows)}).encode())

        self.second_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.second_socket.connect((self.host, self.port))
        except Exception as e:
            print(f"Error connecting to server: {e}")

        self.second_socket.sendall(json.dumps({self.id: ("SECOND", self.num_rows)}).encode())

        self.root = tk.Tk()
        self.root.resizable(False, False)
        self.root.title("Table Viewer")

        self.table_frame = ttk.Frame(self.root)
        self.table_frame.pack(pady=10, padx=10)

        self.send_request("GET_COLUMNS")
        columns = self.receive_response()

        self.sorted_column = columns[0]
        self.sort_ascending = "No"

        self.tree = ttk.Treeview(self.table_frame, height=self.num_rows)
        self.tree["columns"] = tuple(columns)
        self.tree.heading("#0", text="", anchor=tk.W)
        self.tree.column("#0", width=0, stretch=tk.NO)
        for elem in columns:
            self.tree.heading(elem, text=elem, anchor=tk.W, command=lambda element=elem: self.sort_by_column(element))
            self.tree.column(elem, anchor=tk.W, width=150)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.fake_tree = ttk.Treeview(self.table_frame)
        self.fake_tree.heading("#0", text="", anchor=tk.W)
        self.fake_tree.column("#0", width=0, stretch=tk.NO)
        self.fake_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.scrollbar = ttk.Scrollbar(self.table_frame, orient=tk.VERTICAL, command=self.on_scroll)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.fake_tree.config(yscrollcommand=self.scrollbar.set)

        self.update_table()

        self.update_thread = Thread(target=self.receive_updates)
        self.update_thread.daemon = True
        self.update_thread.start()

        self.root.mainloop()

    def receive_updates(self):
        while True:
            response = self.second_socket.recv(4096)

            if not response:
                break

            try:
                updates = json.loads(response.decode())
            except Exception as e:
                continue

            if updates:
                self.table_len = updates[1]
                self.update_table(updates[0])

    def send_request(self, command, *args):
        try:
            request = json.dumps((command, *args))
            self.first_socket.sendall(request.encode())
        except Exception as e:
            print(f"Error sending request: {e}")

    def receive_response(self):
        try:
            response = self.first_socket.recv(4096)
            return json.loads(response.decode())
        except Exception as e:
            print(f"Error receiving response: {e}")
            return None

    def get_rows(self, start_index, num_rows):
        self.send_request("GET_ROWS", start_index, num_rows)
        response = self.receive_response()
        if response:
            return response

    def sort_by_column(self, column_name):
        if column_name == self.sorted_column:
            if self.sort_ascending == "No":
                self.sort_ascending = "Asc"
            elif self.sort_ascending == "Asc":
                self.sort_ascending = "Desc"
            elif self.sort_ascending == "Desc":
                self.sort_ascending = "No"
        else:
            self.sorted_column = column_name
            self.sort_ascending = "Asc"

        self.send_request("SORT_BY_COLUMN", self.sorted_column, self.sort_ascending)
        response = self.receive_response()
        if response:
            self.update_table(response)
        else:
            print("Error: Failed to sort table.")

    def on_scroll(self, *args):
        pos = int(self.fake_tree.yview()[0] * self.table_len)
        if not (pos == 0 and self.start_index == 0) and \
                not (pos == self.table_len - self.num_rows and self.start_index == self.table_len - self.num_rows):
            self.start_index = pos
            self.update_table()
        return self.fake_tree.yview(*args)

    def update_table(self, rows=None):
        if rows is None:
            args = self.get_rows(self.start_index, self.num_rows)
            rows, table_len = args

        try:
            if self.tree.get_children():
                self.tree.delete(*self.tree.get_children())

            pos, _ = self.fake_tree.yview()

            if self.fake_tree.get_children():
                self.fake_tree.delete(*self.fake_tree.get_children())

            if rows is None:
                self.table_len = table_len
        except Exception as e:
            return

        for row in rows:
            self.tree.insert("", tk.END, values=[elem for elem in row.values()])

        for i in range(self.table_len):
            self.fake_tree.insert("", tk.END, values=('',))

        self.fake_tree.yview_moveto(pos)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="localhost", help="Host IP address")
    parser.add_argument("--port", type=int, default=5000, help="Port number")
    parser.add_argument("--num_rows", type=int, default=10, help="Number of rows in table")
    arguments = parser.parse_args()

    client = TableClient(arguments.host, arguments.port, arguments.num_rows)
