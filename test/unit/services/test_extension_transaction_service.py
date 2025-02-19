from bxcommon.test_utils.abstract_transaction_service_test_case import AbstractTransactionServiceTestCase
from bxcommon.services.extension_transaction_service import ExtensionTransactionService
from bxcommon.services.transaction_service import TransactionService
from bxcommon.test_utils import helpers


class ExtensionTransactionServiceTest(AbstractTransactionServiceTestCase):

    def setUp(self):
        helpers.set_extensions_parallelism()
        super(ExtensionTransactionServiceTest, self).setUp()

    def test_get_missing_transactions(self):
        self._test_get_missing_transactions()

    def test_sid_assignment_basic(self):
        self._test_sid_assignment_basic()

    def test_sid_assignment_multiple_sids(self):
        self._test_sid_assignment_multiple_sids()

    def test_sid_expiration(self):
        self._test_sid_expiration()

    def test_sid_expiration_multiple_sids(self):
        self._test_sid_expiration_multiple_sids()

    def test_track_short_ids_seen_in_block(self):
        self._test_track_short_ids_seen_in_block()

    def test_track_short_ids_seen_in_block_multiple_per_tx(self):
        self._test_track_short_ids_seen_in_block_multiple_per_tx()

    def test_transactions_contents_memory_limit(self):
        self._test_transactions_contents_memory_limit()

    def test_expire_old_assignments(self):
        self._test_expire_old_assignments()

    def test_memory_stats(self):
        self._test_memory_stats()

    def test_iter_timestamped_transaction_hashes_from_oldest(self):
        self._test_iter_timestamped_transaction_hashes_from_oldest()

    def _get_transaction_service(self) -> TransactionService:
        return ExtensionTransactionService(self.mock_node, 0)
