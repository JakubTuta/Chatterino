import socket
import threading
import time
from datetime import datetime

import customtkinter as ctk
from google.cloud import firestore

from firebase_functions.messagesStore import fetch_messages_from_server
from firebase_functions.serverStore import (
    addUserToServer,
    closeServer,
    createServer,
    fetchServers,
    findServerRef,
    isServerNameUnique,
    isUserOnServer,
    openServer,
    serverExistsInDatabase,
)
from firebase_functions.userStore import findUser

from .help.colors import HEX_COLORS
from .help.functions import generateRandomId
from .help.messageBuffer import MessageBuffer

selectedServer = None


class ScrollableFrame(ctk.CTkScrollableFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.master = master
        self.width = kwargs["width"]
        self.height = kwargs["height"]
        self.userRefs = {}

    def drawServerList(self, servers):
        font = ctk.CTkFont(family="Arial", size=25)

        for server in servers:
            ctk.CTkButton(
                self,
                command=lambda: self.__handleChooseServerButtonClick(server),
                text=server["name"],
                font=font,
                width=self.width,
                height=50,
            ).pack(pady=10, padx=50)

    def drawMessages(self, messages, myIp):
        font = ctk.CTkFont(family="Arial", size=18)

        for message in messages:
            userRef = message["user"]
            if userRef.id not in self.userRefs:
                user = userRef.get().to_dict()
                self.userRefs[userRef.id] = user
            else:
                user = self.userRefs[userRef.id]

            anchor = "e" if user["ip"] == myIp else "w"

            ctk.CTkLabel(self, text=user["name"], justify="left").pack(
                padx=10, anchor=anchor
            )

            ctk.CTkLabel(
                self,
                text=message["text"],
                font=font,
                fg_color=(HEX_COLORS[user["color"].upper()]),
                corner_radius=15,
                justify="left",
                wraplength=self.width - 200,
            ).pack(padx=5, pady=5, ipadx=15, ipady=5, anchor=anchor)

    def drawMessage(self, message, userRef):
        font = ctk.CTkFont(family="Arial", size=18)

        if userRef.id not in self.userRefs:
            user = userRef.get().to_dict()
            self.userRefs[userRef.id] = user
        else:
            user = self.userRefs[userRef.id]

        ctk.CTkLabel(self, text=user["name"], justify="left").pack(padx=10, anchor="e")

        ctk.CTkLabel(
            self,
            text=message,
            font=font,
            fg_color=(HEX_COLORS[user["color"].upper()]),
            corner_radius=15,
            justify="left",
            wraplength=self.width - 200,
        ).pack(padx=5, pady=5, ipadx=15, ipady=5, anchor="e")

    def __handleChooseServerButtonClick(self, server):
        if server["isPassword"]:
            ScrollableFrame.passwordDialog(server)

        global selectedServer
        selectedServer = server
        self.destroy()
        self.master.destroy()

    @staticmethod
    def passwordDialog(selectedServer):
        while True:
            dialog = ctk.CTkInputDialog(text="Enter password", title="Password")
            data = dialog.get_input()

            if data == selectedServer["password"]:
                return True

            if not data:
                exit(1)


class Window(ctk.CTk):
    def __init__(self, **kwargs):
        width = kwargs.pop("width", 0)
        height = kwargs.pop("height", 0)
        super().__init__()

        self.geometry(f"{width}x{height}")
        self.resizable(False, False)


class GuiApp:
    windowWidth, windowHeight = 600, 700

    @staticmethod
    def run(side: str, userData: dict, userRef: firestore.DocumentReference):
        allServers = fetchServers()
        activeServers = [server for server in allServers if server["isActive"]]

        if side == "host":
            if not serverExistsInDatabase(allServers, userData["ip"]):
                if not GuiApp.createServer(allServers, userData["ip"]):
                    return
            serverRef = findServerRef(userData["ip"])
            GuiApp.hostServer(userData["ip"])
            closeServer(serverRef)

        elif side == "join":
            GuiApp.createServersWindow(activeServers, userData, userRef)

    @staticmethod
    def createServersWindow(
        servers: list, userData: dict, userRef: firestore.DocumentReference
    ):
        app = Window(width=GuiApp.windowWidth, height=GuiApp.windowHeight)

        frame = ScrollableFrame(
            master=app,
            width=GuiApp.windowWidth * 0.9,
            height=GuiApp.windowHeight * 0.75,
        )
        frame.pack()
        frame.drawServerList(servers)

        app.mainloop()

        if selectedServer:
            GuiApp.joinServer(userData, userRef)

    @staticmethod
    def joinServer(userData: dict, userRef: firestore.DocumentReference):
        mySocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        mySocket.settimeout(5)

        maxTries = 5
        retryInterval = 2

        for attempt in range(maxTries):
            try:
                mySocket.connect((selectedServer["ip"], 2137))
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

        serverRef = findServerRef(selectedServer["ip"])
        if not isUserOnServer(selectedServer, userRef):
            addUserToServer(serverRef, selectedServer, userRef)

        GuiApp.createMessagesWindow(userData, mySocket, userRef)

    @staticmethod
    def createMessagesWindow(
        userData: dict, mySocket: socket.socket, userRef: firestore.DocumentReference
    ):
        def __handleButtonPress(event=None):
            GuiApp.__userSendMessage(frame, mySocket, entry.get(), userRef)
            entry.delete(0, ctk.END)

        app = Window(width=GuiApp.windowWidth, height=GuiApp.windowHeight)
        app.bind("<Return>", __handleButtonPress)

        font = ctk.CTkFont(family="Arial", size=15)

        frame = ScrollableFrame(
            master=app,
            width=GuiApp.windowWidth * 0.9,
            height=GuiApp.windowHeight * 0.9,
        )
        frame.pack()

        entry = ctk.CTkEntry(
            master=app,
            placeholder_text="Enter message...",
            width=int(GuiApp.windowWidth * 0.9),
            height=int(GuiApp.windowHeight * 0.1),
            font=font,
        )
        entry.pack()

        serverRef = findServerRef(selectedServer["ip"])
        messages = fetch_messages_from_server(serverRef)
        frame.drawMessages(messages, userData["ip"])

        t_messageRead = threading.Thread(
            target=GuiApp.__userReadMessage, args=(frame, mySocket)
        )
        t_messageRead.start()

        app.mainloop()

    @staticmethod
    def __userReadMessage(window: ctk.CTk, mySocket: socket.socket):
        while True:
            try:
                if len(mySocket.recv(1, socket.MSG_PEEK)):
                    incomingData = mySocket.recv(1024).decode()
                    userRef, message = incomingData.split(":")
                    window.drawMessage(message, userRef)

            except:
                print(
                    "Failed to read a message from server. Connection to the server is broken"
                )
                return

    @staticmethod
    def __userSendMessage(
        window: ctk.CTk,
        mySocket: socket.socket,
        message: str,
        userRef: firestore.DocumentReference,
    ):
        try:
            mySocket.send(message.encode())
            window.drawMessage(message, userRef)
        except:
            return

    @staticmethod
    def createServer(servers: list, myIp: str):
        nameDialog = ctk.CTkInputDialog(
            text="Enter server's name:", title="Server's name"
        )
        name = nameDialog.get_input()

        if not name or name == "":
            return False

        while not isServerNameUnique(servers, name):
            nameDialog = ctk.CTkInputDialog(
                text="(Name already exists. Choose another one)\nEnter server's name:",
                title="Server's name",
            )
            name = nameDialog.get_input()

            if not name or name == "":
                return False

        passwordDialog = ctk.CTkInputDialog(
            text="Enter server's password\nLeave empty if you want no password",
            title="Server's password",
        )
        password = passwordDialog.get_input()

        if not password:
            isPassword = False
            password = ""
        else:
            isPassword = True

        serverData = {
            "name": name,
            "ip": myIp,
            "isPassword": isPassword,
            "password": password,
            "isActive": True,
            "users": [],
        }

        createServer(serverData)
        return True

    @staticmethod
    def hostServer(serverIp: str):
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

        try:
            while True:
                clientSocket, clientAddress = serverSocket.accept()
                clientIp = clientAddress[0]

                connectedClients.append({clientIp: clientSocket})

                t_clientHandle = threading.Thread(
                    target=GuiApp.__handleClients,
                    args=(
                        connectedClients,
                        [clientIp, clientSocket],
                        serverRef,
                        buffer,
                    ),
                )
                t_clientHandle.start()

        except:
            return

    @staticmethod
    def __handleClients(
        connectedClients: list,
        currClient: tuple,
        serverRef: firestore.DocumentReference,
        buffer: MessageBuffer,
    ):
        currClientIp, currClientSocket = currClient
        currClientRef = findUser(currClientIp)
        # currClientData = currClientRef.get().to_dict()

        while True:
            try:
                if len(currClientSocket.recv(1, socket.MSG_PEEK)):
                    incomingData = currClientSocket.recv(1024).decode()

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
                                clientSocket.send(
                                    f"{currClientRef}:{incomingData}".encode()
                                )
            except ConnectionResetError:
                return
