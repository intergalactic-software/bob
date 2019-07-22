import bob.blockchain.blockutil_U as BLK

import socket
import getpass
import netifaces
import logging

"""
Peer to peer network for transmitting BLK
The network wraps BLK with metadata related
to the network called packet
"""

BLK_TYPE_DATA = "data"
BLK_TYPE_SIGNAL = "signal"
BLK_TYPES = [BLK_TYPE_DATA, BLK_TYPE_SIGNAL]


def GetPortsForHost(ip):
    """Returns ports in range 20000-30000

    The ports returned are deterministics by ip, expect same ports
    per ip and potentially different ports for different ips.
    Only the last byte of the ip is used.
    """
    parts = [int(i) for i in ip.split('.')]
    offset = 20000 + parts[-1] * 7
    interval = (13 + parts[-2] + parts[-3]) % 42
    return range(offset, 30000, interval)[:10]


def GetIps():
    """Returns list of eth/wlan ips of this host"""
    ifs = [i for i in netifaces.interfaces()
           if len(i) > 3 and i[:3] in ['eth', 'wla', 'enp']]

    ips_active = [netifaces.ifaddresses(i)[netifaces.AF_INET][0]['addr']
                  for i in ifs
                  if netifaces.AF_INET in netifaces.ifaddresses(i)]
    return ips_active


def GetNodeId(ip, port):
    """Return str identifier of this host-port pair"""
    if type(port) != int or port <= 0 or port > 65365:
        raise ValueError("Invalid port [%s]", repr(port))

    user = getpass.getuser()
    if type(user) != str or len(user) < 2:
        logging.warn("invalid username")

    return "%s@%s:%d" % (user, ip, port)


def ProcessDestination(destinations, node_id):
    """Return destination without current node"""
    if destinations in ["ALL", node_id]:
        return (True, [])
    if node_id in destinations:
        return (True, [i for i in destinations if i != node_id])
    return (False, destinations)


class PacketBuilder:

    def __init__(self):
        self.dict = {}

    def setDestination(self, destinations):
        if type(destinations) not in [str, list]:
            raise ValueError("Invalid destinations type [%s]", 
                             destinations)
        self.dict["dest"] = destinations

    def setAsData(self, data, channel):
        self.dict['type'] = BLK_TYPE_DATA
        self.dict['data_blk'] = data
        self.dict['channel'] = data

    def setAsSignal(self, id, meta):
        self.dict['type'] = BLK_TYPE_SIGNAL
        self.dict['signal_id'] = id
        self.dict['signal_blk'] = meta

    def setSource(self, node_id):
        self.dict['source'] = node_id

    def build(self):
        self.dict['sign'] = "0x000000"
        return self.dict
