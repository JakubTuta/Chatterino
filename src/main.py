from firebase.usersStore import fetchUser

from .functions import getUserInfo, tryMode, trySide
from .gui import GuiApp
from .headless import HeadlessApp


def main():
    userIp = getUserInfo()
    userRef, userData = fetchUser(userIp)

    mode = tryMode()

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
