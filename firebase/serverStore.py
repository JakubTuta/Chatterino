import os
import sys
import threading
import time

from src.colors import CONSOLE_COLORS

from .firebase_init import gc

mainDirectory = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(mainDirectory)


hasDatabaseRead = threading.Event()


def fetchServers():
    servers = []
    t1 = threading.Thread(target=loading, args=("Fetching servers, please wait",))
    t2 = threading.Thread(target=readActiveServers, args=(servers,))

    t1.start()
    t2.start()

    t2.join()
    t1.join()
    print(servers)


def loading(text: str):
    phrases = [
        f"{text}",
        f"{text}.",
        f"{text}..",
        f"{text}...",
    ]

    while True:
        for phrase in phrases:
            if hasDatabaseRead.is_set():
                print(" " * len(phrases[-1]), end="\r")
                hasDatabaseRead.clear()
                return

            print(
                f"{CONSOLE_COLORS['ALERT']}{phrase}{CONSOLE_COLORS['RESET']}", end="\r"
            )
            time.sleep(0.5)
        print(" " * len(phrases[-1]), end="\r")


def readActiveServers(serverList):
    hasDatabaseRead.clear()

    collection = gc.collection("servers")
    docs = collection.stream()

    mappedDocs = [doc.to_dict() for doc in docs]

    hasDatabaseRead.set()

    for doc in mappedDocs:
        serverList.append(doc)
