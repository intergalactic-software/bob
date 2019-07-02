import random
from sthreads.AMI import AMI, FORCE_STOPPING, FAILED
from sthreads.TCPServer import TCPServer
from queue import Queue
import socket
import logging
from net.Signals import Signal
import sys
import blockchain.blockutil_U as B
from store.Store import Store, JOURNAL_PATH

MAX_PEER = 50
SEPARATOR = "\n\n".encode()

BUFFER_MAX_SIZE = 8096

HUB_VERSION = "HUB/0.1".encode()
MAX_HUB_VERSION = 0.999

INBOUND_PATH = "_inbound"
OUBOUND_PATH = "_outbound"

# TODO:
#   - do network exploration by adding peers from peers
#   - do network exploration by attempting to connect to various port
#       -use bobnet to find common network/ip/port
#   - generate channel per sub network
#   -tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#       ssl_socket = ssl.wrap_socket(tcp_socket,
#          cypher="TLS_ECDHE_RSA_WITH_NULL_SHA")
#       ssl_socket.connect((host, port))


class HubClient(AMI):
    def __init__(self, clientSocket=None, ip=None, store=None, **args):
        super(HubClient, self).__init__(tag="Hub %s" % ip, is_thread=True,
                                        enable_hub=False, interval=0.1,
                                        store=store, **args)
        if not store:
            raise TypeError("a shared store is mandatory for a Hub")
        self.buffer = ""
        self.clientSocket = clientSocket
        self.ip = ip
        self.last_outbound = None

    def onStart(self):
        # HUB_VERSION handshake
        self.clientSocket.send(HUB_VERSION + SEPARATOR)

        received = self.clientSocket.recv(64)
        if b"HUB/" not in received:
            self.send(b"Invalid handshake" + SEPARATOR)
            self.fail("Invalid handshake: %s", received[:100])
            return

        if float(received.split(b"HUB/")[1][:-2]) > MAX_HUB_VERSION:
            self.send(b"Unsupported Hub version")
            self.fail("Unsupported hub version [%s]", received)
            return

        self.logger.debug("Handshake success [%s]", received[:-2])

    def onInterval(self):
        # wait for msg
        self.recv()

        outbound = []
        if self.last_outbound is not None:
            outbound = self.store.getSince(OUBOUND_PATH, self.last_outbound)
        else:
            outbound = self.store.get(OUBOUND_PATH) or []

        for signal in outbound:
            if isinstance(signal, Signal):
                self.send(signal.bytes())
            elif isinstance(signal, str):
                self.send(signal)

            self.last_outbound = signal

    def onStop(self):
        self.clientSocket.shutdown(socket.SHUT_RDWR)
        self.clientSocket.close()
        logging.info("%s: Force disconected", self.TAG)

    def send(self, data):
        self.logger.debug("Sending %d bytes", len(data))
        data_bytes = data if isinstance(data, bytes) else data.encode()
        self.clientSocket.send(data_bytes + SEPARATOR)

    def recv(self):
        try:
            '''
            May receive more than one message at once, thus if the last
            message is invalid, we store it for the next recv iteration.
            If a message is invalid and not the last one received, then it
            gets discared.
            '''
            self.buffer = self.clientSocket.recv(8192)
            signal = Signal.parse(self.buffer)
            if not isinstance(signal, Signal):
                self.logger.warning("Invalid message for reason [%d], [%s]",
                                    int(signal), self.buffer[:100])
            else:
                self.logger.debug("Received signal with id [%s]", signal.id)
                self.store.add(INBOUND_PATH, signal.bytes())

            # data_array = filter(lambda x: x, self.buffer.split(SEPARATOR))
            # for pos, data in enumerate(data_array):
            #     signal = Signal.parse(data)

            #     if signal:
            #         self.store.add(INBOUND_PATH, signal)
            #     elif pos == (len(data_array) - 1):
            #         self.buffer = data
            #         if len(self.buffer) > BUFFER_MAX_SIZE:
            #             self.logger.warn("Max buffer size exceeded")
            #             self.buffer = ""
            #     else:
            #         self.logger.warning("Invalid message [%s]", data[:40])

        except socket.timeout:
            return False


class Hub(TCPServer):
    """
        The Hub act as a peer to peer network for sharing store channels

        The passed store to this Hub is going to be exposed to other AMI
    """

    def __init__(self, host="127.0.0.1", port=None, subscriptions=None,
                 maxClient=MAX_PEER, store=None, **args):
        if not store:
            raise TypeError("a shared store is mandatory for a Hub")
        args['enable_hub'] = False
        args['is_thread'] = True
        super(Hub, self).__init__(port=port, maxClient=maxClient,
                                  host=host, store=store, **args)

        self.hub_subscriptions = set(subscriptions) if subscriptions else set()
        self.store_subscriptions = set()

        self.signal_seens = set([])
        self.last_outbound = None
        self.last_inbound = None

    def onTimeout(self):
        """ This method is run every self.timeout seconds """
        outbounds = None
        if not self.last_outbound:
            # first outbound processing
            outbounds = self.store.get(JOURNAL_PATH) or []
        else:
            outbounds = self.store.getSince(JOURNAL_PATH,
                                            self.last_outbound)

        # TODO: do filtering based on signal.data.metadata.path
        for outbound in outbounds:
            self.last_outbound = outbound

            if not B.is_block(outbound) or not B.is_valid(outbound):
                self.fail("Not a block: %s", outbound)
                raise TypeError()

            path = outbound[B.METADATA]['path']
            if path.split('.')[0].endswith('_'):
                self.logger.debug("skipping block path %s", path)
                continue

            signal = Signal.parse(outbound)
            if not isinstance(signal, Signal):
                signal = Signal(data=B.serialize(outbound), channel="X")
            self.emit(signal)

        # Inbound processing
        inbounds = None
        if not self.last_inbound:
            inbounds = self.store.get(INBOUND_PATH) or []
        else:
            inbounds = self.store.getSince(INBOUND_PATH, self.last_inbound)

        for signal in inbounds:
            signal = Signal.parse(signal)

            if not isinstance(signal, Signal):
                self.fail("Not a signal: %s", signal)
                raise TypeError()

            self.last_inbound = signal
            # ignore exact duplicated signal
            if signal.id in self.signal_seens:
                continue

            #TODO: truncate self.signal_seens to last 10000
            self.signal_seens.add(signal.id)
            if self.hub_subscriptions.intersection(set(signal.channel)):
                self.store.processBlock(signal.data)

            # reemmit:
            # find a way to avoid sent message to be re-broadcasted
            # by every node
            # Potential solution: use channel for tagging networks - groups
            # of peers!

    def createClientThread(self, clientSocket, ip):
        client = HubClient(clientSocket=clientSocket, ip=ip, store=self.store)
        return client, {}

    def emit(self, signal):
        if not isinstance(signal, Signal):
            self.fail("signal to emit must be of type Signal, not [%s]" %
                      signal)
            return False
        if signal.id in self.signal_seens:
            self.logger.debug("already seen signal [%s], preventing re-emit",
                              signal.id)
            return False

        self.signal_seens.add(signal.id)
        self.store.add(OUBOUND_PATH, signal.bytes())

    def addStorePath(self, path):
        self.store_subscriptions.add(path)

    def addHubChannel(self, channel):
        self.hub_subscriptions.add(channel)

    # def addCallback(self, callback, subscription_labels):
    #     if type(subscription_labels) != list:
    #         raise ValueError("Must be list")

    #     for label in subscription_labels:
    #         if label not in self.subscriptions:
    #             self.subscriptions[label] = []
    #         if callback in self.subscriptions[label]:
    #             raise ValueError("callback is already registered")
    #         self.subscriptions[label].append(callback)
