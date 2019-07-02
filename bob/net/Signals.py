import uuid
import json

SIGNAL_START = "<BOB"
SIGNAL_END = "BOB>"
VERSION = "0.11"

ENCODE = "encode"
DECODE = "decode"

SEPARATOR = ")--(".encode('utf8')


# TODO: add support: for encryption, for host,service
class Signal(object):
    """ Blob to be sent over tcp/udp

    Attributes:
        type: string representing the type
        bytes: binary payload TODO: set type
        id: UUID string, automatically generated
    """

    def __init__(self, id=None, channel=None, data=None, metadata=None):
        if data is None or channel is None:
            raise ValueError("channel and data are required for Signal")

        if isinstance(channel, str):
            channel = [channel]

        if not isinstance(channel, list) or len(channel) == 0:
            raise TypeError("channel must be non-empty list of strings")

        if not isinstance(data, bytes):
            raise TypeError("Data must be bytes, not [%s]" % type(data))

        self.id = id or uuid.uuid4().bytes  # 16 bytes
        self.data = data
        self.channel = channel
        self.metadata = None  # unused

    @staticmethod
    def parse(data):
        if type(data) != bytes:
            return -1
        if data[:len(SIGNAL_START)].decode() != SIGNAL_START:
            return -2
        if data[-1 * len(SIGNAL_END):].decode() != SIGNAL_END:
            return -3

        trimmed = data[len(SIGNAL_START):-len(SIGNAL_END)]
        parts = [p for p in trimmed.split(SEPARATOR) if p]  # remove empty start/end
        if len(parts) != 4:
            return -4
        if parts[0].decode() != VERSION:  # TODO: add more flexible versionning
            return -5
        if len(parts[1]) != 16:
            return -6
        return Signal(id=parts[1], channel=json.loads(parts[2].decode()),
                      data=parts[3])

    def bytes(self):
        packet_parts = [SIGNAL_START,
                        VERSION,
                        self.id,
                        json.dumps(self.channel),
                        self.data,
                        SIGNAL_END]
        return SEPARATOR.join([part if isinstance(part, bytes) else part.encode('utf-8')
                               for part in packet_parts])

    def __repr__(self):
        raise NotImplementedError("This operation is not supported")

    def __eq__(self, other):
        # return other is not None and self.id == other.id
        if other is None or not isinstance(other, Signal):
            return TypeError("Not a signal [%s]" % other)

        return self.bytes() == other.bytes()

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return self.id
