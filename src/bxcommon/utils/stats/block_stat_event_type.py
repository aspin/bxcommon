from bxcommon.utils.stats.stat_event_logic_flags import StatEventLogicFlags
from bxcommon.utils.stats.stat_event_type_settings import StatEventTypeSettings


class BlockStatEventType:
    BLOCK_ANNOUNCED_BY_BLOCKCHAIN_NODE = StatEventTypeSettings("BlockAnnouncedByBlockchainNode")
    BLOCK_RECEIVED_FROM_BLOCKCHAIN_NODE = StatEventTypeSettings("BlockReceivedFromBlockchainNode")
    BLOCK_RECEIVED_FROM_BLOCKCHAIN_NODE_IGNORE_SEEN = StatEventTypeSettings(
        "BlockReceivedFromBlockchainNodeIgnoreSeen"
    )
    COMPACT_BLOCK_RECEIVED_FROM_BLOCKCHAIN_NODE = StatEventTypeSettings("CompactBlockReceivedFromBlockchainNode")
    COMPACT_BLOCK_RECEIVED_FROM_BLOCKCHAIN_NODE_IGNORE_SEEN = StatEventTypeSettings(
        "CompactBlockReceivedFromBlockchainNodeIgnoreSeen"
    )
    COMPACT_BLOCK_COMPRESSED_SUCCESS = StatEventTypeSettings(
        "CompactBlockCompressedSuccess"
    )
    COMPACT_BLOCK_COMPRESSED_FAILED = StatEventTypeSettings(
        "CompactBlockCompressedFailed"
    )
    COMPACT_BLOCK_RECOVERY_SUCCESS = StatEventTypeSettings("CompactBlockRecoverySuccess")
    COMPACT_BLOCK_RECOVERY_FAILED = StatEventTypeSettings("CompactBlockRecoveryFailed")
    COMPACT_BLOCK_REQUEST_FULL = StatEventTypeSettings("CompactBlockRequestFull")
    BLOCK_COMPRESSED = StatEventTypeSettings("BlockCompressed",
                                             event_logic_flags=StatEventLogicFlags.BLOCK_INFO | \
                                                               StatEventLogicFlags.MATCH)
    BLOCK_ENCRYPTED = StatEventTypeSettings("BlockEncrypted", event_logic_flags=StatEventLogicFlags.MATCH)
    BLOCK_HOLD_REQUESTED = StatEventTypeSettings("BlockHoldRequested", detailed_stat_event=True)
    BLOCK_HOLD_HELD_BLOCK = StatEventTypeSettings("BlockHoldHeldBlock")
    BLOCK_HOLD_LIFTED = StatEventTypeSettings("BlockHoldLifted", detailed_stat_event=True)
    BLOCK_HOLD_TIMED_OUT = StatEventTypeSettings("BlockHoldTimeout")
    BLOCK_HOLD_SENT_BY_GATEWAY_TO_PEERS = StatEventTypeSettings("BlockHoldSentByGatewayToPeers",
                                                                detailed_stat_event=True)
    BLOCK_HOLD_RECEIVED_BY_RELAY_FROM_PEER = StatEventTypeSettings("BlockHoldReceivedByRelayFromPeer",
                                                                   detailed_stat_event=True)
    BLOCK_HOLD_SENT_BY_RELAY_TO_PEERS = StatEventTypeSettings("BlockHoldSentByRelayToPeers",
                                                              detailed_stat_event=True)
    ENC_BLOCK_SENT_FROM_GATEWAY_TO_NETWORK = StatEventTypeSettings("EncBlockSentFromGatewayToNetwork",
                                                                   event_logic_flags=StatEventLogicFlags.SUMMARY)
    ENC_BLOCK_CUT_THROUGH_SEND_START = StatEventTypeSettings("EncBlockCutThroughSendStart")
    ENC_BLOCK_CUT_THROUGH_SEND_END = StatEventTypeSettings("EncBlockCutThroughSendEnd")
    ENC_BLOCK_CUT_THROUGH_RECEIVE_START = StatEventTypeSettings("EncBlockCutThroughReceiveStart",
                                                                event_logic_flags=StatEventLogicFlags.SUMMARY)
    ENC_BLOCK_CUT_THROUGH_RECEIVE_END = StatEventTypeSettings("EncBlockCutThroughReceiveEnd")
    ENC_BLOCK_CUT_THROUGH_IGNORE_SEEN_BLOCK = StatEventTypeSettings("EncBlockCutThroughIgnoreSeenBlock")
    ENC_BLOCK_CUT_THROUGH_SOURCE_CANCELLED = StatEventTypeSettings("EncBlockCutThroughCancelled")
    ENC_BLOCK_CUT_THROUGH_MANGER_CANCELLED = StatEventTypeSettings("EncBlockCutThroughManagerCancelled")
    ENC_BLOCK_RECEIVED_BY_GATEWAY_FROM_NETWORK = StatEventTypeSettings("EncBlockReceivedByGatewayFromNetwork")
    ENC_BLOCK_DECRYPTED_SUCCESS = StatEventTypeSettings("EncBlockDecryptedSuccess")
    ENC_BLOCK_DECRYPTION_ERROR = StatEventTypeSettings("EncBlockDecryptionError")
    ENC_BLOCK_SENT_BLOCK_RECEIPT = StatEventTypeSettings("EncBlockSentBlockReceipt", detailed_stat_event=True)
    ENC_BLOCK_RECEIVED_BLOCK_RECEIPT = StatEventTypeSettings("EncBlockReceivedBlockReceipt")
    ENC_BLOCK_PROPAGATION_NEEDED = StatEventTypeSettings("EncBlockPropagationNeeded")
    BX_BLOCK_PROPAGATION_REQUESTED_BY_PEER = StatEventTypeSettings("BxBlockPropagationRequestedByPeer")
    BLOCK_CUT_THROUGH_SUMMARY = StatEventTypeSettings("BlockCutThroughSummary",
                                                      event_logic_flags=StatEventLogicFlags.SUMMARY)

    BLOCK_TO_ENC_BLOCK_MATCH = StatEventTypeSettings("BlockHashToEncBlockHash",
                                                     event_logic_flags=StatEventLogicFlags.MATCH)
    BLOCK_DECOMPRESSED_IGNORE_SEEN = StatEventTypeSettings("BlockDecompressedIgnoreSeen",
                                                           event_logic_flags=StatEventLogicFlags.BLOCK_INFO |
                                                                             StatEventLogicFlags.MATCH)
    BLOCK_DECOMPRESSED_SUCCESS = StatEventTypeSettings("BlockDecompressedSuccess",
                                                       event_logic_flags=StatEventLogicFlags.BLOCK_INFO |
                                                                         StatEventLogicFlags.MATCH)
    BLOCK_DECOMPRESSED_WITH_UNKNOWN_TXS = StatEventTypeSettings("BlockDecompressedWithUnknownTxs")
    BLOCK_CONVERSION_FAILED = StatEventTypeSettings("BlockConversionFailed")
    BLOCK_RECOVERY_STARTED = StatEventTypeSettings("BlockRecoveryStarted")
    BLOCK_RECOVERY_REPEATED = StatEventTypeSettings("BlockRecoveryRepeated")
    BLOCK_RECOVERY_COMPLETED = StatEventTypeSettings("BlockRecoveryCompleted")
    BLOCK_RECOVERY_CANCELED = StatEventTypeSettings("BlockRecoveryCanceled")
    BLOCK_SENT_TO_BLOCKCHAIN_NODE = StatEventTypeSettings("BlockSentToBlockchainNode",
                                                          event_logic_flags=StatEventLogicFlags.SUMMARY)
    BLOCK_IGNORE_SEEN_BY_BLOCKCHAIN_NODE = StatEventTypeSettings("BlockIgnoreSeenByBlockchainNode")
    ENC_BLOCK_KEY_SENT_FROM_GATEWAY_TO_NETWORK = StatEventTypeSettings("EncBlockKeySentFromGatewayToNetwork",
                                                                       event_logic_flags=StatEventLogicFlags.SUMMARY)
    ENC_BLOCK_KEY_RECEIVED_BY_GATEWAY_FROM_NETWORK = StatEventTypeSettings("EncBlockKeyReceivedByGatewayFromNetwork")
    ENC_BLOCK_KEY_SENT_BY_GATEWAY_TO_PEERS = StatEventTypeSettings("EncBlockKeySentByGatewayToPeers",
                                                                   detailed_stat_event=True)
    ENC_BLOCK_KEY_RELAY_BROADCAST = StatEventTypeSettings("EncBlockKeyBroadcast",
                                                          event_logic_flags=StatEventLogicFlags.SUMMARY)
    REMOTE_BLOCK_RECEIVED_BY_GATEWAY = StatEventTypeSettings("RemoteBlockReceivedByGateway")
    REMOTE_BLOCK_REQUESTED_BY_GATEWAY = StatEventTypeSettings("RemoteBlockRequestedByGateway")
