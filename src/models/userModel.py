import dataclasses

from .baseModel import BaseModel


@dataclasses.dataclass
class UserModel(BaseModel):
    color: str
    ip: str
    name: str

    def __init__(self, data, reference):
        super().__init__(data, reference)
