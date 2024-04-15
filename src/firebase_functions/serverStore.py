import threading
import typing

from google.cloud import firestore

from models.serverModel import ServerModel

from .firebase_init import firestore_client
from .store import Store


class ServerStore(Store):
    collection = firestore_client.collection("servers")
    servers: list[ServerModel] = []

    @staticmethod
    def fetch_servers():
        t1 = threading.Thread(
            target=Store._loading, args=("Fetching servers, please wait",)
        )
        t2 = threading.Thread(target=ServerStore.__read_servers)

        t2.start()
        t1.start()

        t2.join()
        t1.join()

    @staticmethod
    def create_server(server_data: ServerModel) -> firestore.DocumentReference:
        server_ref = ServerStore.collection.add(server_data.to_map())

        return server_ref

    @staticmethod
    def is_server_in_database(server_ip: str) -> bool:
        for server in ServerStore.servers:
            if server["ip"] == server_ip:
                return True

        return False

    @staticmethod
    def is_server_name_unique(server_name: str) -> bool:
        for server in ServerStore.servers:
            if server["name"] == server_name:
                return False

        return True

    @staticmethod
    def find_server(
        server_name: str = None, server_ip: str = None
    ) -> typing.Optional[ServerModel]:
        if server_name:
            for server in ServerStore.servers:
                if server["name"] == server_name:
                    return server

        elif server_ip:
            for server in ServerStore.servers:
                if server["name"] == server_name:
                    return server

    @staticmethod
    def is_user_on_server(
        server: ServerModel, user_ref: firestore.DocumentReference
    ) -> bool:
        for user in server["users"]:
            if user.id == user_ref.id:
                return True

        return False

    @staticmethod
    def add_user_to_server(
        server_data: ServerModel,
        new_user_ref: firestore.DocumentReference,
    ):
        server_data.users.append(new_user_ref)
        server_data["reference"].update({"users": server_data["users"]})

    @staticmethod
    def create_server_name():
        try:
            server_name = input("Enter server's name:\n")
            while not ServerStore.is_server_name_unique(server_name):
                print("This name already exists. Server name has to be unique!")
                server_name = input("Enter server's name:\n")
        except KeyboardInterrupt:
            raise KeyboardInterrupt

        return server_name

    @staticmethod
    def open_server(server_ref: firestore.DocumentReference):
        server_ref.update({"isActive": True})

    @staticmethod
    def close_server(server_ref: firestore.DocumentReference):
        server_ref.update({"isActive": False})

    @staticmethod
    def __read_servers():
        Store.is_database_busy.set()

        docs = ServerStore.collection.stream()

        ServerStore.servers = []
        for doc in docs:
            ServerStore.servers.append(ServerModel(doc.to_dict(), doc.reference))

        Store.is_database_busy.clear()
