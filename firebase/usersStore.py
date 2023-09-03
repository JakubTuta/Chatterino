import threading
import time
import warnings

from src.colors import CONSOLE_COLORS
from src.functions import tryUserColor, tryUserName

from .firebase_init import gc

isDatabaseBusy = threading.Event()
isDatabaseBusy.clear()

isDatabaseHold = threading.Event()
isDatabaseHold.clear()

collectionName = "users"


def loading(text: str):
    phrases = [
        f"{text}",
        f"{text}.",
        f"{text}..",
        f"{text}...",
    ]

    while True:
        for phrase in phrases:
            if not isDatabaseBusy.is_set():
                print(" " * len(phrase), end="\r")
                return
            elif isDatabaseHold.is_set():
                break

            print(
                f"{CONSOLE_COLORS['ALERT']}{phrase}{CONSOLE_COLORS['RESET']}",
                end="\r",
            )
            time.sleep(0.5)

        if not isDatabaseHold.is_set():
            print(" " * len(phrases[-1]), end="\r")


def fetchUser(userIp):
    users = []

    t1 = threading.Thread(target=loading, args=("Fetching user, please wait",))
    t2 = threading.Thread(target=findOrCreateUser, args=(users, userIp))

    t2.start()
    t1.start()

    t2.join()
    t1.join()

    return users


def findOrCreateUser(users, userIp):
    isDatabaseBusy.set()

    if doesUserExist(userIp):
        userRef = findUser(userIp)
        userData = userRef.get().to_dict()
    else:
        isDatabaseHold.set()
        userData = prepareNewUser(userIp)
        isDatabaseHold.clear()

        userRef = createUser(userData)

    users.append(userRef)
    users.append(userData)

    isDatabaseBusy.clear()


def doesUserExist(userIp: str) -> bool:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        collection = gc.collection(collectionName)
        query = collection.where("ip", "==", userIp)
        docs = query.stream()

    for _ in docs:
        return True
    return False


def findUser(userIp: str):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        collection = gc.collection(collectionName)
        query = collection.where("ip", "==", userIp)
        docs = query.stream()

    for doc in docs:
        return doc.reference
    return None


def prepareNewUser(userIp: str) -> dict:
    return {"name": tryUserName(), "ip": userIp, "color": tryUserColor()}


def createUser(userData):
    userRef = gc.collection(collectionName).add(userData)
    return userRef
