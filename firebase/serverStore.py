import threading
import time
import warnings
from typing import Union

from google.cloud import firestore

from src.colors import CONSOLE_COLORS

from .firebase_init import gc

isDatabaseBusy = threading.Event()
isDatabaseBusy.clear()

collectionName = "servers"


def fetchServers():
    servers = []
    t1 = threading.Thread(target=loading, args=("Fetching servers, please wait",))
    t2 = threading.Thread(target=readServers, args=(servers,))

    t2.start()
    t1.start()

    t2.join()
    t1.join()

    return servers


def createServer(data):
    t1 = threading.Thread(target=loading, args=("Creating a server, please wait",))
    t2 = threading.Thread(target=createServerInDatabase, args=(data,))

    t2.start()
    t1.start()

    t2.join()
    t1.join()


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


def readServers(serverList: list):
    isDatabaseBusy.set()

    collection = gc.collection(collectionName)
    docs = collection.stream()

    mappedDocs = [doc.to_dict() for doc in docs]

    for doc in mappedDocs:
        serverList.append(doc)

    isDatabaseBusy.clear()


def createServerInDatabase(data: dict) -> Union[firestore.DocumentReference, None]:
    isDatabaseBusy.set()

    serverRef = gc.collection(collectionName).add(data)

    isDatabaseBusy.clear()

    return serverRef


def serverExistsInDatabase(servers: list[dict], serverIp: str) -> bool:
    for server in servers:
        if serverIp == server["ip"]:
            return True
    return False


def isServerNameUnique(servers: list[dict], serverName: str) -> bool:
    for server in servers:
        if serverName == server["name"]:
            return False
    return True


def findServer(servers: list[dict], serverName: str) -> dict:
    for server in servers:
        if serverName == server["name"]:
            return server
    return None


def findServerRef(serverIp: str) -> Union[firestore.DocumentReference, None]:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        collection = gc.collection(collectionName)
        query = collection.where("ip", "==", serverIp)
        docs = query.stream()

    for doc in docs:
        return doc.reference
    return None


def isUserOnServer(servers: list[dict], userRef: firestore.DocumentReference) -> bool:
    for server in servers:
        for user in server["users"]:
            if user.id == userRef.id:
                return True
    return False


def addUserToServer(
    serverRef: firestore.DocumentReference,
    serverData: dict,
    newUserRef: firestore.DocumentReference,
):
    serverData["users"].append(newUserRef)
    serverRef.update({"users": serverData["users"]})


def openServer(serverRef):
    serverRef.update({"isActive": True})


def closeServer(serverRef):
    serverRef.update({"isActive": False})
