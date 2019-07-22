import socket
from bob.ami import AMI, FORCE_STOPPING, RUNNING
import random
import time
# if 'sthreads.AMI' not in sys.modules:
#     from sthreads.AMI import AMI
# else:
#     AMI = sys.modules['sthreads.AMI']


SOCKET = "socket"
THREAD = "thread"
META = "meta"
CLIENT_KEYS = [SOCKET, THREAD, META]

CLIENTS_STORE_PATH = "_clients_"


class TCPServer(AMI):
    """
    This TCP server should be subclassed

    Arguments:
        app: client thread AMI that takes two parameters clientSocket and ip
        host: ip to bind the listening socket to
        port: port to bind the listening socket to
        maxClient: max number of client waiting for the listen socket
        timeout: interval in between listen timeout, this defines
                 the time interval between calls to self.onTimeout and
                 self.state changes

    Subclasses:
        createClientThread: can be overridden to have custom child
                            thread/processes handling client sockets
        onTimeout: this method is called roughly every [self.timeout] seconds
    """

    def __init__(self, app=None, host="127.0.0.1",
                 port=None, maxClient=2, timeout=0.5, **args):
        super(TCPServer, self).__init__(interval=0.01, **args)

        self.app = app
        self.sock = None
        self.host = host
        self.port = port or random.randint(10000, 50000)
        self.clients = []
        self.maxClient = maxClient
        self.timeout = timeout

    def onStart(self):
        if self.sock is not None:
            self.logger.warning("Server is already started")
            return

        self.clients = {}

        # socket initialization
        self.logger.info("%s: Server is starting %s:%d",
                         self.TAG, self.host, self.port)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.host, self.port))
        self.sock.settimeout(0.1)
        self.sock.listen(self.maxClient)
        self.logger.info("Server is listening (%d)", self.maxClient)

    def onInterval(self):
        # remove dead clients
        self.__cleanDeadClients()
        try:
            # waiting for a client to connect
            (clientSocket, address) = self.sock.accept()
            # starting the client thread
            ip = str(address[0]) + ":" + str(address[1])
            self.logger.info("Client connected: %s", ip)

            clientThread, metadata = self.createClientThread(
                clientSocket=clientSocket, ip=ip)
            clientThread.start()

            # saving the client's socket
            self.clients[ip] = {
                SOCKET: clientSocket,
                THREAD: clientThread,
                META: metadata
            }
            self.store.add(CLIENTS_STORE_PATH, self.clients[ip])

        except socket.timeout:
            self.onTimeout()

    # # Stops the server
    def onStop(self):
        self.logger.info("Stopping server and closing active connections")
        self.sock.close()
        self.logger.info("Closed listening port")

        disconected = 0
        for ip, client in self.clients.items():
            client[THREAD].setState(FORCE_STOPPING)
            disconected += 1

        #TODO: wait until stopped
        time.sleep(0.1)
        self.logger.info("Disconected %d clients", disconected)
        self.clients = []

    def onTimeout(self):
        pass

    def createClientThread(self, clientSocket, ip):
        clientThread = self.app(clientSocket, ip)
        if not isinstance(clientThread, AMI) or not clientThread.is_thread:
            raise TypeError("Client must be a threaded AMI")
        return clientThread, {}

    def __cleanDeadClients(self):
        deadIps = [ip for (ip, obj) in self.clients.items()
                   if obj[THREAD].getState() != RUNNING]
        for ip in deadIps:
            self.clients.pop(ip)
            self.logger.debug("Client is dead: %s", ip)
