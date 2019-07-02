import socket
from sthreads.AMI import AMI

# hosts that accept PING, SSH, HTTPS
TRUSTED_HOSTS = [
    ('google.com', [80, 443]),
    ('github.com', [22, 80, 443]),
    ('bitbucket.com', [22, 443]),
]

DNS_PATH = "dns"
PORT_PATH = "ports"


class NetworkWatcher(AMI):

    def __init__(self, interval=5, **args):
        super(NetworkWatcher, self).__init__(interval=interval, **args)
        self.results = None

    def onInterval(self):
        self.store.add(DNS_PATH, self.test_dns())
        self.store.add(PORT_PATH, self.test_port())

    def test_dns(self, hosts=None):
        if hosts is None:
            hosts = map(lambda h: h[0], TRUSTED_HOSTS)
        elif type(hosts) != list:
            self.logger.error("Invalid hosts [%s]", hosts)
            return None

        results = []
        for host in hosts:
            try:
                ip = socket.gethostbyname(host)
                results.append({"success": (ip is not None), "error": None})
            except socket.gaierror as e:
                error = "[%s]: [%s]" % (host, e)
                self.logger.warning('DNS problem with %s', error)
                results.append({"success": False, "error": e})

        succeeded = list(filter(lambda r: r['success'], results))
        errors = list(filter(lambda r: r['success'] is False, results))
        success_rate = len(succeeded) * 1.0 / len(results)

        return (success_rate == 1.0, success_rate, errors)

    def test_port(self, hosts=None):
        if hosts is None:
            hosts = TRUSTED_HOSTS
        elif hosts is not None and type(hosts) != list:
            self.logger.error("Invalid hosts [%s]", hosts)
            return None

        results = []
        for (host, ports) in hosts:

            for port in ports:
                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.connect((host, port))
                    s.close()
                    results.append({"success": True, "error": None})
                except socket.error as e:
                    error = "%s:%d: %s" % (host, port, e)
                    self.logger.warning('TCP Port problem with %s', error)
                    results.append({"success": False, "error": error})

        succeeded = list(filter(lambda r: r['success'], results))
        errors = list(filter(lambda r: r['success'] is False, results))
        success_rate = len(succeeded) * 1.0 / len(results)

        return (success_rate == 1.0, success_rate, errors)
