import random
import re
import socket
import string
import sys

from .colors import CONSOLE_USER_COLORS


def tryMode() -> str:
    mode = ""

    try:
        mode = sys.argv[1]
        while mode.lower() != "headless" and mode.lower() != "gui":
            mode = input("Enter correct mode [headless / gui]: ")
    except IndexError:
        try:
            mode = input("Enter mode [headless / gui]: ")
            while mode.lower() != "headless" and mode.lower() != "gui":
                mode = input("Enter correct mode [headless / gui]: ")
        except KeyboardInterrupt:
            return "exit"

    return mode


def trySide() -> str:
    side = ""

    try:
        side = sys.argv[2]
        while side.lower() != "join" and side.lower() != "host":
            side = input("Enter correct action [join / host]: ")
    except IndexError:
        try:
            side = input("Enter action [join / host]: ")
            while side.lower() != "join" and side.lower() != "host":
                side = input("Enter correct action [join / host]: ")
        except KeyboardInterrupt:
            return "exit"

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


def getUserInfo() -> str:
    userName = socket.gethostname()
    userIp = socket.gethostbyname(userName)
    return userIp


def tryPassword(correctPassword: str):
    try:
        userInput = input("Enter password:\n")
        while userInput != correctPassword:
            userInput = input("Incorrect password. Try again:\n")
    except KeyboardInterrupt:
        return "exit"


def tryServerName():
    try:
        forbiddenWords = ["exit"]
        data = input(f"Enter server's name:\n")
        while data in forbiddenWords:
            data = input(f'You can\'t use "{data}". Try again:\n')
        return data
    except KeyboardInterrupt:
        return "exit"


def tryServerPassword():
    forbiddenWords = ["exit"]
    data = input(f"Enter server's password:\n")
    while data in forbiddenWords:
        data = input(f'You can\'t use "{data}". Try again:\n')
    return data


def tryUserName():
    try:
        forbiddenWords = ["back", "exit"]
        userInput = input("Enter your name in the chat:\n")
        while userInput in forbiddenWords:
            userInput = input(f'You can\'t use "{userInput}". Try again:\n')
        return userInput
    except KeyboardInterrupt:
        return "exit"


def tryUserColor():
    try:
        availableColors = list(CONSOLE_USER_COLORS.keys())
        availableColors.pop(0)
        userInput = input(
            f"Choose one of the following colors for your texts in chat:\n{', '.join(availableColors)}\n"
        )
        while userInput.upper() not in availableColors:
            userInput = input(f'You can\'t use "{userInput}". Try again:\n')
        return userInput
    except KeyboardInterrupt:
        return "exit"


def generateRandomId():
    characters = string.ascii_letters + string.digits
    return "".join(random.choice(characters) for _ in range(20))
