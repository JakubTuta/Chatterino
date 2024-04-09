import threading
import typing

from google.cloud import firestore

from src.colors import CONSOLE_COLORS, CONSOLE_USER_COLORS

from .firebase_init import firestore_client
from .store import Store


class MessagesStore(Store):
    collection = firestore_client.collection("messages")

    @staticmethod
    def fetch_messages_from_server(
        server_ref: firestore.DocumentReference,
    ) -> typing.List[dict]:
        messages = []

        t1 = threading.Thread(
            target=Store._loading, args=("Fetching messages, please wait",)
        )
        t2 = threading.Thread(
            target=MessagesStore.__read_messages_from_server,
            args=(messages, server_ref),
        )

        t2.start()
        t1.start()

        t2.join()
        t1.join()

        return messages

    @staticmethod
    def __map_timestamp(date) -> str:
        return date.strftime("%d.%m.%y %H:%M")

    @staticmethod
    def print_messages(messages: list):
        userRefs = {}

        for message in messages:
            userRef = message["user"]
            if userRef.id not in userRefs:
                user = userRef.get().to_dict()
                userRefs[userRef.id] = user
            else:
                user = userRefs[userRef.id]

            if "isServer" in message and message["isServer"]:
                print(
                    f"[{MessagesStore.__map_timestamp(message['time'])}] {CONSOLE_USER_COLORS['SERVER']}[Server]: {message['text']}{CONSOLE_COLORS['RESET']}"
                )
            else:
                print(
                    f"[{MessagesStore.__map_timestamp(message['time'])}] {CONSOLE_USER_COLORS[user['color'].upper()]}[{user['name']}]: {message['text']}{CONSOLE_COLORS['RESET']}"
                )

    @staticmethod
    def create_message(message_data: dict) -> firestore.DocumentReference:
        message_ref = MessagesStore.collection.add(message_data)

        return message_ref

    @staticmethod
    def __read_messages_from_server(
        messages: list, server_ref: firestore.DocumentReference
    ):
        Store.is_database_busy.set()

        query = MessagesStore.collection.where("server", "==", server_ref).order_by(
            "time", "ASCENDING"
        )
        docs = query.stream()

        for doc in docs:
            messages.append(doc.to_dict())

        Store.is_database_busy.clear()
