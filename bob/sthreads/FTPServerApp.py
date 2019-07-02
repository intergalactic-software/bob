import time
import datetime
import logging
import socket
import random
from sthreads.AMI import AMI, FORCE_STOPPING

# Pure-FTPd banner
BANNER = "" \
        "220---------- Welcome to Pure-FTPd [privsep] [TLS] ----------\r\n" \
        "220-You are user number 1 of 2 allowed.\r\n"\
        "220-Local time is now %s. Server port: 21\r\n"\
        "220-This is a private system - No anonymous login\r\n"\
        "220 You will be disconnected after 15 minutes of inactivity.\r\n" \
        ""


class FTPServerApp(AMI):
    def __init__(self, clientSocket=None, ip=None, **args):
        super(FTPServerApp, self).__init__(tag="FTP %s" % ip, interval=0.1,
                                           **args)
        self.clientSocket = clientSocket
        self.ip = ip
        self.min_timeout = 1
        self.max_timeout = 4

    def onStart(self):
        now = datetime.datetime.now().strftime('%H:%M').encode()
        banner = BANNER % now
        self.clientSocket.send(banner.encode())
        logging.debug("%s: Sent FTP banner", self.TAG)

    def onInterval(self):
        try:
            cmd = self.clientSocket.recv(1024)
            cmd_str = cmd[:-1]  # dangerous in case a byte can't be a character

            # tiny sleep to simulate processing
            time.sleep(random.randint(self.min_timeout, self.max_timeout) / 10)

            logging.debug("%s: Received: %s", self.TAG, str(cmd_str))

            if cmd_str.startswith(b"user ") and len(cmd_str) > 5:
                self.clientSocket.send(b"331 User " + 
                                       cmd_str[5:] +
                                       b" OK. Password required\r\n")

            elif cmd_str.startswith(b"pass ") and len(cmd_str) > 5:
                logging.info("%s: attempted password: %s", self.TAG,
                             str(cmd_str[5:]))
                # prevents brute force
                time.sleep(random.randint(self.min_timeout, self.max_timeout))
                self.clientSocket.send(
                    b"530 Login authentication failed\r\n")

            elif cmd_str.startswith(b"exit"):
                self.setState(FORCE_STOPPING)

            else:
                self.clientSocket.send(b'530 You aren\'t logged in\r\n')
        except socket.timeout:
            pass

    def onStop(self):
        self.clientSocket.shutdown(socket.SHUT_RDWR)
        self.clientSocket.close()
        logging.info("%s: Force disconected", self.TAG)
