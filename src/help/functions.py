import random
import re
import socket
import string
import sys

from .colors import CONSOLE_USER_COLORS


def check_program_mode() -> str:
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
            raise KeyboardInterrupt

    return mode


def check_program_side() -> str:
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
            raise KeyboardInterrupt

    return side


def is_ip_valid(user_input: str) -> bool:
    pattern = r"^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"

    return re.match(pattern, user_input) is not None


def get_user_info() -> str:
    user_name = socket.gethostname()
    user_ip = socket.gethostbyname(user_name)

    return user_ip


def check_password(correct_password: str):
    try:
        userInput = input("Enter password:\n")
        while userInput != correct_password:
            userInput = input("Incorrect password. Try again:\n")
    except KeyboardInterrupt:
        raise KeyboardInterrupt


def try_user_color():
    available_colors = list(CONSOLE_USER_COLORS.keys())
    available_colors.pop(0)

    user_input = input(
        f"Choose one of the following colors for your texts in chat:\n{', '.join(available_colors)}\n"
    )

    while user_input.upper() not in available_colors:
        user_input = input(f'You can\'t use "{user_input}". Try again:\n')

    return user_input.upper()


def generate_random_id():
    characters = string.ascii_letters + string.digits

    return "".join(random.choice(characters) for _ in range(20))
