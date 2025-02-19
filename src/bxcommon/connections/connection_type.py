from enum import auto, IntFlag


# IntFlag allows comparison with ints, which is not as strict as Flag, but allows easier unit testing.
class ConnectionType(IntFlag):
    NONE = 0
    SDN = auto()
    BLOCKCHAIN_NODE = auto()
    REMOTE_BLOCKCHAIN_NODE = auto()
    GATEWAY = auto()
    RELAY_TRANSACTION = auto()
    RELAY_BLOCK = auto()
    RELAY_ALL = RELAY_TRANSACTION | RELAY_BLOCK
    CROSS_RELAY = auto()

    def __str__(self):
        return self.name

    def __format__(self, format_spec):
        return self.name
