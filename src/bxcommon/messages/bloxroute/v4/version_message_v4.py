from bxcommon import constants
from bxcommon.messages.bloxroute.v4.message_v4 import MessageV4
from bxcommon.utils.message_buffer_builder import PayloadElement, PayloadBlock


class VersionMessageV4(MessageV4):
    """
    Bloxroute message that contains version info.
    """

    BASE_LENGTH = constants.BX_HDR_COMMON_OFF + constants.VERSION_NUM_LEN + constants.NETWORK_NUM_LEN
    VERSION_MESSAGE_BLOCK = PayloadBlock(constants.BX_HDR_COMMON_OFF, "VersionMessage", 0,
                                         PayloadElement(structure="<L", name="protocol_version"),
                                         PayloadElement(structure="<L", name="network_num")
                                         )
    VERSION_MESSAGE_LENGTH = VERSION_MESSAGE_BLOCK.size

    def __init__(self, msg_type, payload_len, protocol_version, network_num, buf):
        if protocol_version is not None and network_num is not None:
            if len(buf) < self.BASE_LENGTH:
                raise ValueError("Version message is not long enough.")
            buf = self.VERSION_MESSAGE_BLOCK.build(buf, protocol_version=protocol_version, network_num=network_num)

        self._protocol_version = None
        self._network_num = None
        super(VersionMessageV4, self).__init__(msg_type, payload_len, buf)

    def __unpack(self):
        contents = self.VERSION_MESSAGE_BLOCK.read(self._memoryview)
        self._protocol_version = contents.get("protocol_version")
        self._network_num = contents.get("network_num")

    def protocol_version(self):
        if self._protocol_version is None:
            self.__unpack()
        return self._protocol_version

    def network_num(self):
        if self._network_num is None:
            self.__unpack()
        return self._network_num
