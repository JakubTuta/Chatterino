import threading
import time
import warnings

from src.colors import CONSOLE_COLORS, CONSOLE_USER_COLORS

from .firebase_init import gc

isDatabaseBusy = threading.Event()
isDatabaseBusy.clear()

collectionName = "messages"


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
                print(" " * len(phrases[-1]), end="\r")
                return

            print(
                f"{CONSOLE_COLORS['ALERT']}{phrase}{CONSOLE_COLORS['RESET']}", end="\r"
            )
            time.sleep(0.5)
        print(" " * len(phrases[-1]), end="\r")


def fetchMessagesFromServer(serverRef):
    messages = []

    t1 = threading.Thread(target=loading, args=("Fetching messages, please wait",))
    t2 = threading.Thread(target=readMessagesFromServer, args=(messages, serverRef))

    t2.start()
    t1.start()

    t2.join()
    t1.join()

    printMessages(messages)

    return messages


def mapTimestamp(date):
    return date.strftime("%d.%m.%y %H:%M")


def printMessages(messages):
    userRefs = {}

    for message in messages:
        userRef = message["user"]
        if userRef.id not in userRefs:
            user = userRef.get().to_dict()
            userRefs[userRef.id] = user
        else:
            user = userRefs[userRef.id]

        print(
            f"[{mapTimestamp(message['time'])}] {CONSOLE_USER_COLORS[user['color'].upper()]}{user['name']}: {message['text']}{CONSOLE_COLORS['RESET']}"
        )


def readMessagesFromServer(messages, serverRef):
    isDatabaseBusy.set()

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        collection = gc.collection(collectionName)
        query = collection.where("server", "==", serverRef).order_by(
            "time", "ASCENDING"
        )
        docs = query.stream()

    mappedDocs = [doc.to_dict() for doc in docs]

    for doc in mappedDocs:
        messages.append(doc)

    isDatabaseBusy.clear()


def createMessage(messageData):
    messageRef = gc.collection(collectionName).add(messageData)
    return messageRef
