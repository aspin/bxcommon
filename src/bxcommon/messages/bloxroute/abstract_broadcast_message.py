import struct
from abc import ABC
from typing import Optional

from bxcommon import constants
from bxcommon.messages.bloxroute.abstract_bloxroute_message import AbstractBloxrouteMessage
from bxcommon.utils import crypto, uuid_pack
from bxcommon.utils.object_hash import Sha256Hash, ConcatHash


class AbstractBroadcastMessage(AbstractBloxrouteMessage, ABC):
    PAYLOAD_LENGTH = crypto.SHA256_HASH_LEN + constants.NETWORK_NUM_LEN + constants.NODE_ID_SIZE_IN_BYTES + \
                     constants.CONTROL_FLAGS_LEN
    SOURCE_ID_OFFSET = AbstractBloxrouteMessage.HEADER_LENGTH + crypto.SHA256_HASH_LEN + constants.NETWORK_NUM_LEN

    def __init__(self, message_hash: Optional[Sha256Hash] = None, network_num: Optional[int] = None,
                 source_id: Optional[str] = None, buf: Optional[bytearray] = None):
        self._message_hash = None
        self._network_num = None
        self._source_id = None
        self._message_id = None

        if buf is None:
            assert message_hash is not None and network_num is not None and source_id is not None
            self.buf = bytearray(self.HEADER_LENGTH + self.PAYLOAD_LENGTH)
        else:
            self.buf = buf

        payload_length = len(self.buf) - self.HEADER_LENGTH
        super().__init__(self.MESSAGE_TYPE, payload_length, self.buf)

        if buf is None:
            off = AbstractBloxrouteMessage.HEADER_LENGTH

            self.buf[off:off + crypto.SHA256_HASH_LEN] = message_hash.binary
            off += crypto.SHA256_HASH_LEN

            struct.pack_into("<L", self.buf, off, network_num)
            off += constants.NETWORK_NUM_LEN

            struct.pack_into("<16s", self.buf, off, uuid_pack.to_bytes(source_id))
            off += constants.NODE_ID_SIZE_IN_BYTES

    def set_message_hash(self, message_hash: Sha256Hash):
        assert self.buf is not None
        off = AbstractBloxrouteMessage.HEADER_LENGTH
        self.buf[off:off + crypto.SHA256_HASH_LEN] = message_hash.binary

    def message_hash(self) -> Sha256Hash:
        if self._message_hash is None:
            off = self.HEADER_LENGTH
            self._message_hash = Sha256Hash(self._memoryview[off:off + crypto.SHA256_HASH_LEN])

        return self._message_hash

    def message_id(self) -> ConcatHash:
        """
        Concatenated hash, includes network info with message hash.
        """
        if self._message_id is None:
            off = self.HEADER_LENGTH
            self._message_id = ConcatHash(
                self._memoryview[off:off + crypto.SHA256_HASH_LEN + constants.NETWORK_NUM_LEN],
                0
            )
        return self._message_id

    def network_num(self) -> int:
        if self._network_num is None:
            off = self.HEADER_LENGTH + crypto.SHA256_HASH_LEN
            self._network_num, = struct.unpack_from("<L", self.buf, off)

        assert self._network_num is not None
        return self._network_num

    def source_id(self) -> str:
        if self._source_id is None:
            off = self.SOURCE_ID_OFFSET
            self._source_id = uuid_pack.from_bytes(struct.unpack_from("<16s", self.buf, off)[0])
            if self._source_id is None:
                self._source_id = constants.EMPTY_SOURCE_ID.decode()

        return self._source_id

    def source_id_as_str(self) -> str:
        if self.source_id() == constants.EMPTY_SOURCE_ID.decode():
            return "None"
        else:
            return self.source_id()

    def set_source_id(self, source_id: str):
        self._source_id = source_id
        off = self.HEADER_LENGTH + crypto.SHA256_HASH_LEN + constants.NETWORK_NUM_LEN
        struct.pack_into("<16s", self.buf, off, uuid_pack.to_bytes(source_id))
