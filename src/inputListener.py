from datetime import datetime, time as dtime

from CASlibrary import Config, Logger, RedisMB
from CASlibrary.constants import AlertType
from pytz import timezone


class InputListener:
    def __init__(self):
        self.logger = Logger.Logger(self.__class__.__name__).getLogger()
        self.config = Config.Config().getConfig()
        self.redisMB = RedisMB.RedisMB()

    def handleInput(self, data):
        self.logger.info("Received new mb message")
        data = self.redisMB.decodeMessage(data)
        self.logger.debug(data)
        try:
            inputType = data["message"]["type"]
        except KeyError:
            self.logger.error("Message does not contain a type")
            self.logger.info(data)
            return
        actions = {}
        if inputType == AlertType.ZVEI:
            actions = self._handleZVEI(data)
        elif inputType == AlertType.FAX:
            # TODO
            self.logger.warn("Fax triggers are not finished yet")
        elif inputType == AlertType.SDS:
            # TODO
            self.logger.warn("SDS triggers are not finished yet")
        else:
            self.logger.warn("Input type {} does not match to any alert type".format(inputType))
            return
        if actions and len(actions) > 0:
            self._notifyActions(actions)

    def _notifyActions(self, actions):
        for action, action_data in actions.items():
            self.logger.info("Sending action {} to queue".format(action))
            self.redisMB.action(action, action_data)

    def _handleZVEI(self, data):
        zvei = data["message"]["data"]
        self.logger.info("Received new ZVEI: " + zvei)
        triggers = []
        for trigger in self.config["trigger"]:
            if "zvei" in trigger:
                if zvei == trigger["zvei"]:
                    self.logger.info("ZVEI does match to trigger {}.".format(trigger["name"]))
                    triggers.append(trigger)
        if len(triggers) == 0:
            self.logger.info("ZVEI does not match to any trigger. Stopping.")
            return False

        actions = {}
        for trigger in triggers:
            if not self._isTriggerActive(trigger):
                self.logger.info("Trigger {} is not active".format(trigger["name"]))
                continue
            if "action" not in trigger or len(trigger["action"]) == 0:
                self.logger.info("Trigger {} has no actions".format(trigger["name"]))
                continue

            action_data = {"trigger_name": trigger["name"], "zvei": zvei}
            self.logger.info("Adding actions of trigger {} to queue".format(trigger["name"]))
            for action in trigger["action"]:
                if action not in actions:
                    self.logger.debug("Adding action {} of trigger {} to queue".format(action, trigger["name"]))
                    actions[action] = action_data
                else:
                    self.logger.debug(
                        "Omit action {} of trigger {} as it is already in queue".format(action, trigger["name"]))
        return actions

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
                    ok = True
                    for k, v in d.items():
                        self.logger.debug(
                            "Trigger {}: Dict: Checking key {} value {} of type {}".format(name, k, v, type(d)))
                        if k == "weekday":
                            if v == now.weekday():
                                continue
                            else:
                                ok = False
                                break
                        elif k == "between":
                            begin_time = dtime(v[0][0], v[0][1])
                            end_time = dtime(v[1][0], v[1][1])
                            if begin_time < now.time() < end_time:
                                continue
                            else:
                                ok = False
                                break
                        else:
                            self.logger.warning(
                                "Trigger {}: Found unknown key {} with value {} in active of trigger".format(name, k,
                                                                                                             v))
                    if ok:
                        return True
                else:
                    self.logger.warning(
                        "Trigger {}: Found unknown type {} with value {} in active of trigger".format(name, type(d), d))
            return False

        self.logger.debug("Check if trigger {} is active".format(trigger["name"]))
        if "active" not in trigger:
            if "inactive" not in trigger:
                self.logger.debug(
                    "Trigger {} has no active nor inactive key in config. So it's active".format(trigger["name"]))
                return True
            return not _isActiveTimeNow(trigger["inactive"], trigger["name"])
        else:
            return _isActiveTimeNow(trigger["active"], trigger["name"])
