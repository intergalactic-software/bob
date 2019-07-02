import unittest
import tempfile
from store.Store import Store
from store.MockStore import MockStore, TYPE, PATH, DATA
import json


class TestStore(unittest.TestCase):

    def test_isStore(self):
        self.assertIsInstance(MockStore(), Store)

    def test_onUpdate(self):
        store = MockStore()
        store.put("path", [1])
        store.add("path", 2)

        logs = store.getLogs("path")
        self.assertEqual(logs, [
            {
                TYPE: "put",
                PATH: "path",
                DATA: "[1]"
            },
            {
                TYPE: "add",
                PATH: "path",
                DATA: "2"
            }
        ])

    def test_mock_with_value(self):
        store = MockStore()
        store.mock_with_value("path", [1, 2, 3])
        self.assertEqual(store.get("path"), [1, 2, 3])

    def test_no_mock(self):
        store = MockStore()
        store.put("path", [1, 2])
        store.add("path", 3)
        self.assertEqual(store.get("path"), [1, 2, 3])

    def test_mock_with_value_override(self):
        store = MockStore()
        store.put("path", [999])
        store.mock_with_value("path", [1, 2, 3])
        self.assertEqual(store.get("path"), [1, 2, 3])

    def test_mock_file(self):
        store = MockStore()
        store.put("path", [1])
        filename = store.mock_with_file("path")
        self.assertEqual(store.get("path"), [1])

        with open(filename, 'w') as file:
            file.write(json.dumps([1, 2]))
        self.assertEqual(store.get("path"), [1, 2])

    def test_mock_with_manual_file(self):
        file = tempfile.NamedTemporaryFile(mode='w', delete=False)
        filename = file.name
        file.write(json.dumps([1, 2, 3]))
        file.close()

        store = MockStore()
        store.mock_with_file("path", filename)
        self.assertEqual(store.get("path"), [1, 2, 3])