import blockchain.blockutil_U as B

MAX_PATH_LENGTH = 10
KILL_VALUE = "__KILL__"
READ_VALUE = "__READ__"
FLAGS = [KILL_VALUE, READ_VALUE]
ADD_METHOD = "add"
PUT_METHOD = "put"
JOURNAL_PATH = "__JOURNAL__"


class StoreData(object):
    """
        Actual dictionary store for the store, this allows
        the store to be branched by allowing 'by reference' passing
        of substores.
    """
    def __init__(self, data):
        self.data = data

    def get(self):
        return self.data

    def __repr__(self):
        return str(self.data)


class Store(object):
    """ This is a dictionnary with a few additions

    Path are channels
    All path entries are list
    .add(path, value) -> create list or append
    .get(path, filter) -> get filtered list, filter is executed on store
    .getLast(path, maxCount) -> get the last X items
    .getSince(path, lastItem) -> get all items since lastItem

    Additions:
        * support multiple deepness of storage
        * execute UNSECURED actions to update itself
        * easy path traversal

    TODO:
        * add channel with permissions?
        * add symetric encryption per "block" in add(),put()...
    """

    def __init__(self):
        self.data = StoreData({})

    def processBlock(self, signal_data):
        block = B.deserialize(signal_data)

        method = block[B.METADATA]['method']
        path = block[B.METADATA]['path']
        data = block[B.DATA]

        if method == ADD_METHOD:
            self.add(path, data)
        elif method == PUT_METHOD:
            self.put(path, data)
        else:
            raise ValueError("unknown method [%s], block: %s",
                             method, block[B.HASH])

    def get(self, path, filter_func=None):
        """return the value stored on this path (if any)"""
        values = self.__updatePath(path)
        if filter_func:
            values = filter(filter_func, values)
        return values

    def getObj(self, path):
        value = self.get(path)
        if type(value) == list and len(value) == 1:
            return value[0]
        else:
            raise ValueError(
                "Value at path [%s] is not a single object", path)

    def getLasts(self, path, max_count):
        values = self.get(path)
        return values[-1 * (min(len(values), max_count)):]

    def getSince(self, path, last_value=None):
        values = self.get(path)
        for pos, value in enumerate(values):
            if value == last_value:
                return values[pos+1:]
        raise ValueError("Unknown last_value %s", last_value)

    def addAll(self, path, values):
        if not isinstance(values, list):
            raise TypeError("Values must be a list")
        for value in values:
            self.add(path, value)

    def add(self, path, value):
        values = self.get(path) + [value] if self.get(path) else [value]
        self.put(path, values, journal=False)
        self._onUpdate(ADD_METHOD, path, value)

    def put(self, path, value, journal=True):
        value_adjusted = value
        if type(value) != list and value not in FLAGS:
            value_adjusted = [value_adjusted]

        # failsafe, eg when value = KILL_VALUE
        if self.__updatePath(path, value_adjusted) != value_adjusted:
            raise RuntimeError(
                "Could not write at path [%s]: %s", path, value_adjusted)

        # journal
        if journal:
            self._onUpdate(PUT_METHOD, path, value_adjusted)

    def clear(self, path):
        self.put(path, KILL_VALUE)

    def _onUpdate(self, method, path, data):
        if path == JOURNAL_PATH:
            return
        metadata = {
            "method": method,
            "path": path
        }
        block = B.create("store", data, metadata)
        self.add(JOURNAL_PATH, block)

    def __updatePath(self, path, value=READ_VALUE):
        """ Read or Write to the store

        2 modes:
        Write mode: [set value] creates the path (if needed) and set the value
        Read mode: [no value] returns the data at path or None
        """
        if type(path) != str:
            raise ValueError("Path is not a string: %s" % path)

        if value not in FLAGS:
            if type(value) != list or len(value) == 0:
                raise TypeError("values must be a non-empty list")

        parts = path.split('.')
        if len(parts) == 0 or len(parts) > MAX_PATH_LENGTH:
            raise ValueError("Path length is %d, but should be within [1,%d]" %
                             (len(parts), MAX_PATH_LENGTH))

        cell = self.data.get()
        while len(parts) > 1:
            if parts[0] not in cell:
                cell[parts[0]] = {}

            cell = cell[parts[0]]
            parts = parts[1:]

        if value == KILL_VALUE:
            if parts[0] in cell:
                del cell[parts[0]]
                return KILL_VALUE
            return None
        elif value == READ_VALUE:
            return cell[parts[0]] if parts[0] in cell else None
        else:
            cell[parts[0]] = value
            return value

    def __repr__(self):
        return str(self.data.get())
