import unittest
from sthreads.NetworkWatcher import NetworkWatcher


class TestNetworkWatcher(unittest.TestCase):

    def test_dns(self):
        (success, rate, errors) = NetworkWatcher().test_dns()
        assert(success is True)
        assert(rate == 1.0)
        assert(len(errors) == 0)

    def test_dns_fail(self):
        hosts = [
            'google.comcom',
            'google.com'
        ]
        (success, rate, errors) = NetworkWatcher().test_dns(hosts)
        assert(success is False)
        assert(rate == 0.5)
        assert(len(errors) == 1)

    def test_ports(self):
        (success, rate, errors) = NetworkWatcher().test_port()
        assert(success is True)
        assert(rate == 1.0)
        assert(len(errors) == 0)

    def test_ports_fail(self):
        hosts = [
            ('google.comcom', [2]),
            ('google.com', [443])
        ]
        (success, rate, errors) = NetworkWatcher().test_port(hosts)
        assert(success is False)
        assert(rate == 0.5)
        assert(len(errors) == 1)
