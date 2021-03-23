from CASlibrary import Config, Logger, RedisMB
from CASlibrary.constants import AlertType


class InputListener:
    def __init__(self):
        self.logger = Logger.Logger(self.__class__.__name__).getLogger()
        self.config = Config.Config().getConfig()
        self.redisMB = RedisMB.RedisMB()
        self.logger.info("__init__")

    def handleInput(self, data):
        self.logger.info("Received new mb message")
        self.logger.debug(self.redisMB.decodeMessage(data))
        try:
            inputType = data["message"]["type"]
        except KeyError:
            self.logger.error("Message does not contain a type")
            self.logger.info(data)
            return
        if inputType == AlertType.ZVEI:
            self.handleZVEI(data)

    def handleZVEI(self, data):
        zvei = data["message"]["data"]
        self.logger.info("Received new ZVEI: " + zvei)
        if "zvei" not in self.config["trigger"]:
            self.logger.info("No ZVEI trigger in config defined")
        trigger = []
        for k, v in self.config["trigger"].items():
            if k == zvei:





