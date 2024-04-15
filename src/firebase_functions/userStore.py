import threading
import time
import typing

from google.cloud import firestore

import help.functions as help_functions
from help.colors import CONSOLE_COLORS
from models.userModel import UserModel

from .firebase_init import firestore_client
from .store import Store


class UserStore(Store):
    is_database_hold = threading.Event()
    is_database_hold.clear()

    collection = firestore_client.collection("servers")
    user_data: UserModel

    @staticmethod
    def fetch_users(user_ip: str) -> list:
        users = []

        t1 = threading.Thread(
            target=UserStore._loading, args=("Fetching user, please wait",)
        )
        t2 = threading.Thread(
            target=UserStore.__find_or_create_user, args=(users, user_ip)
        )

        t2.start()
        t1.start()

        t2.join()
        t1.join()

        return users

    @staticmethod
    def get_user_data(user_ip: str) -> typing.Optional[UserModel]:
        query = UserStore.collection.where("ip", "==", user_ip)
        docs = list(query.stream())

        user = UserModel(docs[0].to_dict(), docs[0].reference)

        UserStore.user_data = user

    @staticmethod
    def find_user(user_ip: str) -> typing.Optional[UserModel]:
        query = UserStore.collection.where("ip", "==", user_ip)
        docs = list(query.stream())

        user = UserModel(docs[0].to_dict(), docs[0].reference)

        return user

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
                    print(" " * len(phrase), end="\r")
                    return
                elif UserStore.is_database_hold.is_set():
                    break

                print(
                    f"{CONSOLE_COLORS['ALERT']}{phrase}{CONSOLE_COLORS['RESET']}",
                    end="\r",
                )
                time.sleep(0.5)

            if not UserStore.is_database_hold.is_set():
                print(" " * len(phrases[-1]), end="\r")

    @staticmethod
    def __find_or_create_user(users: list, user_ip: str):
        Store.is_database_busy.set()

        if UserStore.__does_user_exist(user_ip):
            user_ref = UserStore.find_user(user_ip)
            user_data = user_ref.get().to_dict()
        else:
            UserStore.is_database_hold.set()

            user_data = UserStore.__prepare_new_user(user_ip)
            user_ref = UserStore.__create_user(user_data)

            UserStore.is_database_hold.clear()

        users.append(user_ref)
        users.append(user_data)

        Store.is_database_busy.clear()

    @staticmethod
    def __does_user_exist(user_ip: str) -> bool:
        query = UserStore.collection.where("ip", "==", user_ip)
        docs = query.stream()

        return len(docs) > 0

    @staticmethod
    def __prepare_new_user(user_ip: str) -> dict:
        name = input("Enter your username: ")
        return {"name": name, "ip": user_ip, "color": help_functions.try_user_color()}

    @staticmethod
    def __create_user(user_data: dict) -> firestore.DocumentReference:
        user_ref = UserStore.collection.add(user_data)

        return user_ref
