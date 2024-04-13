import msvcrt
import socket
import sys
import threading
import time
from datetime import datetime

from google.cloud import firestore

import firebase.messagesStore as message_store
import firebase.serverStore as server_store
import firebase.userStore as user_store
import help.functions as help_functions
from help.colors import CONSOLE_COLORS, CONSOLE_USER_COLORS
from help.messageBuffer import MessageBuffer
from models.userModel import UserModel

userInput = ""
serverInput = ""


class HeadlessApp:

    @staticmethod
    def run(side: str, user_data: UserModel):
        server_store.fetch_servers()

        if side == "join":
            HeadlessApp.join_server(user_data["reference"], user_data)

        else:
            if not server_store.is_server_in_database(user_data["ip"]):
                if not HeadlessApp.create_server(user_data["ip"]):
                    return

            HeadlessApp.host_server(user_data["ip"])

            server_data = server_store.find_server(server_ip=user_data["ip"])

            server_store.close_server(server_reference)
            print("Server shut down")

    @staticmethod
    def join_server(user_reference: firestore.DocumentReference, user_data: UserModel):
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

        if not server_store.is_user_on_server(server, user_reference):
            server_store.add_user_to_server(server, user_reference)

        HeadlessApp.__connectToServer(server, user_data)

    @staticmethod
    def createServer(servers, userIp):
        serverName = input("Enter server's name:")
        while not isServerNameUnique(servers, serverName):
            print("This name already exists. Server name has to be unique!")
            serverName = input("Enter server's name:")

        isPassword = input(
            "Do you want your server password protected? [yes \ no]\n",
        )

        isPassword = True if isPassword.lower() == "yes" else False

        password = ""
        if isPassword:
            password = input(f"Enter server's password:\n")

        serverData = {
            "name": serverName,
            "ip": userIp,
            "isPassword": isPassword,
            "password": password,
            "isActive": True,
            "users": [],
        }

        createServer(serverData)
        print("Server created!")
        return True

    @staticmethod
    def hostServer(serverIp):
        print("Creating server socket")

        serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        serverSocket.bind((serverIp, 2137))
        serverSocket.listen(5)

        print("Server socket is created")

        serverRef = findServerRef(serverIp)
        openServer(serverRef)

        print("Waiting for users", end="\n\n")

        messages = fetch_messages_from_server(serverRef)
        print_messages(messages)

        connectedClients = []
        buffer = MessageBuffer()

        t_serverInput = threading.Thread(
            target=HeadlessApp.__serverInput,
            args=(connectedClients, serverSocket, buffer, serverRef),
        )
        t_serverInput.start()

        try:
            while True:
                clientSocket, clientAddress = serverSocket.accept()
                clientIp = clientAddress[0]

                connectedClients.append({clientIp: clientSocket})
                print(
                    f"\r{CONSOLE_COLORS['RESET']}Accepted connection from client: {clientIp}\n{CONSOLE_COLORS['SERVER']}[Server]: ",
                    end="",
                )

                t_handleClient = threading.Thread(
                    target=HeadlessApp.__handleClients,
                    args=(
                        connectedClients,
                        [clientIp, clientSocket],
                        serverRef,
                        buffer,
                    ),
                )
                t_handleClient.start()
        except:
            return

    @staticmethod
    def __connectToServer(server, serverRef, userColor):
        mySocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        mySocket.settimeout(5)

        maxTries = 5
        retryInterval = 2

        for attempt in range(maxTries):
            try:
                mySocket.connect((server["ip"], 2137))
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

        mySocket.settimeout(None)

        messages = fetch_messages_from_server(serverRef)
        print_messages(messages)

        t_userInput = threading.Thread(
            target=HeadlessApp.__userSendMessage, args=(mySocket, userColor)
        )
        t_readData = threading.Thread(
            target=HeadlessApp.__userReadMessage, args=(mySocket, userColor)
        )

        t_userInput.start()
        t_readData.start()

        t_userInput.join()
        t_readData.join()

    @staticmethod
    def __userSendMessage(mySocket, userColor):
        global userInput
        userInput = ""
        print(f"{CONSOLE_USER_COLORS[userColor.upper()]}[You]: ", end="")
        sys.stdout.flush()

        try:
            while True:
                if msvcrt.kbhit():
                    char = msvcrt.getch().decode()

                    if char == "\r" or char == "\n" or char == "\r\n":
                        mySocket.send(userInput.encode())
                        print(
                            f"\n{CONSOLE_USER_COLORS[userColor.upper()]}[You]: ", end=""
                        )
                        userInput = ""
                    else:
                        userInput += char

                        print(char, end="")
                        sys.stdout.flush()

                        if userInput.lower() == "exit":
                            raise KeyboardInterrupt

        except KeyboardInterrupt:
            mySocket.close()

        except:
            print("Failed to send the message. Connection to the server is broken")
            return

    @staticmethod
    def __userReadMessage(mySocket, userColor):
        while True:
            try:
                if len(mySocket.recv(1, socket.MSG_PEEK)):
                    incomingData = mySocket.recv(1024).decode()
                    print(
                        f"\r{CONSOLE_COLORS['RESET']}{incomingData}\n{CONSOLE_USER_COLORS[userColor.upper()]}[You]: {userInput}",
                        end="",
                    )

            except:
                print(
                    "Failed to read a message from server. Connection to the server is broken",
                    mySocket,
                )
                return

    @staticmethod
    def __serverInput(connectedClients, serverSocket, buffer, serverRef):
        global serverInput
        serverInput = ""
        serverData = {"name": "server", "color": "server"}

        print(f"{CONSOLE_COLORS['SERVER']}[Server]: ", end="")
        sys.stdout.flush()

        try:
            while True:
                if msvcrt.kbhit():
                    char = msvcrt.getch().decode()

                    if char == "\r" or char == "\n" or char == "\r\n":
                        if not serverInput.startswith("!"):
                            buffer.push(
                                {
                                    "id": generateRandomId(),
                                    "server": serverRef,
                                    "user": serverRef,
                                    "text": serverInput,
                                    "time": datetime.now(),
                                    "isServer": True,
                                }
                            )

                        for client in connectedClients:
                            for _, clientSocket in client.items():
                                clientSocket.send(
                                    HeadlessApp.__formatMessage(
                                        serverInput, serverData
                                    ).encode()
                                )
                        print(f"\n{CONSOLE_COLORS['SERVER']}[Server]: ", end="")
                        serverInput = ""
                    else:
                        serverInput += char

                        print(char, end="")
                        sys.stdout.flush()

                        if serverInput.lower() == "exit":
                            raise

        except:
            print(f"{CONSOLE_COLORS['RESET']}\nShutting down server...")

        finally:
            serverSocket.close()

    @staticmethod
    def __handleClients(connectedClients, currClient, serverRef, buffer):
        currClientIp, currClientSocket = currClient
        currClientRef = findUser(currClientIp)
        currClientData = currClientRef.get().to_dict()

        while True:
            try:
                if len(currClientSocket.recv(1, socket.MSG_PEEK)):
                    incomingData = currClientSocket.recv(1024).decode()
                    formattedMessage = HeadlessApp.__formatMessage(
                        incomingData, currClientData
                    )
                    print(
                        f"\r{CONSOLE_COLORS['RESET']}{formattedMessage}\n{CONSOLE_COLORS['SERVER']}[Server]: {serverInput}",
                        end="",
                    )
                    buffer.push(
                        {
                            "id": generateRandomId(),
                            "server": serverRef,
                            "user": currClientRef,
                            "text": incomingData,
                            "time": datetime.now(),
                            "isServer": False,
                        }
                    )

                    for client in connectedClients:
                        for clientIp, clientSocket in client.items():
                            if clientIp != currClientIp:
                                clientSocket.send(formattedMessage.encode())
            except:
                return

    @staticmethod
    def __formatMessage(messageText, userData):
        serverTimestamp = datetime.now()
        return f"[{mapTimestamp(serverTimestamp)}] {CONSOLE_USER_COLORS[userData['color'].upper()]}[{userData['name']}]: {messageText}{CONSOLE_COLORS['RESET']}"
