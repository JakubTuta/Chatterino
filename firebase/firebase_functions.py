import threading
import time
from typing import Union

from google.cloud import firestore

from src.colors import CONSOLE_COLORS

from .firebase_init import gc

hasDatabaseRead = threading.Event()

collections = {
    "users": gc.collection("users"),
    "servers": gc.collection("servers"),
    "messages": gc.collection("messages"),
}


def writeToDatabase(
    collectionName: str, data: dict
) -> Union[firestore.DocumentReference, None]:
    if collectionName not in collections:
        print("Collection does not exist")
        return

    userRef = collections[collectionName].add(data)
    return userRef


def setDocumentInDatabase(
    collectionName: str, documentID: str, data: dict
) -> Union[firestore.DocumentReference, None]:
    if collectionName not in collections:
        print("Collection does not exist")
        return

    userRef = collections[collectionName].document(documentID)
    userRef.set(data)
    return userRef


def readAllFromCollection(collectionName: str) -> Union[list, None]:
    if collectionName not in collections:
        print("Collection does not exist")
        return

    hasDatabaseRead.clear()

    collection = collections[collectionName]
    docs = collection.stream()

    mappedDocs = [doc.to_dict() for doc in docs]

    hasDatabaseRead.set()

    return mappedDocs


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
