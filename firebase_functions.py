from typing import Union

from google.cloud import firestore

from firebase_init import gc

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

    collection = collections[collectionName]
    docs = collection.stream()

    mappedDocs = [doc.to_dict() for doc in docs]

    return mappedDocs
