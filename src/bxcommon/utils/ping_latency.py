import subprocess
from concurrent.futures import ThreadPoolExecutor
from typing import List
from collections import namedtuple

from bxutils import logging

from bxcommon import constants
from bxcommon.models.outbound_peer_model import OutboundPeerModel

logger = logging.get_logger(__name__)
NodeLatencyInfo = namedtuple("NodeLatencyInfo", ["node", "latency"])


def get_ping_latency(outbound_peer: OutboundPeerModel) -> NodeLatencyInfo:
    """
    returns ping latency to the outbound peer
    :param outbound_peer: peer to ping
    """
    try:
        res = subprocess.Popen(["ping", "-c", "1", outbound_peer.ip], stdout=subprocess.PIPE)
        if res:
            output = res.communicate(timeout=constants.PING_TIMEOUT_S)[0].decode()
            ping_latency = float(output.split("time=", 1)[1].split("ms", 1)[0])
        else:
            ping_latency = constants.PING_TIMEOUT_S * 1000
            logger.warning("Could not ping {}.", outbound_peer.ip)
    except subprocess.TimeoutExpired:
        ping_latency = constants.PING_TIMEOUT_S * 1000
        logger.warning("Ping to {} timed out.", outbound_peer.ip)
    except Exception as ex:
        logger.error("Ping to {} triggered an error: {}.", outbound_peer.ip, ex)
        ping_latency = constants.PING_TIMEOUT_S * 1000

    return NodeLatencyInfo(outbound_peer, ping_latency)


def get_ping_latencies(outbound_peers: List[OutboundPeerModel]) -> List[NodeLatencyInfo]:
    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(get_ping_latency, ip) for ip in outbound_peers]
        results = [future.result() for future in futures]
    return results
