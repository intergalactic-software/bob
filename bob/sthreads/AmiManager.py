from AMI import AMI, STOPPED
import time


class AmiManager(AMI):

    def __init__(self, **args):
        self.AMIs = {}  # Map<TAG,AMI>
        super(AmiManager, self).__init__(interval=0.1, **args)

    def onInterval(self):
        self.__cleanDeadThreads()

    def onStop(self):
        threadNames = self.AMIs.keys()
        for name in threadNames:
            self.stopThread(name)

    def add(self, thread):
        if isinstance(thread, AMI) is False:
            raise TypeError("thread must be a AMI not [%s]" % type(thread))

        if thread.TAG in self.AMIs:
            raise ValueError(
                "thread [%s] already in this AmiManager" % thread.TAG)

        self.logger.debug("Added thread %s with TAG=%s", thread, thread.TAG)
        self.AMIs[thread.TAG] = thread

    def has(self, name):
        return name in self.AMIs

    def get(self, name):
        if name not in self.AMIs:
            raise ValueError(
                "thread [%s] is not in AmiManager" % name)
        return self.AMIs[name]

    def __remove(self, name):
        if name not in self.AMIs:
            raise ValueError(
                "thread [%s] is not in AmiManager" % name)
        del self.AMIs[name]

    def stopThread(self, name):
        node = self.get(name)

        #write AMI comand to the store

        #wain until paused
        timout = 5  # seconds
        started_at = time.time()
        # read store for AMI
        while False and (time.time() - started_at) < timout:
            time.sleep(0.1)
        if False:
            self.logger.error("can not stop thread [%s] after 5 secs", name)

        self.__remove(name)

    def startThread(self, name):
        thread = self.get(name)
        if thread.isAlive():
            self.logger.error("thread [%s] is already started", name)
            return
        thread.start()

    def __cleanDeadThreads(self):
        deads = [name for (name, thread) in self.AMIs.items()
                 if thread.isAlive() is False]
        for name in deads:
            self.AMIs.pop(name)
            self.logger.debug("thread is dead: %s", name)