import json
import asyncio
import argparse
from faker import Faker


class TableServer:
    def __init__(self):
        self.table = []
        self.sorting_key = lambda row: row['Id']
        self.sort_order = False
        self.lock = asyncio.Lock()
        self.client_windows = {}
        self.clients = {}

    def add_client(self, key, num_rows):
        self.client_windows[key] = [0, num_rows, [elem['Id'] for elem in self.table], (self.sorting_key, "No")]

    def remove_client(self, key):
        del self.client_windows[key]

    async def update_table(self, updated_rows=None):
        async with self.lock:
            flag = False

            if updated_rows is not None:
                flag = True

                deleted = []
                for elem in updated_rows:
                    row, command = elem[0], elem[1]
                    if command == "ADD":
                        self.table.append(row)
                    elif command == "UPDATE":
                        idx = self.table[row["Id"]]["Id"]
                        self.table[row["Id"]] = row
                        self.table[row["Id"]]["Id"] = idx
                    elif command == "DELETE":
                        deleted.append(self.table[row])

                for elem in deleted:
                    self.table.remove(elem)

            self.table.sort(key=self.sorting_key, reverse=self.sort_order)

        await self.update_client_windows(flag)

    def get_rows(self, key, start_index, num_rows):
        if self.client_windows[key][3][1] != "No":
            indexes = self.get_sorted_indexes(*self.client_windows[key][3])
            rows = [self.table[i] for i in indexes[start_index:start_index + num_rows]]
        else:
            rows = self.table[start_index:start_index + num_rows]
        return rows

    def get_sorted_indexes(self, sort_key, ascending):
        flag = ascending != "Asc"
        return [index for index, _ in
                sorted(enumerate(self.table), key=lambda x: x[1][sort_key], reverse=flag)]

    def sort_client_window(self, key, column_name, ascending):
        self.client_windows[key][3] = (column_name, ascending)
        start_index, num_rows, *args = self.client_windows[key]
        return self.get_rows(key, start_index, num_rows)

    async def update_client_windows(self, flag):
        if flag:
            for key, value in self.client_windows.items():
                if value[0] + value[1] > len(self.table):
                    rows = self.get_rows(key, len(self.table) - value[1], value[1])
                    self.client_windows[key] = [len(self.table) - value[1], value[1], [elem['Id'] for elem in rows],
                                                value[3]]
                    await send_response(self.clients[key]["SECOND"][0], (rows, len(self.table)))
                if [elem['Id'] for elem in self.table[value[0]:value[0] + value[1]]] != value[2]:
                    rows = self.get_rows(key, value[0], value[1])
                    self.client_windows[key] = [value[0], value[1], [elem['Id'] for elem in rows], value[3]]
                    await send_response(self.clients[key]["SECOND"][0], (rows, len(self.table)))
        else:
            for key, value in self.client_windows.items():
                if value[3][1] == "No":
                    rows = self.get_rows(key, value[0], value[1])
                    self.client_windows[key] = [value[0], value[1], [elem['Id'] for elem in rows], value[3]]
                    await send_response(self.clients[key]["SECOND"][0], (rows, len(self.table)))


async def handle_client_connection(reader, writer, server):
    addr = writer.get_extra_info("peername")
    print(f"Connection established with {addr}")

    request = await reader.read(4096)
    info = json.loads(request.decode())
    key, value, num_rows = list(info.keys())[0], list(info.values())[0][0], list(info.values())[0][1]

    if value != "SECOND" and key != "UPDATER":
        server.add_client(key, num_rows)
    if key not in server.clients.keys():
        server.clients[key] = {value: (writer, reader)}
    else:
        server.clients[key][value] = (writer, reader)

    if value != "SECOND":
        try:
            while True:
                request = await server.clients[key]["FIRST"][1].read(16284)
                if not request:
                    break

                command, *args = json.loads(request.decode())
                if command == "GET_ROWS":
                    start_index, num_rows = args
                    rows = server.get_rows(key, start_index, num_rows)
                    server.client_windows[key] = [start_index, num_rows, [elem['Id'] for elem in rows],
                                                  server.client_windows[key][3]]
                    await send_response(server.clients[key]["FIRST"][0], (rows, len(server.table)))
                elif command == "SORT_BY_COLUMN":
                    column_name, ascending = args
                    sorted_rows = server.sort_client_window(key, column_name, ascending)
                    await send_response(server.clients[key]["FIRST"][0], sorted_rows)
                elif command == "GET_COLUMNS":
                    await send_response(server.clients[key]["FIRST"][0], list(server.table[0].keys()))
                elif command == "GET_INFO":
                    await send_response(server.clients[key]["FIRST"][0], (len(server.table),
                                                                          max(elem['Id'] for elem in server.table)))
                elif command == "UPDATE_ROWS":
                    await server.update_table(args[0])
                elif command == "UPDATE_SORTING":
                    server.sorting_key = lambda row, column=args[0][0]: row[column]
                    server.sort_order = args[0][1]
                    await server.update_table()
        except Exception as e:
            print(f"Error handling client request: {e}")
        finally:
            print(f"Connection refused with {addr}")
            server.remove_client(key)
            del server.clients[key]
            writer.close()


async def send_response(writer, data):
    response = json.dumps(data)
    writer.write(response.encode())
    await writer.drain()


async def main(host, port):
    server_obj = TableServer()

    fake = Faker()

    for i in range(1, 1001):
        row = {
            'Id': i,
            'Name': fake.name(),
            'Address': fake.address().replace('\n', ', '),
            'Date of birth': fake.date_of_birth().strftime('%d/%m/%Y'),
            'Telephone number': fake.phone_number(),
            'Sex': fake.random_element(['Male', 'Female']),
            'Salary': fake.random_int(1000, 9999),
        }
        server_obj.table.append(row)

    server = await asyncio.start_server(lambda reader, writer: handle_client_connection(reader, writer, server_obj),
                                        host, port)

    print(f"Server is listening on {host}:{port}...")
    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="localhost", help="Host IP address")
    parser.add_argument("--port", type=int, default=5000, help="Port number")
    arguments = parser.parse_args()

    asyncio.run(main(arguments.host, arguments.port))
