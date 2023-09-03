from dataclasses import asdict, dataclass


@dataclass
class Server:
    name: str
    ip: str
    isPassword: bool
    password: str
    isActive: bool

    def toMap(self):
        return asdict(self)
