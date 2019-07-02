import unittest
from sthreads.AMI import AMI, STOPPED, STARTING, RUNNING, INIT, STOPPING, FORCE_STOPPING, FAILED
from store.MockStore import MockStore, DATA
import time
import logging
import json

logging.basicConfig(level=logging.DEBUG)

STATE_SEQUENCE = [INIT, STARTING, RUNNING, STOPPING, STOPPED]
FAILED_RUN_SEQUENCE = [INIT, STARTING, RUNNING, FAILED, STOPPING, STOPPED]
FAILED_START_SEQUENCE = [INIT, STARTING, FAILED, STOPPING, STOPPED]


class DummyAMI(AMI):
    def onStart(self):
        time.sleep(0.05)

    def onInterval(self):
        time.sleep(0.05)

    def onStop(self):
        time.sleep(0.05)


class Util:
    @staticmethod
    def run(ami, run_callback=None,
            start_timeout=0.3, stop_timeout=0.3):
        """ AMI synchronous start/stop with run_callback run once started """
        if not isinstance(ami.store, MockStore):
            raise TypeError("AMI's store must be a MockStore")
        if run_callback and not ami.interval:
            raise ValueError("run_callback is only used with interval AMI")

        filename = ami.store.mock_with_file(ami.HISTORY_PATH)

        ami.start()
        Util.waitForState(ami, [RUNNING, STOPPED], start_timeout)

        # Force stops AMI if there is an interval
        if ami.interval:
            if run_callback:
                run_callback(ami)
            with open(filename, "w") as file:
                file.write(json.dumps([FORCE_STOPPING]))

        Util.waitForState(ami, [STOPPED], stop_timeout)

        return ami

    @staticmethod
    def getStates(ami):
        if not isinstance(ami.store, MockStore):
            raise TypeError("AMI's store must be a MockStore")
        logs = ami.store.getLogs(ami.HISTORY_PATH)
        return [int(log[DATA]) for log in logs]

    @staticmethod
    def waitForState(ami, states, timeout):
        if not isinstance(states, list):
            raise TypeError()
        time_waited = 0
        while Util.getStates(ami)[-1] not in states and time_waited < timeout:
            time_waited += 0.1
            time.sleep(0.1)

        if time_waited >= timeout:
            raise RuntimeError("Timeout waiting for states=%s, current state=%s"
                               % (states, Util.getStates(ami)))

class TestAMI(unittest.TestCase):
    def test_startStop_single_thread_noHub(self):
        ami = DummyAMI(enable_hub=False, is_thread=True, store=MockStore())
        self.assertEqual(Util.getStates(Util.run(ami)), STATE_SEQUENCE)

    def test_startStop_loop_thread_noHub(self):
        ami = DummyAMI(enable_hub=False, is_thread=True,
                       store=MockStore(), interval=0.01)
        self.assertEqual(Util.getStates(Util.run(ami)), STATE_SEQUENCE)

    def test_startStop_single_process_noHub(self):
        ami = DummyAMI(enable_hub=False, is_thread=False, store=MockStore())
        self.assertEqual(Util.getStates(Util.run(ami)), STATE_SEQUENCE)

    def test_startStop_loop_process_noHub(self):
        ami = DummyAMI(enable_hub=False, is_thread=False,
                       store=MockStore(), interval=0.01)
        self.assertEqual(Util.getStates(Util.run(ami)), STATE_SEQUENCE)
