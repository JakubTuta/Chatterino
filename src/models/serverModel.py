import dataclasses

from .baseModel import BaseModel


@dataclasses.dataclass
class ServerModel(BaseModel):
    name: str
    ip: str
    isPassword: bool
    password: str
    isActive: bool

    def __init__(self, data, reference):
        super().__init__(data, reference)
