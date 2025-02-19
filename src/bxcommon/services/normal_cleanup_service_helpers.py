from bxutils import logging
from bxutils.logging.log_record_type import LogRecordType

from bxcommon.messages.bloxroute.abstract_cleanup_message import AbstractCleanupMessage
from bxcommon.services.transaction_service import TransactionService

logger = logging.get_logger(LogRecordType.TransactionCleanup)


def contents_cleanup(transaction_service: TransactionService,
                     block_confirmation_message: AbstractCleanupMessage
                     ):
    message_hash = block_confirmation_message.message_hash()
    for short_id in block_confirmation_message.short_ids():
        transaction_service.remove_transaction_by_short_id(short_id, remove_related_short_ids=True)
    for tx_hash in block_confirmation_message.transaction_hashes():
        transaction_service.remove_transaction_by_tx_hash(tx_hash)
    transaction_service.on_block_cleaned_up(message_hash)
    logger.statistics(
        {
            "type": "MemoryCleanup",
            "event": "CacheStateAfterBlockCleanup",
            "message_hash": repr(message_hash),
            "data": transaction_service.get_cache_state_json()
        }
    )
