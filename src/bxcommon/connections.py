import errno
import hashlib
import select
import signal
import socket
from collections import defaultdict

from bxcommon.messages import PongMessage, AckMessage, Message, HDR_COMMON_OFF
from bxcommon.utils import *
from exceptions import *

MAX_CONN_BY_IP = 30  # Maximum number of connections that an IP address can have

CONNECTION_TIMEOUT = 30  # Number of seconds that we wait to retry a connection.
FAST_RETRY = 3  # Seconds before we retry in case of transient failure (e.g. EINTR thrown)
MAX_RETRIES = 10

# Number of bad messages I'm willing to receive in a row before declaring the input stream
# corrupt beyond repair.
MAX_BAD_MESSAGES = 3

# The size of the recv buffer that we fill each time.
RECV_BUFSIZE = 8192

RETRY_INTERVAL = 30  # Seconds before we retry in case of orderly shutdown

sha256 = hashlib.sha256

MAX_WAIT_TIME = 60  # Seconds timeout for the sink

# Number of messages that can be cut through at a time
MAX_SEND_QUEUE_SIZE = 5000

# Number of messages that can be kept in the history at a time.
# Two identical messages that are broadcast more than MAX_MESSAGE_HISTORY messages apart
# will both be cut through broadcast.
MAX_MESSAGE_HISTORY = 5000


class AbstractClient(object):
    def __init__(self, server_ip, server_port):
        self.server_ip = server_ip
        self.server_port = server_port
        self.epoll = select.epoll()
        self.connection_pool = ConnectionPool()
        self.send_pings = False

        self.num_retries_by_ip = defaultdict(lambda: 0)

        # set up the server sockets for bitcoind and www/json
        self.serversocket = self.listen_on_address('0.0.0.0',
                                                   self.server_port)
        self.serversocketfd = self.serversocket.fileno()
        # Handle termination gracefully
        signal.signal(signal.SIGTERM, self.kill_node)
        signal.signal(signal.SIGINT, self.kill_node)

        # Event handling queue for delayed events
        self.alarm_queue = AlarmQueue()

        self.tx_manager = TransactionManager(self)

    # Create and initialize a nonblocking server socket with at most 50 connections in its backlog,
    #   bound to an interface and port
    # Exit the program if there's an unrecoverable socket error (e.g. no more kernel memory)
    # Reraise the exception if it's unexpected.
    def listen_on_address(self, ip, serverport):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        log_debug("Creating a server socket on {0}:{1}".format(ip, serverport))

        try:
            s.bind((ip, serverport))
            s.listen(50)
            s.setblocking(0)
            self.epoll.register(s.fileno(), select.EPOLLIN | select.EPOLLET)
            log_debug("Finished creating a server socket on {0}:{1}".format(ip, serverport))
            return s

        except socket.error as e:
            if e.errno in [errno.EACCES, errno.EADDRINUSE, errno.EADDRNOTAVAIL, errno.ENOMEM, errno.EOPNOTSUPP]:
                log_crash("Fatal error: " + str(e.errno) + " " + e.strerror +
                          " Occurred while setting up serversocket on {0}:{1}. Exiting...".format(ip, serverport))
                exit(1)
            else:
                log_crash("Fatal error: " + str(e.errno) + " " + e.strerror +
                          " Occurred while setting up serversocket on {0}:{1}. Reraising".format(ip, serverport))
                raise e

    # Make a new conn_cls instance who is connected to (ip, port) and schedule connection_timeout to check its status.
    # If setup is False, then sock is an already established socket. Otherwise, we must initialize and set up socket.
    # If trusted is True, the instance should be marked as a trusted connection.
    def connect_to_address(self, conn_cls, ip, port, sock=None, setup=False):
        log_debug("Initiating connection to {0}:{1}.".format(ip, port))

        # If we're already connected to the remote peer, log the event and ignore it.
        if self.connection_pool.has_connection(ip, port):
            log_err("Connection to {0}:{1} already exists!".format(ip, port))
            if sock is not None:
                try:
                    sock.close()
                except socket.error:
                    pass

            return

        initialized = True  # True if socket is connected. False otherwise.

        # Create a socket and connect to (ip, port).
        if setup:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
                sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                sock.setblocking(0)
                sock.connect((ip, port))
            except socket.error as e:
                if e.errno in [errno.EPERM, errno.EADDRINUSE]:
                    log_err("Connection to {0}:{1} failed! Got errno {2} with msg {3}."
                            .format(ip, port, e.errno, e.strerror))
                    return
                elif e.errno in [errno.EAGAIN, errno.ECONNREFUSED, errno.EINTR, errno.EISCONN, errno.ENETUNREACH,
                                 errno.ETIMEDOUT]:
                    raise RuntimeError('FIXME')

                    # FIXME conn_obj and trusted are not defined, delete trust, alarm register call and test
                    # log_err("Node.connect_to_address",
                    #         "Connection to {0}:{1} failed. Got errno {2} with msg {3}. Retry?: {4}"
                    #         .format(ip, port, e.errno, e.strerror, conn_obj.trusted))
                    # if trusted:
                    #     self.alarm_queue.register_alarm(FAST_RETRY, self.retry_init_client_socket, sock, conn_cls, ip,
                    #                                     port, setup)
                    # return
                elif e.errno in [errno.EALREADY]:
                    # Can never happen because this thread is the only one using the socket.
                    log_err("Got EALREADY while connecting to {0}:{1}.".format(ip, port))
                    exit(1)
                elif e.errno in [errno.EINPROGRESS]:
                    log_debug("Got EINPROGRESS on {0}:{1}. Will wait for ready outputbuf.".format(ip, port))
                    initialized = False
                else:
                    raise e
        else:
            # Even if we didn't set up this socket, we still need to make it nonblocking.
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            sock.setblocking(0)

        # Make a connection object and set its state
        conn_obj = conn_cls(sock, (ip, port), self, setup=setup, from_me=setup)
        conn_obj.state |= ConnectionState.CONNECTING if initialized else ConnectionState.INITIALIZED

        self.alarm_queue.register_alarm(CONNECTION_TIMEOUT, self.connection_timeout, conn_obj)

        # Make the connection object publicly accessible
        self.connection_pool.add(sock.fileno(), ip, port, conn_obj)
        self.epoll.register(sock.fileno(),
                            select.EPOLLOUT | select.EPOLLIN | select.EPOLLERR | select.EPOLLHUP | select.EPOLLET)

        log_debug("Connected {0}:{1} on file descriptor {2} with state {3}"
                  .format(ip, port, sock.fileno(), conn_obj.state))
        return

    # Handles incoming connections on the server socket
    # Only allows MAX_CONN_BY_IP connections from each IP address to be initialized.
    def handle_serversocket_connections(self):
        log_verbose("new connection establishment starting")
        try:
            while True:
                new_socket, address = self.serversocket.accept()
                log_debug("new connection from {0}".format(address))
                ip = address[0]

                # If we have too many connections, then we close this new socket and move on.
                if self.connection_pool.get_num_conn_by_ip(ip) >= MAX_CONN_BY_IP:
                    log_err("The IP {0} has too many connections! Closing...".format(ip))
                    new_socket.close()
                else:
                    log_debug("Establishing connection number {0} from {1}"
                              .format(self.connection_pool.get_num_conn_by_ip(ip), ip))
                    # The trusted bit here will be set when we get the application layer address.
                    conn_cls = self.get_connection_class(ip)
                    self.connect_to_address(conn_cls, address[0], address[1], new_socket, setup=False)

        except socket.error:
            pass

    # Cleans up system resources used by this node.
    def cleanup_node(self):
        log_err("Node is closing! Closing everything.")

        # Clean up server sockets.
        self.epoll.unregister(self.serversocket.fileno())
        self.serversocket.close()

        # Clean up client sockets.
        for conn in self.connection_pool:
            self.destroy_conn(conn.fileno, teardown=True)

        self.epoll.close()

    # Kills the node immediately
    def kill_node(self, _signum, _stack):
        raise TerminationError("Node killed.")

    # Clean up the associated connection and update all data structures tracking it.
    # We also retry trusted connections since they can never be destroyed.
    # If teardown is True, then we do not retry trusted connections and just tear everything down.
    def destroy_conn(self, fileno, teardown=False):
        conn = self.connection_pool.get_byfileno(fileno)
        log_debug("Breaking connection to {0}".format(conn.peer_desc))

        # Get rid of the connection from the epoll and the connection pool.
        self.epoll.unregister(fileno)
        self.connection_pool.delete(conn)

        conn.close()

        if self.can_retry_after_destroy(teardown, conn):
            log_debug("Retrying connection to {0}".format(conn.peer_desc))
            self.alarm_queue.register_alarm(
                FAST_RETRY, self.retry_init_client_socket, None,
                conn.__class__, conn.peer_ip, conn.peer_port, True)

    # Check if the connection is established.
    # If it is not established, we give up for untrusted connections and try again for trusted connections.
    def connection_timeout(self, conn):
        log_debug("Connection timeout, on connection with {0}".format(conn.peer_desc))

        if conn.state & ConnectionState.ESTABLISHED:
            log_debug("Turns out connection was initialized, carrying on with {0}".format(conn.peer_desc))
            self.alarm_queue.register_alarm(60, conn.send_ping)
            return 0

        if conn.state & ConnectionState.MARK_FOR_CLOSE:
            log_debug("We're already closing the connection to {0} (or have closed it). Ignoring timeout."
                      .format(conn.peer_desc))
            return 0

        # Clean up the old connection and retry it if it is trusted
        log_debug("destroying old socket with {0}".format(conn.peer_desc))
        self.destroy_conn(conn.sock.fileno())

        # It is connect_to_address's job to schedule this function.
        return 0

    # Retrys the connect_to_address call
    # Returns 0 to be allowed as a function for the AlarmQueue and not be rescheduled
    def retry_init_client_socket(self, sock, conn_cls, ip, port, setup):
        self.num_retries_by_ip[ip] += 1
        if self.num_retries_by_ip[ip] >= MAX_RETRIES:
            del self.num_retries_by_ip[ip]
            log_debug("Not retrying connection to {0}:{1}- maximum connections exceeded!".format(ip, port))
            return 0
        else:
            log_debug("Retrying connection to {0}:{1}.".format(ip, port))
            self.connect_to_address(conn_cls, ip, port, sock, setup)
        return 0

    # Main loop of this Node. Returns when Node crashes or is stopped.
    # Handles events as they get triggered by epoll.
    # Fires alarms that get scheduled.
    def run(self):
        self.connect_to_peers()

        try:
            _, timeout = self.alarm_queue.time_to_next_alarm()
            while True:
                # Grab all events.
                try:
                    events = self.epoll.poll(timeout)
                except IOError as ioe:
                    if ioe.errno == errno.EINTR:
                        log_verbose("got interrupted in epoll")
                        continue
                    raise ioe

                for fileno, event in events:
                    conn = self.connection_pool.get_byfileno(fileno)

                    if conn is not None:
                        # Mark this connection for close if we received a POLLHUP. No other functions will be called
                        #   on this connection.
                        if event & select.EPOLLHUP:
                            conn.state |= ConnectionState.MARK_FOR_CLOSE

                        if event & select.EPOLLOUT and not conn.state & ConnectionState.MARK_FOR_CLOSE:
                            # If connect received EINPROGRESS, we will receive an EPOLLOUT if connect succeeded
                            if not conn.state & ConnectionState.INITIALIZED:
                                conn.state = conn.state | ConnectionState.INITIALIZED

                            # Mark the connection as sendable and send as much as we can from the outputbuffer.
                            conn.mark_sendable()
                            conn.send()

                    # handle incoming connection on the server port
                    elif fileno == self.serversocketfd:
                        self.handle_serversocket_connections()

                    else:
                        assert False, "Connection not handled!"

                # Handle EPOLLIN events.
                for fileno, event in events:
                    # we already handled the new connections above, no need to handle them again
                    if fileno != self.serversocketfd:
                        conn = self.connection_pool.get_byfileno(fileno)

                        if event & select.EPOLLIN and not conn.state & ConnectionState.MARK_FOR_CLOSE:
                            # log_debug("Node.run", "recv event on {0}".format(conn.peer_desc))
                            conn.recv()

                        # Done processing. Close socket if it got put on the blacklist or was marked for close.
                        if conn.state & ConnectionState.MARK_FOR_CLOSE:
                            log_debug("Connection to {0} closing".format(conn.peer_desc))
                            self.destroy_conn(fileno)
                            if conn.is_persistent:
                                self.alarm_queue.register_alarm(RETRY_INTERVAL, self.retry_init_client_socket, None,
                                                                conn.__class__, conn.peer_ip, conn.peer_port, True)

                timeout = self.alarm_queue.fire_ready_alarms(not events)

        # Handle shutdown of this node.
        finally:
            self.cleanup_node()

    def can_retry_after_destroy(self, teardown, conn):
        raise NotImplementedError()

    def get_connection_class(self, ip=None):
        raise NotImplementedError()

    def connect_to_peers(self):
        raise NotImplementedError()


# A group of connections with active sockets
class ConnectionPool(object):
    INITIAL_FILENO = 5000

    def __init__(self):
        self.byfileno = [None] * ConnectionPool.INITIAL_FILENO
        self.len_fileno = ConnectionPool.INITIAL_FILENO

        self.byipport = {}
        self.count_conn_by_ip = defaultdict(lambda: 0)
        self.num_peer_conn = 0

    # Add a connection for tracking.
    # Throws an AssertionError if there already exists a connection to the same
    # (ip, port) pair.
    def add(self, fileno, ip, port, conn):
        assert (ip, port) not in self.byipport

        while fileno > self.len_fileno:
            self.byfileno.extend([None] * ConnectionPool.INITIAL_FILENO)
            self.len_fileno += ConnectionPool.INITIAL_FILENO

        self.byfileno[fileno] = conn
        self.byipport[(ip, port)] = conn
        self.count_conn_by_ip[ip] += 1

    # Checks whether we have a connection to (ip, port) or not
    def has_connection(self, ip, port):
        return (ip, port) in self.byipport

    # Gets the connection by (ip, port).
    # Throws a KeyError if no such connection exists
    def get_byipport(self, ip, port):
        return self.byipport[(ip, port)]

    # Gets the connection by fileno.
    # Returns None if the fileno does not exist.
    def get_byfileno(self, fileno):
        if fileno > self.len_fileno:
            return None

        return self.byfileno[fileno]

    # Get the number of connections to this ip address.
    def get_num_conn_by_ip(self, ip):
        if ip in self.count_conn_by_ip:
            return self.count_conn_by_ip[ip]
        return 0

    # Delete this connection from the connection pool
    def delete(self, conn):
        # Remove conn from the dictionaries
        self.byfileno[conn.fileno] = None
        del self.byipport[(conn.peer_ip, conn.peer_port)]

        # Decrement the count- if it's 0, we delete the key.
        if self.count_conn_by_ip[conn.peer_ip] == 1:
            del self.count_conn_by_ip[conn.peer_ip]
        else:
            self.count_conn_by_ip[conn.peer_ip] -= 1

    # Delete this connection given its fileno.
    def delete_byfileno(self, fileno):
        return self.delete(self.byfileno[fileno])

    # Iterates through all connection objects in this connection pool
    def __iter__(self):
        for conn in self.byfileno:
            if conn is not None:
                yield conn

    # Returns the number of connections in our pool
    def __len__(self):
        return len(self.byipport)


class AbstractConnection(object):
    def __init__(self, sock, address, node, from_me=False, setup=False):
        self.sock = sock
        self.fileno = sock.fileno()

        # (IP, Port) at time of socket creation. We may get a new application level port in
        # the version message if the connection is not from me.
        self.peer_ip, self.peer_port = address
        self.my_ip = node.server_ip
        self.my_port = node.server_port

        self.from_me = from_me  # Whether or not I initiated the connection
        self.setup = setup  # Whether or not I set up this connection

        self.outputbuf = OutputBuffer()
        self.inputbuf = InputBuffer()
        self.node = node

        self.is_persistent = False
        self.sendable = False  # Whether or not I can send more bytes on this socket.
        self.state = ConnectionState.CONNECTING

        # Temporary buffers to receive the contents of the recv call.
        self.recv_buf = bytearray(RECV_BUFSIZE)

        # Number of bad messages I've received in a row.
        self.num_bad_messages = 0

        self.peer_desc = "%s %d" % (self.peer_ip, self.peer_port)

    # Marks a connection as 'sendable', that is, there is room in the outgoing send buffer, and a send call can succeed.
    # Only gets unmarked when the outgoing send buffer is full.
    def mark_sendable(self):
        self.sendable = True

    def can_send_queued(self):
        return self.sendable

    def pre_process_msg(self, msg_cls):
        is_full_msg, msg_type, payload_len = msg_cls.peek_message(self.inputbuf)

        log_debug("XXX: Starting to get message of type {0}. Is full: {1}".format(msg_type, is_full_msg))

        return is_full_msg, msg_type, payload_len

        # Enqueues the contents of a Message instance, msg, to our outputbuf and attempts to send it if the underlying
        #   socket has room in the send buffer.

    def enqueue_msg(self, msg):
        if self.state & ConnectionState.MARK_FOR_CLOSE:
            return

        self.outputbuf.enqueue_msgbytes(msg.rawbytes())

        if self.can_send_queued():
            self.send()

        # Enqueues the raw bytes of a message, msg_bytes, to our outputbuf and attempts to send it if the underlying socket
        #   has room in the send buffer.

    def enqueue_msg_bytes(self, msg_bytes):
        if self.state & ConnectionState.MARK_FOR_CLOSE:
            return

        size = len(msg_bytes)

        log_debug("Adding message of length {0} to {1}'s outputbuf".format(size, self.peer_desc))

        self.outputbuf.enqueue_msgbytes(msg_bytes)

        if self.can_send_queued():
            self.send()

    def send(self):
        raise NotImplementedError()

    # Receives and processes the next bytes on the socket's inputbuffer.
    # Returns 0 in order to avoid being rescheduled if this was an alarm.
    def recv(self, msg_cls=Message, hello_msgs=['hello', 'ack']):
        self.collect_input()

        while True:
            if self.state & ConnectionState.MARK_FOR_CLOSE:
                return 0

            is_full_msg, msg_type, payload_len = self.pre_process_msg(msg_cls)

            if not is_full_msg:
                break

            # Full messages must be a version or verack if the connection isn't established yet.
            msg = self.pop_next_message(payload_len)
            # If there was some error in parsing this message, then continue the loop.
            if msg is None:
                if self.num_bad_messages == MAX_BAD_MESSAGES:
                    log_debug("Got enough bad messages! Marking connection from {0} closed".format(self.peer_desc))
                    self.state |= ConnectionState.MARK_FOR_CLOSE
                    return 0  # I have MAX_BAD_MESSAGES messages that failed to parse in a row.

                self.num_bad_messages += 1
                continue

            self.num_bad_messages = 0

            if not (self.state & ConnectionState.ESTABLISHED) and msg_type not in hello_msgs:
                log_err("Connection to {0} not established and got {1} message!  Closing."
                        .format(self.peer_desc, msg_type))
                self.state |= ConnectionState.MARK_FOR_CLOSE
                return 0

            log_debug("Received message of type {0} from {1}".format(msg_type, self.peer_desc))

            if msg_type in self.message_handlers:
                msg_handler = self.message_handlers[msg_type]
                msg_handler(msg)

        log_debug("Done receiving from {0}".format(self.peer_desc))
        return 0

    # Pop the next message off of the buffer given the message length.
    # Preserve invariant of self.inputbuf always containing the start of a valid message.
    def pop_next_message(self, payload_len, msg_type=Message, hdr_size=HDR_COMMON_OFF):
        try:
            msg_len = hdr_size + payload_len
            msg_contents = self.inputbuf.remove_bytes(msg_len)
            return msg_type.parse(msg_contents)
        except UnrecognizedCommandError as e:
            log_err("Unrecognized command on {0}. Error Message: {1}".format(self.peer_desc, e.msg))
            log_debug("Src: {0} Raw data: {1}".format(self.peer_desc, e.raw_data))
            return None

        except PayloadLenError as e:
            log_err("ParseError on connection {0}.".format(self.peer_desc))
            log_debug("ParseError message: {0}".format(e.msg))
            self.state |= ConnectionState.MARK_FOR_CLOSE  # Close, no retry.
            return None

    # Collect input from the socket and store it in the inputbuffer until either the socket is drained
    # or the throttling limits are hit.
    def collect_input(self):
        log_debug("Collecting input from {0}".format(self.peer_desc))
        collect_input = True

        while collect_input:
            # Read from the socket and store it into the recv buffer.
            try:
                bytes_read = self.sock.recv_into(self.recv_buf, RECV_BUFSIZE)
            except socket.error as e:
                if e.errno in [errno.EAGAIN, errno.EWOULDBLOCK]:
                    log_debug("Received errno {0} with msg {1} on connection {2}. Stop collecting input"
                              .format(e.errno, e.strerror, self.peer_desc))
                    break
                elif e.errno in [errno.EINTR]:
                    # we were interrupted, try again
                    log_debug("Received errno {0} with msg {1}, recv on {2} failed. Continuing recv."
                              .format(e.errno, e.strerror, self.peer_desc))
                    continue
                elif e.errno in [errno.ECONNREFUSED]:
                    # Fatal errors for the connections
                    log_debug("Received errno {0} with msg {1}, recv on {2} failed. Closing connection and retrying..."
                              .format(e.errno, e.strerror, self.peer_desc))
                    self.state |= ConnectionState.MARK_FOR_CLOSE
                    return
                elif e.errno in [errno.ECONNRESET, errno.ETIMEDOUT, errno.EBADF]:
                    # Perform orderly shutdown
                    self.state |= ConnectionState.MARK_FOR_CLOSE
                    return
                elif e.errno in [errno.EFAULT, errno.EINVAL, errno.ENOTCONN, errno.ENOMEM]:
                    # Should never happen errors
                    log_err("Received errno {0} with msg {1}, recv on {2} failed. This should never happen..."
                            .format(e.errno, e.strerror, self.peer_desc))
                    return
                else:
                    raise e

            piece = self.recv_buf[:bytes_read]
            log_debug("Got {0} bytes from {2}. They were: {1}".format(bytes_read, repr(piece), self.peer_desc))

            # A 0 length recv is an orderly shutdown.
            if bytes_read == 0:
                self.state |= ConnectionState.MARK_FOR_CLOSE
                return
            else:
                self.inputbuf.add_bytes(piece)

    # Send bytes to the peer on the given buffer. Return the number of bytes sent.
    # buf must obey the output buffer read interface which has three properties:
    def send_bytes_on_buffer(self, buf, send_one_msg=False):
        total_bytes_written = 0
        byteswritten = 0

        # Send on the socket until either the socket is full or we have nothing else to send.
        while self.sendable and buf.has_more_bytes() > 0 and (not send_one_msg or buf.at_msg_boundary()):
            try:
                byteswritten = self.sock.send(buf.get_buffer())
                total_bytes_written += byteswritten
            except socket.error as e:
                if e.errno in [errno.EAGAIN, errno.EWOULDBLOCK, errno.ENOBUFS]:
                    # Normal operation
                    log_debug("Got {0}. Done sending to {1}. Marking as not sendable."
                              .format(e.strerror, self.peer_desc))
                    self.sendable = False
                elif e.errno in [errno.EINTR]:
                    # Try again later errors
                    log_debug("Got {0}. Send to {1} failed, trying again...".format(e.strerror, self.peer_desc))
                    continue
                elif e.errno in [errno.EACCES, errno.ECONNRESET, errno.EPIPE, errno.EHOSTUNREACH]:
                    # Fatal errors for the connection
                    log_debug("Got {0}, send to {1} failed, closing connection.".format(e.strerror, self.peer_desc))
                    self.state |= ConnectionState.MARK_FOR_CLOSE
                    return 0
                elif e.errno in [errno.ECONNRESET, errno.ETIMEDOUT, errno.EBADF]:
                    # Perform orderly shutdown
                    self.state = ConnectionState.MARK_FOR_CLOSE
                    return 0
                elif e.errno in [errno.EDESTADDRREQ, errno.EFAULT, errno.EINVAL,
                                 errno.EISCONN, errno.EMSGSIZE, errno.ENOTCONN, errno.ENOTSOCK]:
                    # Should never happen errors
                    log_debug("Got {0}, send to {1} failed. Should not have happened..."
                              .format(e.strerror, self.peer_desc))
                    exit(1)
                elif e.errno in [errno.ENOMEM]:
                    # Fatal errors for the node
                    log_debug("Got {0}, send to {1} failed. Fatal error! Shutting down node."
                              .format(e.strerror, self.peer_desc))
                    exit(1)
                else:
                    raise e

            buf.advance_buffer(byteswritten)
            byteswritten = 0

        return total_bytes_written

        # Handle a Hello Message

    def msg_hello(self, msg):
        self.state |= ConnectionState.HELLO_RECVD
        self.enqueue_msg(AckMessage())

        # Handle an Ack Message

    def msg_ack(self, msg):
        self.state |= ConnectionState.HELLO_ACKD

    def msg_ping(self, msg):
        self.enqueue_msg(PongMessage(msg.nonce()))

    def msg_pong(self, msg):
        pass

    # Receive a transaction assignment from txhash -> shortid
    def msg_txassign(self, msg):
        tx_hash = msg.tx_hash()

        log_debug("Processing txassign message")
        if self.node.tx_manager.get_txid(tx_hash) == -1:
            log_debug("Assigning {0} to sid {1}".format(msg.tx_hash(), msg.short_id()))
            self.node.tx_manager.assign_tx_to_sid(tx_hash, msg.short_id(), time.time())
            return tx_hash

        return None

    def close(self):
        log_debug("Closing connection to {0}".format(self.peer_desc))
        self.sock.close()


class ConnectionState(object):
    CONNECTING = 0b000000000  # Received EINPROGRESS when calling socket.connect
    INITIALIZED = 0b000000001
    HELLO_RECVD = 0b000000010  # Received version message from the remote end
    HELLO_ACKD = 0b000000100  # Received verack message from the remote end
    ESTABLISHED = 0b000000111  # Received version + verack message, is initialized
    MARK_FOR_CLOSE = 0b001000000  # Connection is closed
