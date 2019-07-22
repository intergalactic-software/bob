import unittest
from bob.net import Signal


class TestSignal(unittest.TestCase):

    def test_parse(self):
        values = [
            (bytes(1), [1]),
            (bytes("AAAAAA".encode("ascii")), ["A"]),
            (bytes([21, 4]), ["A", "B"])
        ]

        for value in values:
            signal = Signal(data=value[0], channel=value[1])
            parsed = Signal.parse(signal.bytes())
            self.assertIsInstance(parsed, Signal)
            self.assertEqual(signal, parsed)

    def test_constructor_raise(self):
        with self.assertRaises(ValueError):
            Signal()
        with self.assertRaises(ValueError):
            Signal(data=bytes(1))
        with self.assertRaises(ValueError):
            Signal(channel=bytes(1))
        with self.assertRaises(TypeError):
            Signal(data=[1], channel=["A"])
