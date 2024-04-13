import firebase.userStore as user_store
import help.functions as help_functions

from .gui import GuiApp
from .headless import HeadlessApp


def main():
    user_ip = help_functions.get_user_info()
    user_data = user_store.fetch_user(user_ip)

    try:
        mode = help_functions.check_program_mode()
        side = help_functions.check_program_side()
    except KeyboardInterrupt:
        return

    if mode == "headless":
        HeadlessApp.run(side, user_data)

    elif mode == "gui":
        GuiApp.run(side, user_data)


if __name__ == "__main__":
    main()
