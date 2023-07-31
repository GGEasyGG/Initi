import time
import random
import json
import socket
import argparse
from faker import Faker


def monitor_table_changes(server):
    fake = Faker()
    begin = time.time()
    end = time.time()

    while True:
        request = json.dumps(("GET_INFO",))
        try:
            server.sendall(request.encode())
        except Exception as e:
            print(f"Error sending request to server: {e}")

        response = server.recv(4096)
        num_rows, maximum = json.loads(response.decode())

        data = []

        indexes = []

        if end - begin >= 30:
            data = [random.choice(['Id', 'Name', 'Address', 'Date of birth', 'Telephone number', 'Sex', 'Salary']),
                    random.choice([True, False])]

            request = json.dumps(("UPDATE_SORTING", data))
            try:
                server.sendall(request.encode())
            except Exception as e:
                print(f"Error sending update to server: {e}")

            begin = time.time()
        else:
            for i in range(50):
                flag = random.randint(1, 3)

                if flag == 1:
                    row = {
                            'Id': maximum + 1 + i,
                            'Name': fake.name(),
                            'Address': fake.address().replace('\n', ', '),
                            'Date of birth': fake.date_of_birth().strftime('%d/%m/%Y'),
                            'Telephone number': fake.phone_number(),
                            'Sex': fake.random_element(['Male', 'Female']),
                            'Salary': fake.random_int(1000, 9999),
                            }
                    data.append((row, 'ADD'))
                elif flag == 2:
                    num = random.randint(0, num_rows - 1)
                    while num in indexes:
                        num = random.randint(0, num_rows - 1)
                    indexes.append(num)
                    data.append((num, 'DELETE'))
                elif flag == 3:
                    num = random.randint(0, num_rows - 1)
                    while num in indexes:
                        num = random.randint(0, num_rows - 1)
                    indexes.append(num)
                    row = {
                        'Id': num,
                        'Name': fake.name(),
                        'Address': fake.address().replace('\n', ', '),
                        'Date of birth': fake.date_of_birth().strftime('%d/%m/%Y'),
                        'Telephone number': fake.phone_number(),
                        'Sex': fake.random_element(['Male', 'Female']),
                        'Salary': fake.random_int(1000, 9999),
                    }
                    data.append((row, 'UPDATE'))

            request = json.dumps(("UPDATE_ROWS", data))
            try:
                server.sendall(request.encode())
            except Exception as e:
                print(f"Error sending update to server: {e}")

            time.sleep(1)

        end = time.time()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="localhost", help="Host IP address")
    parser.add_argument("--port", type=int, default=5000, help="Port number")
    arguments = parser.parse_args()

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        server_socket.connect((arguments.host, arguments.port))
    except Exception as e:
        print(f"Error connecting to server: {e}")

    try:
        server_socket.sendall(json.dumps({"UPDATER": ("FIRST", 0)}).encode())
    except Exception as e:
        print(f"Error sending information to server: {e}")

    print("Updating service connected to the server.")

    monitor_table_changes(server_socket)
