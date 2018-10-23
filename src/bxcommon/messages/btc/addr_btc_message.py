import struct

from bxcommon.constants import BTC_HDR_COMMON_OFF
from bxcommon.messages.btc.btc_message import BTCMessage
from bxcommon.messages.btc.btc_messages_util import ipaddrport_to_btcbytearray, pack_int_to_btcvarint


# the addr argument should be an array of (timestamp, ipaddr, port) triples
class AddrBTCMessage(BTCMessage):
    # FIXME addrs arg is sharing global state
    def __init__(self, magic=None, addrs=[], buf=None):
        if buf is None:
            buf = bytearray(BTC_HDR_COMMON_OFF + 9 + len(addrs) * (4 + 18))
            self.buf = buf

            off = BTC_HDR_COMMON_OFF
            off += pack_int_to_btcvarint(len(addrs), buf, off)

            for triplet in addrs:
                # pack the timestamp
                struct.pack_into('<L', buf, off, triplet[0])
                off += 4
                # pack the host ip and port pair
                buf[off:off + 18] = ipaddrport_to_btcbytearray(triplet[1], triplet[2])
                off += 18

            BTCMessage.__init__(self, magic, 'addr', off - BTC_HDR_COMMON_OFF, buf)
        else:
            self.buf = buf
            self._memoryview = memoryview(buf)
            self._magic = self._command = self._payload_len = self._checksum = None
            self._payload = None

    def __iter__(self):
        raise RuntimeError('FIXME')
        # FIXME buf is not defined, change to self.buf and test
        # off = BTC_HDR_COMMON_OFF
        # count, size = btcvarint_to_int(buf, off)
        # off += size
        #
        # for i in xrange(count):
        #     timestamp = struct.unpack_from('<L', self.buf, off)
        #     off += 4
        #     host, port = btcbytearray_to_ipaddrport(buf[off:off+18])
        #     off += 18
        #     yield (timestamp, host, port)
