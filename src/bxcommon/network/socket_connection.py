import errno
import socket

from bxcommon import constants
from bxcommon.network.socket_connection_state import SocketConnectionState
from bxcommon.utils import convert
from bxutils import logging

logger = logging.get_logger(__name__)


class SocketConnection:
    def __init__(self, socket_instance, node, is_server=False):
        if not isinstance(socket_instance, socket.socket):
            raise ValueError("socket_instance is expected to be of type socket but was {0}"
                             .format(type(socket.socket)))

        self.socket_instance = socket_instance
        self.is_server = is_server
        self._node = node

        self.state = SocketConnectionState.CONNECTING

        self._receive_buf = bytearray(constants.RECV_BUFSIZE)
        self.can_send = False

    def set_state(self, state: SocketConnectionState):
        self.state |= state

    def mark_for_close(self):
        self.set_state(SocketConnectionState.MARK_FOR_CLOSE)

    def receive(self):

        fileno = self.fileno()

        logger.trace("Collecting input from fileno {0}.", fileno)
        collect_input = True

        while collect_input and not self.state & SocketConnectionState.MARK_FOR_CLOSE:
            # Read from the socket and store it into the receive buffer.
            try:
                bytes_read = self.socket_instance.recv_into(self._receive_buf, constants.RECV_BUFSIZE)
            except socket.error as e:
                if e.errno in [errno.EAGAIN, errno.EWOULDBLOCK]:
                    logger.trace("Received errno {0} with message: '{1}' on connection {2}. Stop collecting input.",
                                 e.errno, e.strerror, fileno)
                    break
                elif e.errno in [errno.EINTR]:
                    # we were interrupted, try again
                    logger.trace("Received errno {0} with message '{1}', receive on {2} failed. Continuing recv.",
                                 e.errno, e.strerror, fileno)
                    continue
                elif e.errno in [errno.ECONNREFUSED]:
                    # Fatal errors for the connections
                    logger.trace("Received errno {0} with message '{1}', receive on {2} failed. "
                                 "Closing connection and retrying...",
                                 e.errno, e.strerror, fileno)
                    self._node.enqueue_disconnect(self)
                    return
                elif e.errno in [errno.ECONNRESET, errno.ETIMEDOUT, errno.EBADF]:
                    # Perform orderly shutdown
                    self._node.enqueue_disconnect(self)
                    return
                elif e.errno in [errno.EFAULT, errno.EINVAL, errno.ENOTCONN, errno.ENOMEM]:
                    # Should never happen errors
                    logger.error("Received errno {0} with msg {1}, receive on {2} failed. This should never happen.",
                                 e.errno, e.strerror, fileno)
                    return
                else:
                    raise e

            piece = self._receive_buf[:bytes_read]
            logger.trace("Got {0} bytes from fileno {1}: {2}",
                         bytes_read, fileno, convert.bytes_to_hex(piece))

            if bytes_read == 0:
                logger.info("Received close from fileno: {}. Closing connection.", self.fileno())
                self._node.enqueue_disconnect(self)
                return
            else:
                self._node.on_bytes_received(fileno, piece)

        self._node.on_finished_receiving(fileno)

    def send(self):
        if self.state & SocketConnectionState.MARK_FOR_CLOSE:
            return 0

        if not self.can_send:
            return 0

        fileno = self.fileno()

        total_bytes_written = 0
        bytes_written = 0

        # Send on the socket until either the socket is full or we have nothing else to send.
        while self.can_send and not self.state & SocketConnectionState.MARK_FOR_CLOSE:
            try:
                send_buffer = self._node.get_bytes_to_send(fileno)

                if not send_buffer:
                    break

                bytes_written = self.socket_instance.send(send_buffer)
                logger.trace("Sent {0} bytes on fileno {1}", bytes_written, fileno)
            except socket.error as e:
                if e.errno in [errno.EAGAIN, errno.EWOULDBLOCK, errno.ENOBUFS]:
                    logger.trace("Got {0}. Fileno {1} has a full socket. Marking as not sendable.", e.strerror, fileno)
                    self.can_send = False
                elif e.errno in [errno.EINTR]:
                    logger.trace("Got {0}. Send to {1} failed, trying again...", e.strerror, fileno)
                    continue
                elif e.errno in [errno.EACCES, errno.ECONNRESET, errno.EPIPE, errno.EHOSTUNREACH,
                                 errno.ECONNRESET, errno.ETIMEDOUT, errno.EBADF, errno.ECONNREFUSED]:
                    logger.trace("Got {0}, send to {1} failed, closing connection.", e.strerror, fileno)
                    self._node.enqueue_disconnect(self)
                    return 0
                elif e.errno in [errno.EDESTADDRREQ, errno.EFAULT, errno.EINVAL,
                                 errno.EISCONN, errno.EMSGSIZE, errno.ENOTCONN, errno.ENOTSOCK]:
                    logger.fatal("Fatal socket error {} on fileno {}: {}. Shutting down.",
                                 e.errno, fileno, e.strerror)
                    exit(1)
                elif e.errno in [errno.ENOMEM]:
                    # Fatal errors for the node
                    logger.fatal("Fatal socket error ENOMEM on fileno {}: {}. Shutting down.", fileno, e.strerror)
                    exit(1)
                else:
                    raise e

            total_bytes_written += bytes_written
            self._node.on_bytes_sent(fileno, bytes_written)

            bytes_written = 0

        return total_bytes_written

    def fileno(self):
        return self.socket_instance.fileno()

    def close(self, force_destroy: bool = False):
        if not force_destroy and not self.state & SocketConnectionState.MARK_FOR_CLOSE:
            raise ValueError("Attempted to close socket that was not MARK_FOR_CLOSE.")
        try:
            self.socket_instance.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        self.socket_instance.close()
        self._receive_buf = None
