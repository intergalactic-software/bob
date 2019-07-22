import unittest
import time
import socket
import logging
from bob.ami.TCPServer import TCPServer
from bob.ami.AMI import AMI, FORCE_STOPPING
from bob.ami.tests.test_AMI import Util, STATE_SEQUENCE
from bob.store.MockStore import MockStore

logging.basicConfig(level=logging.DEBUG)


class DummyClient(AMI):

    def __init__(self, client_socket, ip, **args):
        super(DummyClient, self).__init__(store=MockStore(), is_thread=True,
                                          enable_hub=False, **args)
        self.client_socket = client_socket
        self.ip = ip

    def onInterval(self):
        received = self.client_socket.recv(8192)
        if received == '':
            self.logger.info("Client closed socket")
            self.setState(FORCE_STOPPING)
            return

        self.logger.info(b"Received %s", received)
        self.client_socket.send(bytes(len(received)))

    def onStop(self):
        self.client_socket.close()


class LoopDummyClient(DummyClient):
    def __init__(self, client_socket, ip, interval=0.1):
        super(LoopDummyClient, self).__init__(client_socket, ip,
                                              interval=interval)
        self.client_socket = client_socket
        self.ip = ip


class TestTCPServer(unittest.TestCase):

    def test_startStop(self):
        server = TCPServer(enable_hub=False, is_thread=True, store=MockStore())
        self.assertEqual(Util.getStates(Util.run(server)), STATE_SEQUENCE)

    def test_connectClients(self):
        server = TCPServer(enable_hub=False, is_thread=True,
                           app=DummyClient, store=MockStore())

        def callback(ami):
            s1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s1.connect((server.host, server.port))
            s1.send(b"1")
            self.assertEqual(s1.recv(1024), bytes(len("1")))
            s1.close()

            s2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s2.connect((server.host, server.port))
            s2.send(b"22")
            self.assertEqual(s2.recv(1024), bytes(len("22")))
            s2.close()

            time.sleep(0.2)

        states = Util.run(server, run_callback=callback)
        self.assertEqual(Util.getStates(states), STATE_SEQUENCE)

    def test_connectClient_loop(self):
        server = TCPServer(enable_hub=False, is_thread=True,
                           app=LoopDummyClient, store=MockStore())

        def callback(ami):
            s1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s1.connect((server.host, server.port))
            s1.send(b"1")
            self.assertEqual(s1.recv(1024), bytes(len("1")))
            s1.send(b"11")
            self.assertEqual(s1.recv(1024), bytes(len("11")))
            s1.close()
            time.sleep(0.1)

        states = Util.run(server, run_callback=callback)
        self.assertEqual(Util.getStates(states), STATE_SEQUENCE)
