import unittest
from bob.blockchain import blockutil_U as B


class ADummyClass:
    pass


class TestBlockutilU(unittest.TestCase):

    def test_create(self):
        block = B.create("author", "payload", {"x": 1})
        for key in B.KEYS:
            self.assertIn(key, block)
        self.assertEqual(block[B.AUTHOR], "author")
        self.assertEqual(block[B.DATA], "payload")
        self.assertEqual(block[B.METADATA], {"x": 1})

    def test_create_invalid(self):
        values = [
            (None, {}, None),  # author is None
            ("a", ADummyClass(), None),  # non primitive payload
            ("a", {}, "m"),  # metadata is not a dict
            ("a", {}, [1, 2, 3]),  # metadata is not a dict
        ]
        for (author, payload, meta) in values:
            with self.assertRaises(TypeError):
                B.create(author, payload, meta)

    def test_hashData(self):
        inputs = ["", 123, {"a": 1}, [4, 5, 6]]
        for i in inputs:
            output = B.hash_data(i)
            self.assertIsInstance(output, str)
            self.assertTrue(len(output) > 32 and len(output) < 128)

    def test_isBlock(self):
        block = B.create("author", "payload")
        self.assertTrue(B.is_block(block))

    def test_isBlock_notFull(self):
        block = B.create("author", "payload")
        del block[B.HASH]
        self.assertFalse(B.is_block(block))
        self.assertTrue(B.is_block(block, full=False))

    def test_isBlock_missingKey(self):
        for key in B.KEYS:
            block = B.create("author", "payload")
            del block[key]
            self.assertFalse(B.is_block(block))

    def test_isValid_notBlock(self):
        with self.assertRaises(TypeError):
            B.is_valid({})

    def test_isValid_corrupted(self):
        for key in B.KEYS:
            block = B.create("author", "payload")
            block[key] = "xxx"
            self.assertFalse(B.is_valid(block))

    def test_isValid(self):
        block = B.create("author", "payload")
        self.assertTrue(B.is_valid(block))

    def test_serialize_deserialize(self):
        block = B.create("author", {"data": 123})
        serialized = B.serialize(block)
        self.assertIsInstance(serialized, bytes)
        self.assertEqual(block, B.deserialize(serialized))
