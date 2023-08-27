import re
import sys
import threading
import time

from colors import CONSOLE_COLORS

hasDatabaseReadServers = threading.Event()


def tryMode() -> str:
    # headless / gui

    mode = ""

    try:
        mode = sys.argv[1]
        while mode.lower() != "headless" and mode.lower() != "gui":
            mode = input("Please enter correct mode [headless / gui]: ")
    except IndexError:
        mode = input("Please enter mode [headless / gui]: ")
        while mode.lower() != "headless" and mode.lower() != "gui":
            mode = input("Enter correct mode [headless / gui]: ")
    except KeyboardInterrupt:
        pass

    return mode


def trySide() -> str:
    # join / host

    side = ""

    try:
        side = sys.argv[2]
        while side.lower() != "join" and side.lower() != "host":
            side = input("Please enter correct action [join / host]: ")
    except IndexError:
        side = input("Please enter action [join / host]: ")
        while side.lower() != "join" and side.lower() != "host":
            side = input("Enter correct action [join / host]: ")
    except KeyboardInterrupt:
        pass

    return side


def isValidIpAndPort(userInput: str) -> bool:
    pattern = r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d{1,4}$"
    if re.match(pattern, userInput) is not None:
        myIp, myPort = userInput.split(":")
        for num in myIp.split("."):
            if not (0 <= int(num) <= 255):
                return False
        if not (1 <= int(myPort) <= 9999):
            return False
        return True
    return False


def isValidIp(userInput: str) -> bool:
    pattern = r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$"
    if re.match(pattern, userInput) is not None:
        for num in userInput.split("."):
            if not (0 <= int(num) <= 255):
                return False
        return True
    return False


def readActiveServersFromDatabase():
    print("reading database")
    time.sleep(3)
    print("database finished")
    hasDatabaseReadServers.set()


def printTextWhileWaiting(text: str):
    phrases = [
        f"{text}",
        f"{text}.",
        f"{text}..",
        f"{text}...",
    ]

    while True:
        for phrase in phrases:
            if hasDatabaseReadServers.is_set():
                return

            print(
                f"{CONSOLE_COLORS['ALERT']}{phrase}{CONSOLE_COLORS['RESET']}", end="\r"
            )
            time.sleep(0.5)
        print(" " * len(phrases[-1]), end="\r")
