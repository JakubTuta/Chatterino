import help.functions as help_functions
from firebase_functions.userStore import UserStore

# from gui import GuiApp
from headless import HeadlessApp


def main():
    user_ip = help_functions.get_user_info()
    UserStore.get_user_data(user_ip)

    try:
        mode = help_functions.check_program_mode()
        side = help_functions.check_program_side()
    except KeyboardInterrupt:
        return

    if mode == "headless":
        HeadlessApp.run(side)

    # elif mode == "gui":
    #     GuiApp.run(side)


if __name__ == "__main__":
    main()
