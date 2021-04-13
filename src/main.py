import signal
import sys

from CASlibrary import Config, Logger, RedisMB

from inputListener import InputListener


class Brain:
    input_thread = None

    def __init__(self):
        self.logger = Logger.Logger(self.__class__.__name__).getLogger()
        self.config = Config.Config().getConfig()
        self.redisMB = RedisMB.RedisMB()

        signal.signal(signal.SIGTERM, self.signalhandler)
        signal.signal(signal.SIGHUP, self.signalhandler)

    def signalhandler(self, signum):
        self.logger.info("Signal handler called with signal {}".format(signum))

        self.redisMB.exit()
        self.logger.notice("exiting...")
        sys.exit()

    def main(self):
        self.input_thread = self.redisMB.subscribeToType('input', InputListener().handleInput, daemon=True)
        try:
            self.input_thread.join()
        except (KeyboardInterrupt, SystemExit):
            self.signalhandler("KeyboardInterrupt")


if __name__ == "__main__":
    c = Brain()
    c.main()
