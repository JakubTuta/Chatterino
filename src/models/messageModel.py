import dataclasses

from google.cloud import firestore

from .baseModel import BaseModel


@dataclasses.dataclass
class MessageModel(BaseModel):
    id: str
    isServer: bool
    server: firestore.DocumentReference
    text: str
    time: str
    user: firestore.DocumentReference

    def __init__(self, data, reference):
        data["time"] = self.__map_timestamp(data["time"])
        super().__init__(data, reference)

    @staticmethod
    def __map_timestamp(date) -> str:
        return date.strftime("%d.%m.%y %H:%M")
