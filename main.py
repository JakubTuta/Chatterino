from firebase.usersStore import fetchUser
from src.functions import getUserInfo, tryMode, trySide
from src.gui import GuiApp
from src.headless import HeadlessApp


def main():
    userIp = getUserInfo()
    userRef, userData = fetchUser(userIp)

    # mode = tryMode()
    mode = "headless"

    if mode == "exit":
        return

    side = trySide()

    if side == "exit":
        return

    print()

    if mode == "headless":
        HeadlessApp.run(side, userData, userRef)

    else:
        GuiApp.run(side, userData, userRef)


if __name__ == "__main__":
    main()
