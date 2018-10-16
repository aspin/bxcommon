import unittest
from bxcommon.utils.object_hash import BTCObjectHash
from bxcommon.constants import SHA256_HASH_LEN


class ObjectHashTests(unittest.TestCase):
    length1 = 32
    length2 = 64
    to_31 = bytearray([i for i in range(length1)])
    to_63 = bytearray([i for i in range(length2)])

    def setUp(self):
        self.int_hash_31a = BTCObjectHash(binary=self.to_31)
        self.int_hash_31b = BTCObjectHash(binary=memoryview(self.to_31))
        self.int_hash_31c = BTCObjectHash(buf=self.to_63, length=32)
        self.int_hash_32 = BTCObjectHash(buf=self.to_63, offset=1, length=self.length1)
        self.int_hash_all_0 = BTCObjectHash(binary=bytearray([0] * self.length1))

    def test_init(self):
        with self.assertRaises(ValueError):
            BTCObjectHash(binary=bytearray([i for i in range(self.length1 - 1)]))
        with self.assertRaises(ValueError):
            BTCObjectHash(binary=bytearray())
        with self.assertRaises(ValueError):
            BTCObjectHash(buf=self.to_63, offset=40)
        expected = self.int_hash_31a.binary
        actual = self.to_31
        self.assertEqual(expected, actual)
        actual2 = BTCObjectHash(binary=memoryview(actual))
        self.assertEqual(expected, actual2.binary)
        self.assertIsNotNone(hash(self.int_hash_all_0))

    def test_hash(self):
        self.assertEqual(hash(self.int_hash_31a), hash(self.int_hash_31b))
        self.assertNotEqual(hash(self.int_hash_31a), hash(self.int_hash_32))
        # checking that hash does not change when byte array is mutated
        to_31 = bytearray([i for i in range(self.length1)])
        mutable_to_31 = BTCObjectHash(binary=to_31)
        initial_hash = hash(mutable_to_31)
        to_31[6] = 12
        mutated_hash = hash(mutable_to_31)
        self.assertEqual(initial_hash, mutated_hash)

    def test_cmp(self):
        self.assertEqual(self.int_hash_31a, self.int_hash_31b)
        self.assertGreater(self.int_hash_32, self.int_hash_31a)
        self.assertLess(self.int_hash_all_0, self.int_hash_31b)

    def test_get_item(self):
        int_list = [0] * SHA256_HASH_LEN
        expected_1 = 3
        expected_index_1 = 1
        expected_2 = 9
        expected_index_2 = 8
        int_list[expected_index_1] = expected_1
        int_list[expected_index_2] = expected_2
        int_hash = BTCObjectHash(binary=bytearray(int_list))
        self.assertEqual(expected_1, int_hash[expected_index_1])
        self.assertEqual(expected_2, int_hash[expected_index_2])

    def test_repr(self):
        self.assertEqual(repr(self.int_hash_31a), repr(self.int_hash_31b))
        self.assertNotEqual(repr(self.int_hash_31a), repr(self.int_hash_32))
        self.assertNotEqual(repr(self.int_hash_31b), repr(self.int_hash_all_0))
        expected = bytearray([i for i in range(self.length1)])
        actual = BTCObjectHash(binary=bytearray(expected))
        self.assertEqual(repr(expected), repr(actual))

    def test_full_string(self):
        expected = str(self.to_31)
        actual = BTCObjectHash(binary=self.to_31).full_string()
        self.assertEqual(expected, actual)

    def test_little_endian(self):
        expected = self.to_31
        actual = BTCObjectHash(binary=self.to_31).get_little_endian()
        self.assertEqual(expected, actual)

    def test_big_endian(self):
        expected = self.to_31[::-1]
        actual = BTCObjectHash(binary=self.to_31).get_big_endian()
        self.assertEqual(expected, actual)








