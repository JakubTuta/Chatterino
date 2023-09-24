from google.cloud import firestore
import customtkinter as ctk
from firebase.serverStore import fetchServers


selectedServer = None


class ScrollableFrame(ctk.CTkScrollableFrame):
    def __init__(self, master, **kwargs):
        servers = kwargs.pop("servers", [])
        super().__init__(master, **kwargs)

        font = ctk.CTkFont(family="Arial", size=25)

        for i, server in enumerate(servers):
            ctk.CTkButton(
                self,
                command=lambda: ScrollableFrame.__handleButtonClick(server),
                text=server["name"],
                font=font,
                width=kwargs["width"],
                height=50
            ).pack(pady=10, padx=50)

    @staticmethod
    def __handleButtonClick(server):
        global selectedServer
        selectedServer = server
        GuiApp.passwordDialog()


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
            GuiApp.createWindow(activeServers)

    @staticmethod
    def createWindow(servers):
        app = Window(width=GuiApp.windowWidth, height=GuiApp.windowHeight)

        GuiApp.createServerSelectionView(app, servers)

        app.mainloop()

    @staticmethod
    def createServerSelectionView(app, servers):
        ScrollableFrame(
            master=app,
            width=GuiApp.windowWidth * .9,
            height=GuiApp.windowHeight * .75,
            servers=servers
        ).pack()

    @staticmethod
    def passwordDialog():
        while ctk.CTkInputDialog(text="Enter password", title="Password").get_input() != selectedServer["password"]:
            pass
