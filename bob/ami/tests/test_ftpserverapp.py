import unittest
import time
from bob.ami.tests.test_AMI import Util, STATE_SEQUENCE
from bob.ami.tests.test_hub import MockSocket
from bob.ami.FTPServerApp import FTPServerApp, BANNER
from bob.store.MockStore import MockStore



class TestFTPServerApp(unittest.TestCase):


    # def test_banner(self):
    #     mock_socket = MockSocket()
    #     server = FTPServerApp(clientSocket=mock_socket, ip="127.0.0.1",
    #                           is_thread=True, store=MockStore(),
    #                           enable_hub=False)
    #     self.assertEqual(Util.getStates(Util.run(server)), STATE_SEQUENCE)
    #     self.assertEqual(mock_socket.getSent()[0][:50], BANNER[:50])

    def test_commands(self):
        mock_socket = MockSocket()
        mock_socket.listOnRecv([
            b"user tester\n",
            b"pass abcdef\n",
            b"aaa\n"
            b"exit\n"
        ])

        def callback(ami):
            time.sleep(0.2)

        server = FTPServerApp(clientSocket=mock_socket, ip="127.0.0.1",
                              is_thread=True, store=MockStore(),
                              enable_hub=False)
        server.min_timeout = 0
        server.max_timeout = 0
        self.assertEqual(Util.getStates(Util.run(server, run_callback=callback)), STATE_SEQUENCE)
        self.assertEqual(mock_socket.getSent()[1:], [
            b"331 User tester OK. Password required",
            b"530 Login authentication failed",
            b"530 You aren't logged in"
        ])