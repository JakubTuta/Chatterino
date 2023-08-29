from firebase_functions import readAllFromCollection
from functions import tryMode, trySide
from gui import GuiApp
from headless import HeadlessApp

# t1 = threading.Thread(target=printTextWhileWaiting, args=("wait",))
# t2 = threading.Thread(target=readActiveServersFromDatabase)

# t1.start()
# t2.start()

# t2.join()
# t1.join()

# if __name__ == "__main__":
#     mode = tryMode()
#     side = trySide()

#     if mode == "headless":
#         headlessApp = HeadlessApp(side)
#         headlessApp.run()

#     else:
#         guiApp = GuiApp(side)
#         guiApp.run()

print(readAllFromCollection("users"))
