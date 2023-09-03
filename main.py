from firebase.usersStore import fetchUser
from src.functions import getUserInfo, trySide
from src.gui import GuiApp
from src.headless import HeadlessApp

if __name__ == "__main__":
    userIp = getUserInfo()
    userRef, userData = fetchUser(userIp)

    # mode = tryMode()
    side = trySide()
    print()

    mode = "headless"

    if mode == "headless":
        HeadlessApp.run(side, userData, userRef)

    else:
        GuiApp.run(side, userData, userRef)
