import unittest
from bob.ami.Hub import Hub, HubClient, HUB_VERSION, SEPARATOR, INBOUND_PATH, OUBOUND_PATH
from bob.net.Signals import Signal
from bob.store.MockStore import MockStore, DATA
from bob.store.Store import ADD_METHOD
from bob.ami.tests.test_AMI import Util, STATE_SEQUENCE, FAILED_START_SEQUENCE
import socket
import logging
import tempfile
import time
import bob.blockchain.blockutil_U as B

logging.basicConfig(level=logging.DEBUG)


MOCKSOCKET_SEPARATOR = b"SENT#["

class MockHub(Hub):
    def __init__(self, **kargs):
        super(MockHub, self).__init__(**kargs)
        self.mock_sockets = []


    """ Allows mocking of client sockets for easier testing """
    def mockSockets(self, sockets):
        self.mock_sockets = sockets

    def createClientThread(self, clientSocket, ip):
        clientSocket = self.mock_sockets[0]
        self.mock_sockets = self.mock_sockets[1:]
        return HubClient(clientSocket=clientSocket, ip=ip, store=self.store), {}


class MockSocket:
    """ Allows mocking of socket.recv and logs sent data to a file"""
    def __init__(self):
        self.mock_recv = lambda _: None
        self.last_sent = None
        file = tempfile.NamedTemporaryFile(delete=False)
        self.filename = file.name
        self.mock_func_recv = None
        self.mock_list_recv = None

    def funcOnRecv(self, func):
        self.mock_func_recv = func

    def listOnRecv(self, list_of_data):
        self.mock_list_recv = list_of_data

    def recv(self, max_length):
        to_recv = None
        if self.mock_func_recv is not None:
            to_recv = self.mock_func_recv(self.last_sent)
        elif self.mock_list_recv is not None:
            to_recv = self.mock_list_recv[0]
            if len(self.mock_list_recv) > 1:
                self.mock_list_recv = self.mock_list_recv[1:]
            else:
                self.mock_list_recv = None

        if to_recv is None:
            raise socket.timeout
        else:
            return to_recv

    def send(self, data):
        self.last_sent = data
        with open(self.filename, "a+b") as file:
            file.write(MOCKSOCKET_SEPARATOR + data)

    def getSent(self, to_trim=None):
        with open(self.filename, 'r+b') as file:
            chunks = file.read().split(MOCKSOCKET_SEPARATOR)
            return [chunk.rstrip(to_trim) for chunk in chunks if chunk]

    def shutdown(self, _):
        pass

    def close(self):
        pass


class TestHub(unittest.TestCase):

    # HubClient tests

    def test_HubClient_handshake(self):
        socket = MockSocket()
        socket.funcOnRecv(lambda _: HUB_VERSION + SEPARATOR)

        hubClient = HubClient(socket, "127.0.0.1", store=MockStore())
        self.assertEqual(Util.getStates(Util.run(hubClient)), STATE_SEQUENCE)
        self.assertEqual(socket.getSent(), [HUB_VERSION])

    def test_HubClient_handshake_unsuported(self):
        socket = MockSocket()
        socket.funcOnRecv(lambda _: b"HUB/9.9" + SEPARATOR)

        hubClient = HubClient(socket, "127.0.0.1", store=MockStore())
        self.assertEqual(Util.getStates(Util.run(hubClient)),
                         FAILED_START_SEQUENCE)
        self.assertEqual(socket.getSent(), [HUB_VERSION,
                                            b"Unsupported Hub version"])

    def test_HubClient_handshake_invalid(self):
        socket = MockSocket()
        socket.funcOnRecv(lambda _: b"XXXX")

        hubClient = HubClient(socket, "127.0.0.1", store=MockStore())
        self.assertEqual(Util.getStates(Util.run(hubClient)),
                         FAILED_START_SEQUENCE)
        self.assertEqual(socket.getSent(), [HUB_VERSION, b"Invalid handshake"])

    def test_HubClient_outboundQueue(self):
        socket = MockSocket()
        socket.funcOnRecv(lambda _: HUB_VERSION + SEPARATOR)

        def callback(ami):
            ami.store.put(OUBOUND_PATH, ["A", "B"])
            time.sleep(0.2)

        hubClient = HubClient(socket, "127.0.0.1", store=MockStore())
        self.assertEqual(Util.getStates(Util.run(hubClient, callback)),
                         STATE_SEQUENCE)
        self.assertEqual(socket.getSent(), [HUB_VERSION, b"A", b"B"])

    def test_HubClient_inboundQueue(self):
        signal = Signal(data=B.serialize(B.create('a', 'p')), channel="ABCDEF")
        socket = MockSocket()
        socket.listOnRecv([
            HUB_VERSION + SEPARATOR,
            signal.bytes()
        ])

        def callback(ami):
            time.sleep(0.2)

        hubClient = HubClient(socket, "127.0.0.1", store=MockStore())
        self.assertEqual(Util.getStates(Util.run(hubClient, callback)),
                         STATE_SEQUENCE)

        inbounds = hubClient.store.get(INBOUND_PATH)
        self.assertEqual(inbounds, [signal.bytes()])

    # Hub tests

    def test_init_port(self):
        hub = Hub(store=MockStore())
        self.assertTrue(hub.port > 1000)
        self.assertTrue(hub.port < 65000)
        self.assertEqual(Hub(port=15123, store=MockStore()).port, 15123)

    def test_init_host(self):
        self.assertEqual(Hub(store=MockStore()).host, "127.0.0.1")
        ip = "192.168.0.0"
        self.assertEqual(Hub(host=ip, store=MockStore()).host, ip)

    def test_emit_offline(self):
        hub = Hub(store=MockStore())
        assert(hub.store.get(OUBOUND_PATH) is None)
        signal = Signal(channel="CH1", data=B.serialize(B.create('a', 'p')))
        hub.emit(signal)
        assert(hub.store.get(OUBOUND_PATH) == [signal.bytes()])

    def test_startstop(self):
        hub = Hub(store=MockStore())
        self.assertEqual(Util.getStates(Util.run(hub)), STATE_SEQUENCE)

    def test_createClientThread(self):
        hub = Hub(store=MockStore())
        socket = MockSocket()
        expected = HubClient(clientSocket=socket, ip="127.0.0.1", store=MockStore())
        client, metadata = hub.createClientThread(socket, "127.0.0.1")
        self.assertIsInstance(client, HubClient)
        self.assertEqual(client.clientSocket, expected.clientSocket)
        self.assertEqual(client.ip, expected.ip)

    def test_client_inbound(self):
        block1 = B.serialize(B.create("t1", "A", {
            "method": ADD_METHOD,
            "path": "p1"
        }))
        block2 = B.serialize(B.create("t1", "B", {
            "method": ADD_METHOD,
            "path": "p1"
        }))

        signal1 = Signal(data=block1, channel="Ch1")
        signal2 = Signal(data=block2, channel="Ch1")

        socket1 = MockSocket()
        socket1.listOnRecv([
            HUB_VERSION + SEPARATOR,
            signal1.bytes(),
            signal2.bytes()
        ])

        hub = MockHub(store=MockStore(), subscriptions=["Ch1"])
        hub.mockSockets([socket1, socket1])

        def callback(ami):
            s1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s1.connect((hub.host, hub.port))
            s1.close()
            time.sleep(0.2)

        self.assertEqual(Util.getStates(Util.run(hub, callback)), STATE_SEQUENCE)
        inbounds = [i[DATA] for i in hub.store.getLogs(INBOUND_PATH)]
        self.assertEqual(inbounds, [str(signal1.bytes()), 
                         str(signal2.bytes())])
        p1_path = [i[DATA] for i in hub.store.getLogs("p1")]
        self.assertEqual(p1_path, ["A", "B"])