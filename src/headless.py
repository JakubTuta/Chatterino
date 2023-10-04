import socket
import threading
import time
from datetime import datetime

from google.cloud import firestore

from firebase.messagesStore import fetchMessagesFromServer, mapTimestamp, printMessages
from firebase.serverStore import (
    addUserToServer,
    closeServer,
    createServer,
    fetchServers,
    findServer,
    findServerRef,
    isServerNameUnique,
    isUserOnServer,
    openServer,
    serverExistsInDatabase,
)
from firebase.usersStore import findUser

from .colors import CONSOLE_COLORS, CONSOLE_USER_COLORS
from .functions import generateRandomId, tryPassword
from .messageBuffer import MessageBuffer


class HeadlessApp:
    @staticmethod
    def run(side: str, userData: dict, userRef: firestore.DocumentReference):
        allServers = fetchServers()
        activeServers = [server for server in allServers if server["isActive"]]

        if side == "join":
            HeadlessApp.joinServer(activeServers, userRef, userData["color"])

        else:
            if not serverExistsInDatabase(allServers, userData["ip"]):
                if not HeadlessApp.createServer(allServers, userData["ip"]):
                    return
            HeadlessApp.hostServer(userData["ip"])

        serverRef = findServerRef(userData["ip"])
        closeServer(serverRef)
        print("Server shut down")

    @staticmethod
    def joinServer(servers, userRef, userColor):
        if len(servers) == 0:
            print("There are not any online servers")
            return

        serverNames = [server["name"] for server in servers]

        print("Currently online servers:\n")
        for index, server in enumerate(serverNames):
            print(f"{index + 1}: {server}")

        userInput = input("\nEnter server's name:\n")
        while not userInput in serverNames:
            userInput = input("Incorrect server name. Try again:\n")
        print()

        server = findServer(servers, userInput)
        serverRef = findServerRef(server["ip"])

        if server["isPassword"]:
            tryPassword(server["password"])
            print("Correct password!\n")

        if not isUserOnServer(servers, userRef):
            addUserToServer(serverRef, server, userRef)

        HeadlessApp.__connectToServer(server, serverRef, userColor)

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

        mySocket.settimeout(5)

        messages = fetchMessagesFromServer(serverRef)
        printMessages(messages)

        t_userInput = threading.Thread(
            target=HeadlessApp.__userInput, args=(mySocket, userColor)
        )
        t_readData = threading.Thread(
            target=HeadlessApp.__readData, args=(mySocket, userColor)
        )

        t_userInput.start()
        t_readData.start()

    @staticmethod
    def __userInput(mySocket, userColor):
        try:
            while True:
                userInput = input(f"{CONSOLE_USER_COLORS[userColor.upper()]}[You]: ")
                print(f"{CONSOLE_COLORS['RESET']}", end="")

                if userInput == "exit":
                    raise KeyboardInterrupt

                mySocket.send(userInput.encode())

        except ConnectionAbortedError:
            print("Failed to send the message. Connection to the server is broken")
            return

        except KeyboardInterrupt:
            mySocket.close()

    @staticmethod
    def __readData(mySocket, userColor):
        while True:
            try:
                if len(mySocket.recv(1, socket.MSG_PEEK)):
                    incomingData = mySocket.recv(1024).decode()
                    print(
                        f"\r{CONSOLE_COLORS['RESET']}{incomingData}\n{CONSOLE_USER_COLORS[userColor.upper()]}[You]: ",
                        end="",
                    )

            except ConnectionAbortedError:
                print(
                    "Failed to read a message from server. Connection to the server is broken"
                )
                return

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

        print("Waiting for users")

        connectedClients = []
        buffer = MessageBuffer()

        t_serverInput = threading.Thread(
            target=HeadlessApp.__serverInput,
            args=(connectedClients, serverSocket),
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
    def __serverInput(connectedClients, serverSocket):
        serverData = {"name": "server", "color": "server"}

        try:
            while True:
                serverInput = input(f"{CONSOLE_COLORS['SERVER']}[Server]: ")
                print(f"{CONSOLE_COLORS['RESET']}", end="")

                if serverInput.lower() == "exit":
                    raise

                for client in connectedClients:
                    for _, clientSocket in client.items():
                        clientSocket.send(
                            HeadlessApp.__formatMessage(
                                serverInput, serverData
                            ).encode()
                        )

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
            if len(currClientSocket.recv(1, socket.MSG_PEEK)):
                incomingData = currClientSocket.recv(1024).decode()
                formattedMessage = HeadlessApp.__formatMessage(
                    incomingData, currClientData
                )
                print(
                    f"\r{CONSOLE_COLORS['RESET']}{formattedMessage}\n{CONSOLE_COLORS['SERVER']}[Server]: ",
                    end="",
                )
                buffer.push(
                    {
                        "id": generateRandomId(),
                        "server": serverRef,
                        "user": currClientRef,
                        "text": incomingData,
                        "time": datetime.now(),
                    }
                )

                for client in connectedClients:
                    for clientIp, clientSocket in client.items():
                        if clientIp != currClientIp:
                            clientSocket.send(formattedMessage.encode())

    @staticmethod
    def __formatMessage(messageText, userData):
        serverTimestamp = datetime.now()
        return f"[{mapTimestamp(serverTimestamp)}] {CONSOLE_USER_COLORS[userData['color'].upper()]}[{userData['name']}]: {messageText}{CONSOLE_COLORS['RESET']}"
