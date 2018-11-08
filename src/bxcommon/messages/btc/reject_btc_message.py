import struct

from bxcommon.constants import BTC_HDR_COMMON_OFF
from bxcommon.messages.btc.btc_message import BTCMessage
from bxcommon.messages.btc.btc_message_type import BtcMessageType


class RejectBTCMessage(BTCMessage):
    MESSAGE_TYPE = BtcMessageType.REJECT
    # ccodes
    REJECT_MALFORMED = 0x01
    REJECT_INVALID = 0x10
    REJECT_OBSOLETE = 0x11
    REJECT_DUPLICATE = 0x12
    REJECT_NONSTANDARD = 0x40
    REJECT_DUST = 0x41
    REJECT_INSUFFICIENTFEE = 0x42
    REJECT_CHECKPOINT = 0x43

    def __init__(self, magic=None, message=None, ccode=None, reason=None, b_data=None, buf=None):
        if buf is None:
            buf = bytearray(BTC_HDR_COMMON_OFF + 9 + len(message) + 1 + 9 + len(reason) + len(b_data))
            self.buf = buf

            off = BTC_HDR_COMMON_OFF
            struct.pack_into('<%dpB' % (len(message) + 1,), buf, off, message, ccode)
            off += len(message) + 1 + 1
            struct.pack_into('<%dp' % (len(reason) + 1,), buf, off, reason)
            off += len(reason) + 1
            buf[off:off + len(b_data)] = b_data
            off += len(b_data)

            BTCMessage.__init__(self, magic, self.MESSAGE_TYPE, off - BTC_HDR_COMMON_OFF, buf)
        else:
            self.buf = buf
            self._memoryview = memoryview(buf)
            self._magic = self._command = self._payload_len = self._checksum = None
            self._payload = None

        self._message = self._ccode = self._reason = self._data = None

    def message(self):
        if self._message is None:
            off = BTC_HDR_COMMON_OFF
            self._message = struct.unpack_from('%dp' % (len(self.buf) - off,), self.buf, off)[0]
            off += len(self._message) + 1
            self._ccode = struct.unpack_from('B', self.buf, off)[0]
            off += 1
            self._reason = struct.unpack_from('%dp' % (len(self.buf) - off,), self.buf, off)[0]
            off += len(self._reason) + 1
            self._data = self.buf[off:]
        return self._message

    def ccode(self):
        if self._message is None:
            self.message()
        return self._ccode

    def reason(self):
        if self._message is None:
            self.message()
        return self._reason

    def data(self):
        if self._message is None:
            self.message()
        return self._data
