from datetime import datetime, time as dtime
from pytz import timezone

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

        actions = {}
        for trigger in triggers:
            if not self._isTriggerActive(trigger):
                self.logger.info("Trigger {} is not active".format(trigger["name"]))
                continue
            if "action" not in trigger or len(trigger["action"]) == 0:
                self.logger.info("Trigger {} has no actions".format(trigger["name"]))
                continue

            template = {"trigger_name": trigger["name"], "zvei": zvei}
            self.logger.info("Adding actions of trigger {} to queue".format(trigger["name"]))
            for action in trigger["action"]:
                if action not in actions:
                    self.logger.debug("Adding action {} of trigger {} to queue".format(action, trigger["name"]))
                    actions[action] = template
                else:
                    self.logger.debug("Omit action {} of trigger {} as it is already in queue".format(action, trigger["name"]))

    def _isTriggerActive(self, trigger):
        def _isActiveTimeNow(data, name):
            now = datetime.now(timezone("Europe/Berlin"))

            if isinstance(data, bool):
                self.logger.debug("Trigger {} active config is bool. Returning it".format(name))
                return data
            for d in data:
                self.logger.debug("Trigger {}: Checking value {} of type {}".format(name, d, type(d)))
                if isinstance(d, bool):
                    self.logger.debug("Trigger {}: Found a bool in the active config. Returning it".format(name))
                    return d
                elif isinstance(d, int):
                    if d == now.weekday():
                        self.logger.debug("Trigger {}: Int does match to the current weekday. Return true".format(name))
                        return True
                elif isinstance(d, dict):
                    if len(d) == 0:
                        self.logger.debug("Trigger {}: Dict is empty. Ignore".format(name))
                        continue
                    for k, v in d.items():
                        if k == "weekday":
                            if v != now.weekday():
                                continue
                        elif k == "between":
                            begin_time = dtime(v[0][0], v[0][1])
                            end_time = dtime(v[1][0], v[1][1])
                            if begin_time > now.time() or now.time() > end_time:
                                continue
                        else:
                            self.logger.warning("Found unknown key {} with value {} in active of trigger".format(k, v))
                    return True
                else:
                    self.logger.warning("Found unknown type {} with value {} in active of trigger".format(name, type(d), d))
            return False

        self.logger.debug("Check if trigger {} is active".format(trigger["name"]))
        inactive = False
        data = []
        if "active" not in trigger:
            if "inactive" not in trigger:
                self.logger.debug("Trigger {} has no active nor inactive key in config. So it es active".format(trigger["name"]))
                return True
            return not _isActiveTimeNow(data, trigger["name"])
        else:
            return _isActiveTimeNow(data, trigger["name"])

    def _isActiveTimeNow(self, data, name):
        now = datetime.now(timezone("Europe/Berlin"))

        if isinstance(data, bool):
            self.logger.debug("Trigger {} active config is bool. Returning it", name)
            return data
        for d in data:
            self.logger.debug("Trigger {}: Checking value {} of type {}", name, d, type(d))
            if isinstance(d, bool):
                self.logger.debug("Trigger {}: Found a bool in the active config. Returning it", name)
                return d
            elif isinstance(d, int):
                if d == now.weekday():
                    self.logger.debug("Trigger {}: Int does match to the current weekday. Return true", name)
                    return True
            elif isinstance(d, dict):
                pass
            else:
                self.logger.warning("Found unknown type {} with value {} in active of trigger", name, type(d), d)
        return False
