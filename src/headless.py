import msvcrt
import socket
import sys
import threading
import time
import typing
from datetime import datetime

from google.cloud import firestore

import firebase.messagesStore as message_store
import firebase.serverStore as server_store
import firebase.userStore as user_store
import help.functions as help_functions
from help.colors import CONSOLE_COLORS, CONSOLE_USER_COLORS
from help.messageBuffer import MessageBuffer
from models.serverModel import ServerModel
from models.userModel import UserModel

user_input = ""
server_input = ""


class HeadlessApp:

    @staticmethod
    def run(side: str):
        server_store.fetch_servers()

        if side == "join":
            HeadlessApp.join_server()

        elif side == "host":
            if not server_store.is_server_in_database():
                server_data = HeadlessApp.create_server()

                if not server_data:
                    return

            HeadlessApp.host_server(server_data)

            server_store.close_server(server_data["reference"])
            print("Server shut down")

    @staticmethod
    def join_server():
        online_servers = [
            server for server in server_store.servers if server["isActive"]
        ]

        if len(online_servers) == 0:
            print("There are no online servers")
            return

        server_names = [server["name"] for server in server_store.servers]
        print("Currently online servers:\n")
        for index, server_name in enumerate(server_names):
            print(f"{index + 1}: {server_name}")

        user_input = input("\nEnter server's name:\n")
        while not user_input in server_names:
            user_input = input("Incorrect server name. Try again:\n")
        print()

        server = server_store.find_server(server_name=user_input)

        if server["isPassword"]:
            try:
                help_functions.check_password(server["password"])
            except KeyboardInterrupt:
                return

            print("Correct password!\n")

        user_data = user_store.user_data
        if not server_store.is_user_on_server(server, user_data["reference"]):
            server_store.add_user_to_server(server, user_data["reference"])

        HeadlessApp.__connect_to_server(server)

    @staticmethod
    def create_server() -> typing.Optional[ServerModel]:
        try:
            server_name = server_store.create_server_name()

            is_password_protected = input(
                "Do you want your server password protected? [yes \ no]\n",
            )
            is_password_protected = (
                True if is_password_protected.lower() == "yes" else False
            )

            password = ""
            if is_password_protected:
                password = input(f"Enter server's password:\n")

        except KeyboardInterrupt:
            return

        user_data = user_store.user_data

        server_data = {
            "name": server_name,
            "ip": user_data["ip"],
            "isPassword": is_password_protected,
            "password": password,
            "isActive": True,
            "users": [],
        }

        server_reference = server_store.create_server(server_data)
        server_model = ServerModel(server_data, server_reference)

        print("Server created!")

        return server_model

    @staticmethod
    def host_server(server_data: ServerModel):
        print("Creating server socket")

        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((server_data["ip"], 2137))
        server_socket.listen(5)

        connected_clients = []
        buffer = MessageBuffer()

        print("Server socket is created")

        server_store.open_server(server_data["reference"])

        print("Waiting for users", end="\n\n")

        messages = message_store.fetch_messages_from_server(server_data["reference"])
        message_store.print_messages(messages)

        t_server_input = threading.Thread(
            target=HeadlessApp.__server_input,
            args=(connected_clients, server_socket, buffer, server_data["reference"]),
        )
        t_server_input.start()

        while True:
            try:
                client_socket, client_address = server_socket.accept()
                client_ip = client_address[0]

                connected_clients.append({client_ip: client_socket})
                print(
                    f"\r{CONSOLE_COLORS['RESET']}Accepted connection from client: {client_ip}\n{CONSOLE_COLORS['SERVER']}[Server]: ",
                    end="",
                )

                t_handle_client = threading.Thread(
                    target=HeadlessApp.__handle_clients,
                    args=(
                        connected_clients,
                        [client_ip, client_socket],
                        server_data["reference"],
                        buffer,
                    ),
                )
                t_handle_client.start()

            except:
                return

    @staticmethod
    def __connect_to_server(server_data: ServerModel):
        my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        my_socket.settimeout(5)

        maxTries = 5
        retryInterval = 2

        for attempt in range(maxTries):
            try:
                my_socket.connect((server_data["ip"], 2137))
            except:
                print(
                    f"Attempt {attempt + 1}/{maxTries}: Connection refused. Retrying in {retryInterval} seconds..."
                )
                time.sleep(retryInterval)
            else:
                break
        else:
            print(
                f"Failed to connect to server after {maxTries} attempts. Maybe the server is down?"
            )
            return

        my_socket.settimeout(None)

        messages = message_store.fetch_messages_from_server(server_data["reference"])
        message_store.print_messages(messages)

        t_user_input = threading.Thread(
            target=HeadlessApp.__user_send_message, args=(my_socket,)
        )
        t_read_data = threading.Thread(
            target=HeadlessApp.__user_read_message, args=(my_socket,)
        )

        t_user_input.start()
        t_read_data.start()

        t_user_input.join()
        t_read_data.join()

    @staticmethod
    def __user_send_message(my_socket):
        global user_input
        user_input = ""

        user_data = user_store.user_data
        user_color = user_data["color"]

        print(f"{CONSOLE_USER_COLORS[user_color.upper()]}[You]: ", end="")
        sys.stdout.flush()

        while True:
            try:
                if msvcrt.kbhit():
                    char = msvcrt.getch().decode()

                    if char == "\r" or char == "\n" or char == "\r\n":
                        my_socket.send(user_input.encode())
                        print(
                            f"\n{CONSOLE_USER_COLORS[user_color.upper()]}[You]: ",
                            end="",
                        )
                        user_input = ""
                    else:
                        user_input += char

                        print(char, end="")
                        sys.stdout.flush()

                        if user_input.lower() == "exit":
                            raise KeyboardInterrupt

            except KeyboardInterrupt:
                my_socket.close()
                return

            except:
                print("Failed to send the message. Connection to the server is broken")
                return

    @staticmethod
    def __user_read_message(my_socket):
        user_data = user_store.user_data
        user_color = user_data["color"]

        while True:
            try:
                if len(my_socket.recv(1, socket.MSG_PEEK)):
                    incoming_data = my_socket.recv(1024).decode()

                    print(
                        f"\r{CONSOLE_COLORS['RESET']}{incoming_data}\n{CONSOLE_USER_COLORS[user_color.upper()]}[You]: {user_input}",
                        end="",
                    )

            except:
                print(
                    "Failed to read a message from server. Connection to the server is broken",
                    my_socket,
                )
                return

    @staticmethod
    def __server_input(
        connected_clients: typing.List[dict],
        server_socket,
        buffer: MessageBuffer,
        server_reference: firestore.DocumentReference,
    ):
        global server_input
        server_input = ""

        server_data = {"name": "server", "color": "server"}

        print(f"{CONSOLE_COLORS['SERVER']}[Server]: ", end="")
        sys.stdout.flush()

        while True:
            try:
                if msvcrt.kbhit():
                    char = msvcrt.getch().decode()

                    if char == "\r" or char == "\n" or char == "\r\n":
                        if not server_input.startswith("!"):
                            buffer.push(
                                {
                                    "id": help_functions.generate_random_id(),
                                    "server": server_reference,
                                    "user": server_reference,
                                    "text": server_input,
                                    "time": datetime.now(),
                                    "isServer": True,
                                }
                            )

                        for client in connected_clients:
                            for _, client_socket in client.items():
                                client_socket.send(
                                    HeadlessApp.__format_message(
                                        server_input, server_data
                                    ).encode()
                                )
                        print(f"\n{CONSOLE_COLORS['SERVER']}[Server]: ", end="")
                        server_input = ""
                    else:
                        server_input += char

                        print(char, end="")
                        sys.stdout.flush()

                        if server_input.lower() == "exit":
                            raise Exception

            except:
                print(f"{CONSOLE_COLORS['RESET']}\nShutting down server...")

            server_socket.close()

    @staticmethod
    def __handle_clients(
        connected_clients: typing.List[dict],
        current_client,
        server_reference: firestore.DocumentReference,
        buffer: MessageBuffer,
    ):
        current_client_ip, current_client_socket = current_client
        current_client_reference = user_store.find_user(current_client_ip)
        current_client_data = current_client_reference.get().to_dict()

        while True:
            try:
                if len(current_client_socket.recv(1, socket.MSG_PEEK)):
                    incoming_data = current_client_socket.recv(1024).decode()
                    formatted_message = HeadlessApp.__format_message(
                        incoming_data, current_client_data
                    )

                    print(
                        f"\r{CONSOLE_COLORS['RESET']}{formatted_message}\n{CONSOLE_COLORS['SERVER']}[Server]: {server_input}",
                        end="",
                    )

                    buffer.push(
                        {
                            "id": help_functions.generate_random_id(),
                            "server": server_reference,
                            "user": current_client_reference,
                            "text": incoming_data,
                            "time": datetime.now(),
                            "isServer": False,
                        }
                    )

                    for client in connected_clients:
                        for client_ip, client_socket in client.items():
                            if client_ip != current_client_ip:
                                client_socket.send(formatted_message.encode())
            except:
                return

    @staticmethod
    def __format_message(message_text: str, user_data: UserModel) -> str:
        server_timestamp = datetime.now()

        formatted_message = f"[{HeadlessApp.__map_timestamp(server_timestamp)}] {CONSOLE_USER_COLORS[user_data['color'].upper()]}[{user_data['name']}]: {message_text}{CONSOLE_COLORS['RESET']}"

        return formatted_message

    @staticmethod
    def __map_timestamp(date) -> str:
        return date.strftime("%d.%m.%y %H:%M")
