import customtkinter as ctk
from firebase.serverStore import fetchServers, findServerRef
from firebase.messagesStore import fetchMessagesFromServer
from google.cloud import firestore
from .colors import HEX_COLORS
import threading

selectedServer = None


class ScrollableFrame(ctk.CTkScrollableFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.master = master
        self.width = kwargs["width"]
        self.height = kwargs["height"]

    def drawServerList(self, servers):
        font = ctk.CTkFont(family="Arial", size=25)

        for i, server in enumerate(servers):
            ctk.CTkButton(
                self,
                command=lambda: self.__handleChooseServerButtonClick(server),
                text=server["name"],
                font=font,
                width=self.width,
                height=50
            ).pack(pady=10, padx=50)

    def drawMessages(self, messages, myIp):
        font = ctk.CTkFont(family="Arial", size=15)
        userRefs = {}

        for i, message in enumerate(messages):
            userRef = message["user"]
            if userRef.id not in userRefs:
                user = userRef.get().to_dict()
                userRefs[userRef.id] = user
            else:
                user = userRefs[userRef.id]

            ctk.CTkLabel(
                self,
                text=message["text"],
                font=font,
                fg_color=(HEX_COLORS[user["color"].upper()]),
                corner_radius=15,
                justify="left"
            ).pack(pady=10, padx=10, ipady=10, ipadx=20, side="bottom")

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
                return False


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
            pass

        elif side == "join":
            GuiApp.createServersWindow(activeServers, userData)

    @staticmethod
    def createServersWindow(servers, userData):
        app = Window(width=GuiApp.windowWidth, height=GuiApp.windowHeight)

        frame = ScrollableFrame(
            master=app,
            width=GuiApp.windowWidth * .9,
            height=GuiApp.windowHeight * .75,
        )
        frame.pack()
        frame.drawServerList(servers)

        app.mainloop()

        GuiApp.createMessagesWindow(userData)

    @staticmethod
    def createMessagesWindow(userData):
        font = ctk.CTkFont(family="Arial", size=15)

        app = Window(width=GuiApp.windowWidth, height=GuiApp.windowHeight)

        frame = ScrollableFrame(
            master=app,
            width=GuiApp.windowWidth * .9,
            height=GuiApp.windowHeight * .8,
        )
        frame.pack()

        entry = ctk.CTkEntry(
            master=app,
            placeholder_text="Enter message...",
            width=int(GuiApp.windowWidth * .9),
            height=int(GuiApp.windowHeight * .2),
            font=font
        )
        entry.pack()

        serverRef = findServerRef(selectedServer["ip"])
        messages = fetchMessagesFromServer(serverRef)

        frame.drawMessages(messages, userData["ip"])

        t_messageInput = threading.Thread(target=GuiApp.__handleInput)
        t_messageInput.start()

        t_messageOutput = threading.Thread(target=GuiApp.__handleOutput)
        t_messageOutput.start()

        app.mainloop()

    @staticmethod
    def __handleInput():
        pass
    
    @staticmethod
    def __handleOutput():
        pass
