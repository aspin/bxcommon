import struct
from abc import ABCMeta

from bxutils import logging

from bxcommon import constants
from bxcommon.constants import VERSION_NUM_LEN
from bxcommon.messages.bloxroute.v4.version_message_v4 import VersionMessageV4
from bxcommon.messages.bloxroute.version_message import VersionMessage
from bxcommon.utils.buffers.input_buffer import InputBuffer

logger = logging.get_logger(__name__)


class AbstractVersionManager:
    __metaclass__ = ABCMeta

    CURRENT_PROTOCOL_VERSION = 1
    MIN_SUPPORTED_PROTOCOL_VERSION = 1
    VERSION_MESSAGE_MAIN_LENGTH = VersionMessage.BASE_LENGTH

    def __init__(self):
        self.protocol_to_factory_mapping = {}
        self.protocol_to_converter_factory_mapping = {}
        self.version_message_command = ""

    def is_protocol_supported(self, protocol_version):
        return protocol_version >= self.MIN_SUPPORTED_PROTOCOL_VERSION

    def get_message_factory_for_version(self, protocol_version):
        """
        Returns message factory for provided protocol version

        :param protocol_version: protocol version
        :return: message factory
        """
        if not self.is_protocol_supported(protocol_version):
            raise ValueError("Protocol of version {} is not supported.".format(protocol_version))
        if protocol_version not in self.protocol_to_factory_mapping:
            logger.error("Got a message of type {}. Should be supported, but not in factory mapping.", protocol_version)
            raise NotImplementedError()

        return self.protocol_to_factory_mapping[protocol_version]

    def convert_message_to_older_version(self, convert_to_version, msg):
        """
        Converts message from current version to provided version

        :param convert_to_version: version to convert to
        :param msg: message
        :return: converted message
        """
        if not convert_to_version:
            raise ValueError("convert_to_version is required")

        if not msg:
            raise ValueError("msg is required")

        if convert_to_version not in self.protocol_to_converter_factory_mapping:
            raise ValueError("Conversion for version {} is not supported".format(convert_to_version))

        msg_converter = self._get_message_converter(convert_to_version, msg.msg_type())
        return msg_converter.convert_to_older_version(msg)

    def convert_message_from_older_version(self, convert_from_version, msg):
        """
        Converts message from older version to current version

        :param convert_from_version: version to convert from
        :param msg: message
        :return: converted message
        """
        if not convert_from_version:
            raise ValueError("convert_to_version is required")

        if not msg:
            raise ValueError("msg is required")

        if convert_from_version not in self.protocol_to_converter_factory_mapping:
            raise ValueError("Conversion for version {} is not supported".format(convert_from_version))

        msg_converter = self._get_message_converter(convert_from_version, msg.msg_type())
        return msg_converter.convert_from_older_version(msg)

    def convert_message_first_bytes_to_older_version(self, convert_to_version, msg_type, first_message_bytes):
        """
        Converts first message bytes from current version to provided version

        :param convert_to_version: version to convert to
        :param msg_type: message type
        :param first_message_bytes: message bytes
        :return: converted message bytes
        """

        if not convert_to_version:
            raise ValueError("convert_to_version is required")

        if not msg_type:
            raise ValueError("msg_type is required")

        if not first_message_bytes:
            raise ValueError("first_message_bytes is required")

        msg_converter = self._get_message_converter(convert_to_version, msg_type)

        return msg_converter.convert_first_bytes_to_older_version(first_message_bytes)

    def convert_message_first_bytes_from_older_version(self, convert_from_version, msg_type, first_message_bytes):
        """
        Converts first message bytes from older version to current version

        :param convert_from_version: version to convert from
        :param msg_type: message type
        :param first_message_bytes: message bytes
        :return: converted message bytes
        """

        if not convert_from_version:
            raise ValueError("convert_from_version is required")

        if not msg_type:
            raise ValueError("msg_type is required")

        if not first_message_bytes:
            raise ValueError("first_message_bytes is required")

        msg_converter = self._get_message_converter(convert_from_version, msg_type)

        return msg_converter.convert_first_bytes_from_older_version(first_message_bytes)

    def convert_message_last_bytes_to_older_version(self, convert_to_version, msg_type, message_last_bytes):
        """
        Converts message last bytes from current version to provided version

        :param convert_to_version: version to convert to
        :param msg_type: message type
        :param message_last_bytes: message bytes
        :return: converted message bytes
        """

        if not convert_to_version:
            raise ValueError("convert_to_version is required")

        if not msg_type:
            raise ValueError("msg_type is required")

        if not message_last_bytes:
            raise ValueError("first_message_bytes is required")

        msg_converter = self._get_message_converter(convert_to_version, msg_type)

        return msg_converter.convert_last_bytes_to_older_version(message_last_bytes)

    def convert_message_last_bytes_from_older_version(self, convert_from_version, msg_type, message_last_bytes):
        """
        Converts first message bytes from older version to current version

        :param convert_from_version: version to convert from
        :param msg_type: message type
        :param message_last_bytes: message bytes
        :return: converted message bytes
        """

        if not convert_from_version:
            raise ValueError("convert_from_version is required")

        if not msg_type:
            raise ValueError("msg_type is required")

        if not message_last_bytes:
            raise ValueError("first_message_bytes is required")

        msg_converter = self._get_message_converter(convert_from_version, msg_type)

        return msg_converter.convert_last_bytes_from_older_version(message_last_bytes)

    def get_message_size_change_to_older_version(self, convert_to_version, msg_type):
        """
        Returns the difference in size between current protocol version and older version

        :param convert_to_version: version to convert to
        :param msg_type: message type
        :return: size difference
        """

        if not convert_to_version:
            raise ValueError("convert_to_version is required")

        if not msg_type:
            raise ValueError("msg_type is required")

        msg_converter = self._get_message_converter(convert_to_version, msg_type)
        return msg_converter.get_message_size_change_to_older_version()

    def get_message_size_change_from_older_version(self, convert_from_version, msg_type):
        """
        Returns the difference in size between older version and current protocol version

        :param convert_from_version: version to convert from
        :param msg_type: message type
        :return: size difference
        """

        if not convert_from_version:
            raise ValueError("convert_to_version is required")

        if not msg_type:
            raise ValueError("msg_type is required")

        msg_converter = self._get_message_converter(convert_from_version, msg_type)

        return msg_converter.get_message_size_change_from_older_version()

    def get_connection_protocol_version(self, input_buffer):
        if not isinstance(input_buffer, InputBuffer):
            raise TypeError("Argument input_buffer expected to have type InputBuffer but was {}"
                            .format(type(input_buffer)))

        if input_buffer.length < constants.STARTING_SEQUENCE_BYTES_LEN + constants.BX_HDR_COMMON_OFF + constants.VERSION_NUM_LEN:
            return None

        header_buf = input_buffer.peek_message(VersionMessage.HEADER_LENGTH)

        if header_buf[:constants.STARTING_SEQUENCE_BYTES_LEN] == constants.STARTING_SEQUENCE_BYTES:
            command, payload_len = VersionMessage.unpack(header_buf)
            header_len = VersionMessage.HEADER_LENGTH
        else:
            command, payload_len = VersionMessageV4.unpack(header_buf)
            header_len = VersionMessageV4.HEADER_LENGTH

        if command != self.version_message_command:
            logger.debug("Received a nonversion hello message of type {}. Ignoring and closing connection.", command)
            return self.MIN_SUPPORTED_PROTOCOL_VERSION - 1

        if payload_len < self.VERSION_MESSAGE_MAIN_LENGTH:
            return 1

        version_buf = input_buffer.get_slice(header_len, header_len + VERSION_NUM_LEN)
        version, = struct.unpack_from("<L", version_buf, 0)
        return version

    def _get_message_converter(self, version, msg_type):
        msg_converter_factory = self.protocol_to_converter_factory_mapping[version]
        return msg_converter_factory.get_message_converter(msg_type)
