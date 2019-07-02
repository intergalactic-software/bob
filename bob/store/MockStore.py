from store.Store import Store
import tempfile
import json

TYPE = "type"
PATH = "path"
DATA = "data"

SEPARATOR = "*+*_*"
LINE_SEPARATOR = "%^U]\n["

class MockStore(Store):
    """ Store for testing

    This store use local file storage to store logs. Thus it works
    across processes and threads but not accross machines.

    Refer to tests/test_mockStore.py for usage examples
    """
    def __init__(self):
        super(MockStore, self).__init__()
        self.mocks = {}
        file = tempfile.NamedTemporaryFile(delete=False)
        self.filename = file.name
        file.close()

    def mock_with_value(self, path, return_value, ):
        """ Mock data in store with static value """
        self.mocks[path] = lambda path: return_value

    def mock_with_file(self, path, filename=None, json_content=None):
        if filename is None:
            file = tempfile.NamedTemporaryFile(mode='w', delete=False)
            filename = file.name
            if json:
                file.write(json.dumps(json_content))
            file.close()

        """ Mock data in store with values from a file """
        self.mocks[path] = lambda path: self.__readFile(filename)
        return filename

    def getLogs(self, path=None):
        """ Return all write operations that occured on this store """
        logs = []
        with open(self.filename) as file:
            lines = file.read().split(LINE_SEPARATOR)
            lines_splitted = [line.split(SEPARATOR) for line in lines if line]
            logs = [{
                TYPE: line[0],
                PATH: line[1],
                DATA: line[2]
            } for line in lines_splitted]
            logs = [log for log in logs if not path or path in log[PATH]]
        return logs

    def get(self, path):
        """ (Overide) Support mocked data """
        mocked_data = None
        if path in self.mocks:
            mocked_data = self.mocks[path](path)

        return mocked_data or super(MockStore, self).get(path)

    def _onUpdate(self, method, path, data):
        """ (Overide) Logs any update to output file """
        with open(self.filename, "a") as file:
            data_str = data
            if type(data) not in (str, bytes):
                data_str = repr(data)
            newLine = method + SEPARATOR + path + SEPARATOR + str(data_str)
            file.write(newLine + LINE_SEPARATOR)
        super(MockStore, self)._onUpdate(method, path, data)

    def __readFile(self, filename):
        with open(filename) as file:
            content = file.read()
            if len(content) == 0:
                return None
            else:
                return json.loads(content)
