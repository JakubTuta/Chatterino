from google.cloud import firestore
import tkinter as tk
import customtkinter as ctk


class ScrollableFrame(ctk.CTkScrollableFrame):
    def __init__(self, master, **kwargs):
        servers = kwargs.pop("servers", [])
        super().__init__(master, **kwargs)

        font = ctk.CTkFont(family="Arial", size=25)

        for i, server in enumerate(servers):
            ctk.CTkButton(self, text=server, font=font, width=kwargs["width"], height=50) \
                .grid(row=i, column=0, pady=10, padx=5)


class GuiApp:
    windowWidth, windowHeight = 700, 700

    @staticmethod
    def run(side: str, userData: dict, userRef: firestore.DocumentReference):
        root = tk.Tk()
        root.geometry(f"{GuiApp.windowWidth}x{GuiApp.windowHeight}")
        root.resizable(False, False)

        GuiApp.createServerSelectionView(root)

        root.mainloop()

    @staticmethod
    def createServerSelectionView(root):
        def enterPassword():
            ctk.CTkLabel(root, text="Enter password", font=font).grid(row=2, column=0, pady=10)

            entry = ctk.CTkEntry(root)
            entry.grid(row=3, column=0, pady=10)

        font = ctk.CTkFont(family="Arial", size=25)

        ScrollableFrame(
            master=root,
            width=GuiApp.windowWidth * .9,
            height=GuiApp.windowHeight * .75,
            servers=["jeden", "dwa"]
        ).pack()

        ctk.CTkButton(root, text="Join!", font=font).pack(pady=10)
