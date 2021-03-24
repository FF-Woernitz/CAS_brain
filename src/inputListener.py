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
            self._handleZVEI(data)

    def _handleZVEI(self, data):
        zvei = data["message"]["data"]
        self.logger.info("Received new ZVEI: " + zvei)
        triggers = []
        for trigger in self.config["trigger"]:
            if "zvei" in trigger:
                if zvei == trigger["zvei"]:
                    triggers.append(trigger)
        if len(triggers) == 0:
            self.logger.info("ZVEI does not match to any trigger. Stopping.")
            return

        actions = []
        for trigger in triggers:
            if not self._isTriggerActive(trigger):
                self.logger.info("Trigger {} is not active", trigger["name"])
                continue
            if "action" not in trigger or len(trigger["action"]) == 0:
                self.logger.info("Trigger {} has no actions", trigger["name"])
                continue
            self.logger.info("Adding actions of trigger {} to queue", trigger["name"])
            for action in trigger["action"]:
                if action not in actions:
                    self.logger.debug("Adding action {} of trigger {} to queue", action, trigger["name"])
                    actions.append(action)
                else:
                    self.logger.debug("Omit action {} of trigger {} as it is already in queue", action, trigger["name"])


    def _isTriggerActive(self, trigger):
        pass



