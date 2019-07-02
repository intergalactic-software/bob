import unittest
from store.Store import Store, JOURNAL_PATH
from store.Store import MAX_PATH_LENGTH, PUT_METHOD, ADD_METHOD
import blockchain.blockutil_U as B


class TestStore(unittest.TestCase):

    def test_put_get(self):
        store = Store()
        tests = [
            ("tA", ["basic"]),
            ("tA", ["overwrite"]),
            ("tB.t2", [14]),
            ("tB.t3", [1, 2, 3]),
            ("tC.t2.t3.t4.t5.t6.t7.t8.t9.t0",  ["max"]),
            ("tC.t2", [5, [None]]),
            ("tC.t2", [None])
        ]

        for (key, val) in tests:
            store.put(key, val)
            self.assertEqual(store.get(key), val)

    def test_clear(self):
        store = Store()
        store.put("t1.t2", [1])
        self.assertEqual(store.get("t1.t2"), [1])
        self.assertIsNone(store.clear("t1.t2"))
        self.assertIsNone(store.get("t1.t2"))

    def test_put_overwrite_fail(self):
        store = Store()
        store.put("t1", 1)
        with self.assertRaises(TypeError):
            store.put("t1.t2", 2)

    def test_put_pathTooLong(self):
        store = Store()
        long_path = "t" + ".t" * MAX_PATH_LENGTH
        with self.assertRaises(ValueError):
            store.put(long_path, [1])

    def test_invalidPath(self):
        store = Store()
        with self.assertRaises(ValueError):
            store.put(None, [1])
        with self.assertRaises(ValueError):
            store.add(None, [1])
        with self.assertRaises(ValueError):
            store.addAll(None, [1])

    def test_getObj(self):
        store = Store()
        store.put("t1", 123)
        self.assertEqual(store.getObj("t1"), 123)

        store.put("t1", [1, 2])
        with self.assertRaises(ValueError):
            store.getObj("t1")

    def test_add_primitives(self):
        store = Store()
        store.add("t1.t2", 1)
        store.add("t1.t2", None)
        self.assertEqual(store.get("t1.t2"), [1, None])
        store.addAll("t1.t2", ["A", 3])
        self.assertEqual(store.get("t1.t2"), [1, None, "A", 3])

    def test_get_filter(self):
        store = Store()
        store.put("t1", [1, 2, 3, 4])
        def is_odd(x): return x % 2 == 1
        self.assertEqual(list(store.get("t1", is_odd)), [1, 3])

    def test_getLasts(self):
        store = Store()
        store.put("t1", [1, 2, 3, 4])
        self.assertEqual(store.getLasts("t1", 1), [4])
        self.assertEqual(store.getLasts("t1", 2), [3, 4])

    def test_getLasts_overflow(self):
        store = Store()
        store.put("t1", [1, 2])
        self.assertEqual(store.getLasts("t1", 5), [1, 2])

    def test_getSince(self):
        store = Store()
        store.put("t1", [1, 2, 3, 4])
        self.assertEqual(store.getSince("t1", 2), [3, 4])

    def test_journal(self):
        store = Store()
        store.put("t1", ["a"])
        store.add("t1", "b")
        journal = store.get(JOURNAL_PATH)
        self.assertEqual(len(journal), 2)
        self.assertEqual(journal[0][B.DATA], ["a"])
        self.assertEqual(journal[0][B.METADATA], {
            "method": PUT_METHOD,
            "path": "t1"
        })
        self.assertEqual(journal[1][B.DATA], "b")
        self.assertEqual(journal[1][B.METADATA], {
            "method": ADD_METHOD,
            "path": "t1"
        })

    def test_processBlock_add(self):
        store = Store()
        block = B.create("test", 1, metadata={
            "method": ADD_METHOD,
            "path": "t1"
        })
        store.processBlock(B.serialize(block))
        self.assertEqual(store.get("t1"), [1])

    def test_processBlock_put(self):
        store = Store()
        block = B.create("test", 1, metadata={
            "method": PUT_METHOD,
            "path": "t1"
        })
        store.processBlock(B.serialize(block))
        self.assertEqual(store.get("t1"), [1])

    def test_journal_sharing(self):
        storeA = Store()
        storeA.addAll("t1", [1, 2, 3, 4])
        storeB = Store()

        for journal in storeA.get(JOURNAL_PATH):
            block_serialized = B.serialize(journal)
            storeB.processBlock(block_serialized)
        self.assertEqual(storeB.get("t1"), [1, 2, 3, 4])
