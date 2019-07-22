import unittest
from bob.net import bobnet


class BobnetTest(unittest.TestCase):
    def testPortsForHost_Match(self):
        ports1 = bobnet.GetPortsForHost("127.0.0.1")
        ports2 = bobnet.GetPortsForHost("127.0.0.1")
        self.assertEqual(ports1, ports2)

    def testPortsForHost_Dismatch(self):
        ports1 = bobnet.GetPortsForHost("127.0.0.1")
        ports2 = bobnet.GetPortsForHost("127.0.0.2")
        self.assertNotEqual(ports1, ports2)

    def testGetIps_nonEmpty(self):
        ips = bobnet.GetIps()
        self.assertGreater(len(ips), 0)

    def testGetIps_valids(self):
        ips = bobnet.GetIps()
        for ip in ips:
            for s in ip.split('.'):
                self.assertTrue(s.isdigit())

    def testGetNodeId_valid(self):
        ip = "127.0.0.1"
        port = 999
        node_id = bobnet.GetNodeId(ip, port)
        self.assertEqual(type(node_id), str)
        self.assertIn(ip, node_id)
        self.assertIn(str(port), node_id)

    def testGetNodeId_same(self):
        ip = "127.0.0.1"
        port = 999
        self.assertEqual(bobnet.GetNodeId(ip, port),
                         bobnet.GetNodeId(ip, port))


if __name__ == '__main__':
    unittest.main()