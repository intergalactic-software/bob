from bob.ami import AMI


class Dummy(AMI):

    def __init__(self, **args):
        super(Dummy, self).__init__(interval=2, **args)

    def onStart(self):
        self.logger.warning("onStart()")

    def onInterval(self):
        self.logger.warning("onInterval()")

    def onStop(self):
        self.logger.warning("onStop()")
