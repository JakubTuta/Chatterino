from firebase.serverStore import fetchServers
from src.functions import tryMode, trySide
from src.gui import GuiApp
from src.headless import HeadlessApp

# if __name__ == "__main__":
#     mode = tryMode()
#     side = trySide()

#     if mode == "headless":
#         headlessApp = HeadlessApp(side)
#         headlessApp.run()

#     else:
#         guiApp = GuiApp(side)
#         guiApp.run()

fetchServers()
