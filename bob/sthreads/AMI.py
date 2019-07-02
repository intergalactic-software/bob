from time import sleep
from store.Store import Store
import logging
from time import time
import os
import sys
import traceback
from threading import Thread

# states
FAILED = -2
INIT = -1
STOPPED = 0
STOPPING = 1
FORCE_STOPPING = 2
STARTING = 3
RUNNING = 4


STATES = {
    INIT: "init",
    STOPPED: "stopped",
    STOPPING: "stopping",
    FORCE_STOPPING: "force_stopping",
    STARTING: "starting",
    RUNNING: "running",
    FAILED: "failed"
}

COMMANDS = "__AMI__.commands"  # commands for the AMI
HISTORY = "__AMI__.states"      # history of AMI state
LOGS = "__AMI__.logs"          # append logs


class AMI(object):
    """
    Abstract Processing node

    External API:
        * start()
        * stop()

    Life cycle:
        * start()
        *     -> status=STARTING -> onStart() -> status=STARTED -> onInterval()
        * stop() # Can only be called from this instance
        *     -> status=STOPPING -> onStop()  -> status=STOPPED

    Overwrite any/all of the following:
        * __init__(): call super and accept arguments
        * onStart(): initialization
        * onStop(): cleanup
        * onInterval(): execute every x ms

    onInterval():
        in onStart() or __init__() if the self.interval is not defined, then
        this method will only be executed once. Otherwise, this method will be
        excecuted every [self.interval] milliseconds.

    Store: self.store is a substore
    """

    def __init__(self, tag=None, store=None, interval=None,
                 enable_hub=True, is_thread=False, **args):
        self.TAG = tag or ''
        self.ID = str(hash(time()))[-5:]
        self.TAG += self.ID
        self.HISTORY_PATH = HISTORY + self.ID
        self.store = store if store else Store()
        self.interval = interval
        self.logger = logging.getLogger(str(self))
        from sthreads.Hub import Hub
        self.hub = Hub(store=self.store) if enable_hub else None
        self.is_thread = is_thread
        self.setState(INIT)

    def onStart(self):
        pass

    def onInterval(self):
        raise NotImplementedError()

    def onStop(self):
        pass

    def stop(self):
        """ Stops the AMI completely, should not be overwritten

        An external call to this method will not stop this AMI.
        """
        if self.getState() not in [RUNNING, FORCE_STOPPING, FAILED]:
            self.logger.debug("Can not stop [%s]" % self.getState())
            return
        try:
            self.setState(STOPPING)
            self.onStop()  # TODO: add timeout, call self.onStop() in thread
            self.setState(STOPPED)
            if not self.is_thread:
                os._exit(0)  # exit without error
        except Exception:
            self.logger.error("Exception while running onStop()")
            print(sys.exc_info())  # push onto Store on top of STDOUT
            print(traceback.print_exc())
            if not self.is_thread:
                os._exit(1)

    def start(self):

        if self.is_thread:
            """ Starts this AMI in a thread with shared memory """
            thread = Thread(target=self.__start)
            thread.start()
        else:
            """ Starts this AMI in a new process and
            returns the unique node_id """
            pid = os.fork()
            if pid:
                # parent process
                return self.TAG
            else:
                # AMI process
                self.__start()

    def __start(self):
        self.setState(STARTING)
        if self.hub is not None:
            self.hub.store = self.store
            self.hub.start()
        self.onStart()
        if self.getState() == STARTING:
            self.setState(RUNNING)
            try:
                while self.getState() == RUNNING:
                    self.onInterval()
                    if self.interval:
                        # at interval execution
                        sleep(self.interval or 0)
                    else:
                        # single execution
                        break
            except Exception:
                (_, err, trace) = sys.exc_info()
                stack_trace = traceback.extract_tb(trace)
                self.logger.error("AMI failed: %s: %s", err, stack_trace)
                self.setState(FAILED)

        self.stop()

    def setState(self, newState):
        if newState not in STATES:
            raise ValueError("Invalid state [%s]" % newState)
        self.store.add(self.HISTORY_PATH, newState)
        self.logger.debug("State change to [%s]", STATES[newState])

    def getState(self):
        return self.store.getLasts(self.HISTORY_PATH, 1)[0]

    def __repr__(self):
        return "[AMI.%s.%s]" % (self.__class__.__name__, self.TAG)

    def fail(self, *args):
        self.logger.error(*args)
        self.setState(FAILED)
