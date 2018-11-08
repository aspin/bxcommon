import struct

from bxcommon.constants import BTC_HDR_COMMON_OFF, BTC_HEADER_MINUS_CHECKSUM, MSG_NULL_BYTE, btc_magic_numbers
from bxcommon.exceptions import ChecksumError, PayloadLenError
from bxcommon.messages.abstract_message import AbstractMessage
from bxcommon.utils import crypto, logger


class BTCMessage(AbstractMessage):
    HEADER_LENGTH = BTC_HDR_COMMON_OFF

    def __init__(self, magic=None, command=None, payload_len=None, buf=None):
        self.buf = buf
        self._memoryview = memoryview(buf)

        magic_num = magic if magic not in btc_magic_numbers else btc_magic_numbers[magic]
        checksum = crypto.bitcoin_hash(self._memoryview[BTC_HDR_COMMON_OFF:payload_len + BTC_HDR_COMMON_OFF])

        off = 0
        struct.pack_into('<L12sL', buf, off, magic_num, command, payload_len)
        off += 20
        buf[off:off + 4] = checksum[0:4]

        self._magic = magic_num
        self._command = command
        self._payload_len = payload_len
        self._payload = None
        self._checksum = None

    # TODO: pull this out in to a message protocol
    @classmethod
    def unpack(cls, buf):
        magic, command, payload_length = struct.unpack_from('<L12sL', buf)
        checksum = buf[BTC_HEADER_MINUS_CHECKSUM:cls.HEADER_LENGTH]
        return command.rstrip(MSG_NULL_BYTE), magic, checksum, payload_length

    @classmethod
    def validate_payload(cls, buf, unpacked_args):
        command, _magic, checksum, payload_length = unpacked_args
        if payload_length != len(buf) - cls.HEADER_LENGTH:
            error_message = "Payload length does not match buffer size: %d vs %d bytes" % (payload_length, len(buf))
            logger.error(error_message)
            raise PayloadLenError(error_message)

        if checksum != crypto.bitcoin_hash(buf[cls.HEADER_LENGTH:cls.HEADER_LENGTH + payload_length])[0:4]:
            error_message = "Checksum for packet doesn't match: %s" % (repr(buf))
            logger.error(error_message)
            raise ChecksumError(error_message, buf)

    @classmethod
    def initialize_class(cls, cls_type, buf, unpacked_args):
        command, magic, checksum, payload_length = unpacked_args
        instance = cls_type(buf=buf)
        instance._magic = magic
        instance._command = command
        instance._payload_len = payload_length
        instance._checksum = checksum
        return instance

    # END TODO

    def rawbytes(self):
        """
        Returns a memoryview of the message
        """
        if self._payload_len is None:
            self._payload_len = struct.unpack_from('<L', self.buf, 16)[0]

        if self._payload_len + BTC_HDR_COMMON_OFF == len(self.buf):
            return self._memoryview
        else:
            return self._memoryview[0:self._payload_len + BTC_HDR_COMMON_OFF]

    def magic(self):
        if self._magic is None:
            self._magic = struct.unpack_from('<L', self.buf)[0]
        return self._magic

    def command(self):
        if self._command is None:
            self._command = struct.unpack_from('<12s', self.buf, 4)[0]
        return self._command

    def payload_len(self):
        if self._payload_len is None:
            self._payload_len = struct.unpack_from('<L', self.buf, 16)[0]
        return self._payload_len

    def checksum(self):
        if self._checksum is None:
            self._checksum = self.buf[BTC_HEADER_MINUS_CHECKSUM:BTC_HDR_COMMON_OFF]
        return self._checksum

    def payload(self):
        if self._payload is None:
            self._payload = self.buf[BTC_HDR_COMMON_OFF:self.payload_len() + BTC_HDR_COMMON_OFF]
        return self._payload

    @staticmethod
    def get_header_from_partial_buf(buf):
        return struct.unpack_from('Q12s<I', buf, 0)
