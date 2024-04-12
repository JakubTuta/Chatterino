import threading
import typing

from google.cloud import firestore

from models.messageModel import MessageModel
from src.colors import CONSOLE_COLORS, CONSOLE_USER_COLORS

from .firebase_init import firestore_client
from .store import Store


class MessagesStore(Store):
    collection = firestore_client.collection("messages")

    @staticmethod
    def fetch_messages_from_server(
        server_ref: firestore.DocumentReference,
    ) -> typing.List[MessageModel]:
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
    def print_messages(messages: typing.List[MessageModel]):
        user_colors = {}

        for message in messages:
            user_ref = message["user"]

            if user_ref.id not in user_colors:
                user = user_ref.get().to_dict()
                user_color = user["color"]
                user_colors[user_ref.id] = user_color
            else:
                user_color = user_colors[user_ref.id]

            if "isServer" in message and message["isServer"]:
                print(
                    f"[{message['time']}] {CONSOLE_USER_COLORS['SERVER']}[Server]: {message['text']}{CONSOLE_COLORS['RESET']}"
                )
            else:
                print(
                    f"[{message['time']}] {CONSOLE_USER_COLORS[user_color.upper()]}[{user['name']}]: {message['text']}{CONSOLE_COLORS['RESET']}"
                )

    @staticmethod
    def create_message(message_data: MessageModel) -> firestore.DocumentReference:
        message_ref = MessagesStore.collection.add(message_data.to_map())

        return message_ref

    @staticmethod
    def __read_messages_from_server(
        messages: typing.List[MessageModel], server_ref: firestore.DocumentReference
    ):
        Store.is_database_busy.set()

        query = MessagesStore.collection.where("server", "==", server_ref).order_by(
            "time", "ASCENDING"
        )
        docs = query.stream()

        for doc in docs:
            messages.append(MessageModel(doc.to_dict(), doc.reference))

        Store.is_database_busy.clear()
