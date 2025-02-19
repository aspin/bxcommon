import platform
import socket

from bxcommon.utils import crypto
from bxcommon.utils.object_hash import Sha256Hash

PLATFORM_LINUX = "linux"
PLATFORM_MAC = "darwin"
DEFAULT_TEXT_ENCODING = "utf-8"
LISTEN_ON_IP_ADDRESS = "0.0.0.0"
LOCALHOST = "127.0.0.1"
MAX_BYTE_VALUE = 255

PUBLIC_IP_ADDR_REGEX = r"[0-9]+(?:\.[0-9]+){3}"
PUBLIC_IP_ADDR_RESOLVER = "http://checkip.dyndns.org/"

NODE_CONFIG_FILE = "config.cfg"
BLXR_ENV_VAR = "BLXR_ENV"

HOSTNAME = socket.gethostname()
OS_VERSION = platform.platform()

MANIFEST_PATH = "MANIFEST.MF"
MANIFEST_SOURCE_VERSION = "source_version"
PROTOCOL_VERSION = "protocol_version"
REQUIRED_PARAMS_IN_MANIFEST = [MANIFEST_SOURCE_VERSION]
VERSION_TYPE_LIST = ["dev", "v", "ci"]

# <editor-fold desc="Internal Constants">
ALL_NETWORK_NUM = 0
DEFAULT_NETWORK_NUM = 1

OUTPUT_BUFFER_MIN_SIZE = 65535
OUTPUT_BUFFER_BATCH_MAX_HOLD_TIME = 0.05

# The unsigned integer transaction SID representing null.
# If changing, also change in bxapi/constants.py
NULL_TX_SID = 0
UNKNOWN_TRANSACTION_HASH: Sha256Hash = Sha256Hash(bytearray(b"\xff" * crypto.SHA256_HASH_LEN))
# </editor-fold>

# <editor-fold desc="Connection Management">

# number of tries to resolve network address
NET_ADDR_INIT_CONNECT_TRIES = 3
NET_ADDR_INIT_CONNECT_RETRY_INTERVAL_SECONDS = 2

MAX_CONN_BY_IP = 30

# seconds interval between checking connection stances
CONNECTION_TIMEOUT = 3

MAX_CONNECT_RETRIES = 3
MAX_CONNECT_TIMEOUT_INCREASE = 7

RECV_BUFSIZE = 65536
MAX_BAD_MESSAGES = 3
PING_INTERVAL_S = 60
# </editor-fold>

# <editor-fold desc="Logging">

MAX_LOGGED_BYTES_LEN = 500 * 1024

# </editor-fold>

# <editor-fold desc="Message Packing Constants">

STARTING_SEQUENCE_BYTES = bytearray(b"\xFF\xFE\xFD\xFC")
STARTING_SEQUENCE_BYTES_LEN = 4
CONTROL_FLAGS_LEN = 1
UL_SHORT_SIZE_IN_BYTES = 2
UL_INT_SIZE_IN_BYTES = 4
UL_ULL_SIZE_IN_BYTES = 8
IP_V4_PREFIX = bytearray(b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xff")
IP_V4_PREFIX_LENGTH = 12
IP_ADDR_SIZE_IN_BYTES = 16
MSG_NULL_BYTE = b"\x00"

# bytes of basic message header
BX_HDR_COMMON_OFF = 16

# bytes for storing message type
MSG_TYPE_LEN = 12

BLOCK_ENCRYPTED_FLAG_LEN = 1

NETWORK_NUM_LEN = UL_INT_SIZE_IN_BYTES
VERSION_NUM_LEN = UL_INT_SIZE_IN_BYTES
VERSIONED_HELLO_MSG_MIN_PAYLOAD_LEN = UL_INT_SIZE_IN_BYTES + NETWORK_NUM_LEN + VERSION_NUM_LEN

NODE_ID_SIZE_IN_BYTES = 16

NULL_ENCRYPT_REPEAT_VALUE = "1"  # must be nonzero string character
BLOXROUTE_HELLO_MESSAGES = [b"hello", b"ack"]

# </editor-fold>

# <editor-fold desc="SDN Constants">
SDN_ROOT_URL = "http://127.0.0.1:8080"
SDN_CONTACT_RETRY_SECONDS = 5
MAX_COUNTRY_LENGTH = 30

# Should use extension modules
USE_EXTENSION_MODULES = True

# Should support compact block message
ACCEPT_COMPACT_BLOCK = True

DUMP_MISSING_SHORT_IDS_PATH = "/app/bxrelay/debug/missing-short-ids"


class SdnRoutes(object):
    nodes = "/nodes"
    node = "/nodes/{0}"
    gateway_node_config = "/configs/gateway_node/{0}"
    node_relays = "/nodes/{0}/peers"
    node_potential_relays = "/nodes/{0}/potential-relays"
    node_potential_relays_by_network = "/nodes/{0}/{1}/potential-relays"
    node_gateways = "/nodes/{0}/gateways"
    node_remote_blockchain = "/nodes/blockchain-peers/{0}"
    node_event = "/nodes/{0}/events"
    blockchain_network = "/blockchain-networks/{0}/{1}"
    blockchain_networks = "/blockchain-networks"
    gateway_inbound_connection = "/nodes/{0}/gateway-inbound-connection"


# </editor-fold>

# <editor-fold desc="Stats Recording">
FIRST_STATS_INTERVAL_S = 5 * 60

THROUGHPUT_STATS_INTERVAL_S = 15
THROUGHPUT_STATS_LOOK_BACK = 5

INFO_STATS_INTERVAL_S = 60 * 60

# how often the threaded stats services check for termination
THREADED_STAT_SLEEP_INTERVAL = 1

# TODO: turn this number up to 60 minutes after we've done some testing to ensure that this is ok
MEMORY_STATS_INTERVAL_S = 5 * 60
MEMORY_USAGE_INCREASE_FOR_NEXT_REPORT_BYTES = 100 * 1024 * 1024

# Percentage for transactions that will be logged by stats service. The value should be controlled by SDN in the future.
TRANSACTIONS_PERCENTAGE_TO_LOG_STATS_FOR = 0.5
ENABLE_TRANSACTIONS_STATS_BY_SHORT_IDS = False
DEFAULT_THREAD_POOL_PARALLELISM_DEGREE = 1
DEFAULT_TX_MEM_POOL_BUCKET_SIZE = 10000

# </editor-fold>

# <editor-fold desc="Timers">
MAX_KQUEUE_EVENTS_COUNT = 1000
CANCEL_ALARMS = 0

# Fast execution timeout on alarm queue
DEFAULT_SLEEP_TIMEOUT = 0.1

REQUEST_EXPIRATION_TIME = 15 * 60  # TODO: Return this value to 1 minute

# Expiration time for encrypted blocks in cache on relays and gateways
BLOCK_CACHE_TIMEOUT_S = 60 * 60

# Duration to warn on if alarm doesn't execute
WARN_ALARM_EXECUTION_DURATION = 1

# Timeout to warn on if alarm executed later than expected
WARN_ALARM_EXECUTION_OFFSET = 5

# Minimal expired transactions clean up task frequency
MIN_CLEAN_UP_EXPIRED_TXS_TASK_INTERVAL_S = 1 * 60

# Duration to warn on if message processing takes longer than
WARN_MESSAGE_PROCESSING_S = 0.1

# Expiration time for cache of relayed blocks hashes
RELAYED_BLOCKS_EXPIRE_TIME_S = 6 * 60 * 60

DUMP_REMOVED_SHORT_IDS_INTERVAL_S = 5 * 60
DUMP_REMOVED_SHORT_IDS_PATH = "/app/bxcommon/debug/removed-short-ids"

CLEAN_UP_SEEN_SHORT_IDS_DELAY_S = 10

# </editor-fold>

# <editor-fold desc="Default Values">

# Default transactions contents cache maximum size per network number
DEFAULT_TX_CACHE_MEMORY_LIMIT_BYTES = 250 * 1024 * 1024

# Default maximum allowed length of internal message payload
DEFAULT_MAX_PAYLOAD_LEN_BYTES = 1024 * 1024

# cleanup confirmed blocks in this depth
BLOCK_CONFIRMATIONS_COUNT = 4

TXS_MSG_SIZE = 64000
TX_SERVICE_SYNC_TXS_S = 0.01
SENDING_TX_MSGS_TIMEOUT_MS = 1 * 60 * 1000
TX_SERVICE_CHECK_NETWORKS_SYNCED_S = 5 * 60
LAST_MSG_FROM_RELAY_THRESHOLD_S = 30
PING_TIMEOUT_S = 2

NODE_LATENCY_THRESHOLD_MS = 2
FASTEST_PING_LATENCY_THRESHOLD_PERCENT = 0.2
UPDATE_TX_SERVICE_FULLY_SYNCED_S = 1
TX_SERVICE_SYNC_PROGRESS_S = 10
TX_SERVICE_SYNC_RELAY_IN_NETWORKS_S = 30

ALARM_QUEUE_INIT_EVENT = 1

# extensions memory management params
MAX_ALLOCATION_POINTER_COUNT = 10
MAX_COUNT_PER_ALLOCATION = 10

EMPTY_SOURCE_ID = MSG_NULL_BYTE * 16

TRANSACTION_SERVICE_LOG_TRANSACTIONS_INTERVAL_S = 60 * 15
TRANSACTION_SERVICE_TRANSACTIONS_HISTOGRAM_BUCKETS = 36

# https://urllib3.readthedocs.io/en/latest/reference/urllib3.util.html#module-urllib3.util.retry
HTTP_REQUEST_RETRIES_COUNT: int = 3
HTTP_REQUEST_BACKOFF_FACTOR: float = 0.5
HTTP_REQUEST_TIMEOUT: int = 4

MAX_EVENT_LOOP_TIMEOUT_S = 1

# </editor-fold>

# keep constants_local.py file to override settings in the constants file
# this part should be at the bottom of the file
try:
    # pyre-ignore Leave this for CircleCI, as it lacks a constants_local.py
    from bxcommon.constants_local import *
except ImportError as e:
    pass
