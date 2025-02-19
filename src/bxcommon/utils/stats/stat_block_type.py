from enum import Enum


class StatBlockType(Enum):
    ENCRYPTED = "encrypted"
    COMPRESSED = "compressed"

    def __str__(self):
        return self.value
