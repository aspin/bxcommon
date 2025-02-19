import os
import socket
from argparse import Namespace
from contextlib import closing
from typing import Optional, TypeVar, Type, TYPE_CHECKING

from bxcommon import constants
from bxcommon.connections.abstract_node import AbstractNode
from bxcommon.connections.node_type import NodeType
from bxcommon.models.blockchain_network_environment import BlockchainNetworkEnvironment
from bxcommon.models.blockchain_network_model import BlockchainNetworkModel
from bxcommon.models.blockchain_network_type import BlockchainNetworkType
from bxcommon.test_utils.mocks.mock_node import MockNode
from bxcommon.test_utils.mocks.mock_socket_connection import MockSocketConnection
from bxcommon.utils import config, crypto, convert
from bxcommon.utils.buffers.input_buffer import InputBuffer
from bxcommon.utils.object_hash import Sha256Hash
from bxcommon.utils.proxy import task_pool_proxy

if TYPE_CHECKING:
    # noinspection PyUnresolvedReferences
    from bxcommon.connections.abstract_connection import AbstractConnection


COOKIE_FILE_PATH = "gateway_cookies/.cookie.blxrbdn-gw-localhost:8080"
BTC_COMPACT_BLOCK_DECOMPRESS_MIN_TX_COUNT = 10


def generate_bytes(size):
    return bytes(generate_bytearray(size))


def generate_bytearray(size):
    result = bytearray(0)
    result.extend(os.urandom(size))

    return result


def generate_hash() -> bytearray:
    return generate_bytearray(crypto.SHA256_HASH_LEN)


def generate_object_hash() -> Sha256Hash:
    return Sha256Hash(generate_hash())


Connection = TypeVar("Connection", bound="AbstractConnection")


def create_connection(connection_cls: Type[Connection],
                      node: Optional[AbstractNode] = None,
                      node_opts: Optional[Namespace] = None,
                      fileno: int = 1,
                      ip: str = constants.LOCALHOST,
                      port: int = 8001,
                      from_me: bool = False,
                      add_to_pool: bool = True) -> Connection:
    if node_opts is None:
        node_opts = get_common_opts(8002)

    if node is None:
        node = MockNode(node_opts)

    if isinstance(node, MockNode):
        add_to_pool = False

    test_address = (ip, port)
    test_socket_connection = MockSocketConnection(fileno, node)
    connection = connection_cls(test_socket_connection, test_address, node, from_me)

    if add_to_pool:
        node.connection_pool.add(fileno, ip, port, connection)
    return connection


def clear_node_buffer(node, fileno):
    bytes_to_send = node.get_bytes_to_send(fileno)
    while bytes_to_send is not None and len(bytes_to_send) > 0:
        node.on_bytes_sent(fileno, len(bytes_to_send))
        bytes_to_send = node.get_bytes_to_send(fileno)


def receive_node_message(node, fileno, message):
    node.on_bytes_received(fileno, message)
    node.on_finished_receiving(fileno)


def get_queued_node_message(node: AbstractNode, fileno: int, message_type: str):
    bytes_to_send = node.get_bytes_to_send(fileno)
    assert message_type in bytes_to_send.tobytes(), \
        f"could not find {message_type} in message bytes {convert.bytes_to_hex(bytes_to_send.tobytes())}"
    node.on_bytes_sent(fileno, len(bytes_to_send))
    return bytes_to_send


def get_free_port():
    """
    Find a free port and returns it. Has a race condition that some other process could steal the port between this
    and the actual port usage, but that shouldn't be too important.
    :return: port number
    """
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        sock.bind(("", 0))
        address, port = sock.getsockname()
    return port


def create_input_buffer_with_message(message):
    return create_input_buffer_with_bytes(message.rawbytes())


def create_input_buffer_with_bytes(message_bytes):
    input_buffer = InputBuffer()
    input_buffer.add_bytes(message_bytes)
    return input_buffer


def set_extensions_parallelism(degree: int = constants.DEFAULT_THREAD_POOL_PARALLELISM_DEGREE) -> None:
    task_pool_proxy.init(config.get_thread_pool_parallelism_degree(str(degree)))


def blockchain_network(protocol: str, network_name: str, network_num: int, block_recovery_timeout: int = 30,
                       block_hold_timeout: int = 30, final_tx_confirmations_count: int = 2,
                       block_confirmations_count: int = 1, **kwargs) \
        -> BlockchainNetworkModel:
    _blockchain_network = BlockchainNetworkModel(
        protocol, network_name, network_num, BlockchainNetworkType.PUBLIC, BlockchainNetworkEnvironment.DEVELOPMENT,
        {}, 60, 5, block_recovery_timeout, block_hold_timeout, final_tx_confirmations_count, 50 * 1024 * 1024,
        block_confirmations_count=block_confirmations_count
    )

    for key, val in kwargs.items():
        _blockchain_network.__dict__[key] = val
    return _blockchain_network


def get_common_opts(port,
                    external_ip=constants.LOCALHOST,
                    node_id=None,
                    outbound_peers=None,
                    blockchain_network_num=constants.ALL_NETWORK_NUM,
                    block_confirmations_count=2,
                    final_tx_confirmations_count=4,
                    **kwargs) -> Namespace:
    if node_id is None:
        node_id = f"Node at {port}"
    if outbound_peers is None:
        outbound_peers = []

    opts = Namespace()
    opts.__dict__ = {
        "external_ip": external_ip,
        "external_port": port,
        "node_id": node_id,
        "outbound_peers": outbound_peers,
        "memory_stats_interval": 3600,
        "blockchain_network_num": blockchain_network_num,
        "dump_detailed_report_at_memory_usage": 100,
        "dump_removed_short_ids": False,
        "dump_missing_short_ids": False,
        "sid_expire_time": 30,
        "blockchain_networks": [
            blockchain_network("Bitcoin", "Mainnet", 0, 15, 15, final_tx_confirmations_count, block_confirmations_count),
            blockchain_network("Bitcoin", "Testnet", 1, 15, 15, final_tx_confirmations_count, block_confirmations_count),
            blockchain_network("Ethereum", "Mainnet", 2, 5, 5, final_tx_confirmations_count, block_confirmations_count),
            blockchain_network("Ethereum", "Testnet", 3, 5, 5, final_tx_confirmations_count, block_confirmations_count)
        ],
        "transaction_pool_memory_limit": 200000000,
        "track_detailed_sent_messages": True,
        "use_extensions": constants.USE_EXTENSION_MODULES,
        "import_extensions": constants.USE_EXTENSION_MODULES,
        "tx_mem_pool_bucket_size": constants.DEFAULT_TX_MEM_POOL_BUCKET_SIZE,
        "throughput_stats_interval": constants.THROUGHPUT_STATS_INTERVAL_S,
        "info_stats_interval": constants.INFO_STATS_INTERVAL_S,
        "sync_tx_service": True,
    }
    for key, val in kwargs.items():
        opts.__dict__[key] = val
    return opts


def get_gateway_opts(port, node_id=None, external_ip=constants.LOCALHOST, blockchain_address=None,
                     test_mode=None, peer_gateways=None, peer_relays=None, peer_transaction_relays=None,
                     split_relays=False, protocol_version=1, sid_expire_time=30, bloxroute_version="bloxroute 1.5",
                     include_default_btc_args=False, include_default_eth_args=False,
                     blockchain_network_num=constants.DEFAULT_NETWORK_NUM, min_peer_gateways=0,
                     remote_blockchain_ip=None, remote_blockchain_port=None, connect_to_remote_blockchain=False,
                     is_internal_gateway=False, is_gateway_miner=False, enable_buffered_send=False, encrypt_blocks=True,
                     parallelism_degree=1, cookie_file_path=COOKIE_FILE_PATH, blockchain_block_hold_timeout_s=30,
                     blockchain_block_recovery_timeout_s=30, stay_alive_duration=30 * 60, source_version="v1.1.1.1",
                     initial_liveliness_check=30, block_interval=600, **kwargs) -> Namespace:
    if node_id is None:
        node_id = "Gateway at {0}".format(port)
    if peer_gateways is None:
        peer_gateways = []
    if peer_relays is None:
        peer_relays = []
    if peer_transaction_relays is None:
        peer_transaction_relays = []
    if blockchain_address is None:
        blockchain_address = ("127.0.0.1", 7000)  # not real, just a placeholder
    if test_mode is None:
        test_mode = []
    if remote_blockchain_ip is not None and remote_blockchain_port is not None:
        remote_blockchain_peer = (remote_blockchain_ip, remote_blockchain_port)
    else:
        remote_blockchain_peer = None

    partial_apply_args = locals().copy()
    for kwarg, arg in partial_apply_args["kwargs"].items():
        partial_apply_args[kwarg] = arg

    partial_apply_args["outbound_peers"] = peer_gateways + peer_relays

    opts = get_common_opts(**partial_apply_args)

    opts.__dict__.update({
        "node_type": NodeType.GATEWAY,
        "bloxroute_version": bloxroute_version,
        "blockchain_ip": blockchain_address[0],
        "blockchain_port": blockchain_address[1],
        "blockchain_protocol": "Bitcoin",
        "blockchain_network": "Mainnet",
        "test_mode": test_mode,
        "peer_gateways": peer_gateways,
        "peer_relays": peer_relays,
        "peer_transaction_relays": peer_transaction_relays,
        "split_relays": split_relays,
        "protocol_version": protocol_version,
        "blockchain_block_interval": block_interval,
        "blockchain_ignore_block_interval_count": 3,
        "blockchain_block_recovery_timeout_s": blockchain_block_recovery_timeout_s,
        "blockchain_block_hold_timeout_s": blockchain_block_hold_timeout_s,
        "min_peer_gateways": min_peer_gateways,
        "remote_blockchain_ip": remote_blockchain_ip,
        "remote_blockchain_port": remote_blockchain_port,
        "remote_blockchain_peer": remote_blockchain_peer,
        "connect_to_remote_blockchain": connect_to_remote_blockchain,
        "is_internal_gateway": is_internal_gateway,
        "is_gateway_miner": is_gateway_miner,
        "encrypt_blocks": encrypt_blocks,
        "enable_buffered_send": enable_buffered_send,
        "compact_block": True,
        "compact_block_min_tx_count": BTC_COMPACT_BLOCK_DECOMPRESS_MIN_TX_COUNT,
        "tune_send_buffer_size": False,
        "dump_short_id_mapping_compression": False,
        "thread_pool_parallelism_degree": config.get_thread_pool_parallelism_degree(
            str(parallelism_degree)
        ),
        "max_block_interval": 10,
        "cookie_file_path": cookie_file_path,
        "config_update_interval": 60,
        "blockchain_message_ttl": 10,
        "remote_blockchain_message_ttl": 10,
        "stay_alive_duration": stay_alive_duration,
        "initial_liveliness_check": initial_liveliness_check,
        "has_fully_updated_tx_service": False,
        "source_version": source_version,
        "require_blockchain_connection": True
    })

    if include_default_btc_args:
        opts.__dict__.update({
            "blockchain_net_magic": 12345,
            "blockchain_version": 23456,
            "blockchain_nonce": 0,
            "blockchain_services": 1,
        })
    if include_default_eth_args:
        opts.__dict__.update({
            "private_key": "294549f8629f0eeb2b8e01aca491f701f5386a9662403b485c4efe7d447dfba3",
            "node_public_key": None,
            "remote_public_key": None,
            "network_id": 1,
            "chain_difficulty": 4194304,
            "genesis_hash": "1e8ff5fd9d06ab673db775cf5c72a6b2d63171cd26fe1e6a8b9d2d696049c781",
            "no_discovery": True,
        })
    for key, val in kwargs.items():
        opts.__dict__[key] = val
    return opts
