import struct
from abc import ABCMeta

from bxcommon.utils import convert
from bxcommon.utils.crypto import SHA256_HASH_LEN

# Used to take the last few characters of the SHA256 encryption as the hash function.
# This is done because using the last characters of the SHA256 function provides major speed boosts.
PARTIAL_HASH_LENGTH = 4


class AbstractObjectHash:
    """
    Base class for representing hash as an object
    binary is a memoryview or a bytearray
    Assumes that binary does not mutate
    """
    __meta__ = ABCMeta

    def __init__(self, binary):
        self.binary = bytearray(binary) if isinstance(binary, memoryview) else binary

        self._hash = struct.unpack("<L", self.binary[-PARTIAL_HASH_LENGTH:])[0]

    def __hash__(self):
        return self._hash

    def __eq__(self, other):
        return other is not None and self.binary == other.binary

    def __lt__(self, other):
        return other is None or self.binary < other.binary

    def __getitem__(self, arg):
        return self.binary.__getitem__(arg)


class Sha256Hash(AbstractObjectHash):
    """
    Represents SHA256 hash as an object
    binary is a memoryview or a bytearray
    Assumes that binary does not mutate
    """

    def __init__(self, binary):
        if len(binary) != SHA256_HASH_LEN:
            raise ValueError("Binary has the wrong length.")

        super(Sha256Hash, self).__init__(binary)

    def __repr__(self):
        return "Sha256Hash<binary: {}>".format(convert.bytes_to_hex(self.binary))

    def __str__(self):
        return convert.bytes_to_hex(self.binary)


class ConcatHash(AbstractObjectHash):
    """
    Hash value that is concatenated with additional data.
    binary is a memoryview or a bytearray that is not mutable
    hashstart is the start of the random bytes that we take a hash with.
    """

    def __init__(self, binary, hashstart):
        super(ConcatHash, self).__init__(binary)

        self._hash = struct.unpack("<L", self.binary[hashstart:hashstart + PARTIAL_HASH_LENGTH])[0]

    def __repr__(self):
        return "ConcatHash<binary: {}>".format(convert.bytes_to_hex(self.binary))

    def __str__(self):
        return convert.bytes_to_hex(self.binary)


NULL_SHA256_HASH = Sha256Hash(binary=bytearray(SHA256_HASH_LEN))
