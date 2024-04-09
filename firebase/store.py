import threading
import time

from src.colors import CONSOLE_COLORS


class Store:
    collection: str
    is_database_busy = threading.Event()
    is_database_busy.clear()

    @staticmethod
    def _loading(text: str):
        phrases = [
            f"{text}",
            f"{text}.",
            f"{text}..",
            f"{text}...",
        ]

        while True:
            for phrase in phrases:
                if not Store.is_database_busy.is_set():
                    print(" " * len(phrases[-1]), end="\r")
                    return

                print(
                    f"{CONSOLE_COLORS['ALERT']}{phrase}{CONSOLE_COLORS['RESET']}",
                    end="\r",
                )
                time.sleep(0.5)
            print(" " * len(phrases[-1]), end="\r")
