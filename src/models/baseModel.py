import dataclasses

from google.cloud import firestore


@dataclasses.dataclass
class BaseModel:
    reference: firestore.DocumentReference = dataclasses.field(
        compare=False, hash=False, repr=False
    )

    def __init__(self, data, reference):
        for key, value in data.items():
            setattr(self, key, value)
        setattr(self, "reference", reference)

    def to_map(self):
        data = dataclasses.asdict(self)
        del data["reference"]

        return data
