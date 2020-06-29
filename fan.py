from pyHS100 import SmartPlug
from threading import Timer

HEAT_ON = "1"
HEAT_OFF = "0"


class Fan:
    FAN_OFF_DELAY = 500.0

    def __init__(self, fan_ip, logger):
        self.logger = logger
        self.state = False
        self.changing = False
        self.fan_ip = fan_ip
        self.plug = SmartPlug(self.fan_ip)

    def fan_off(self):
        try:
            if self.plug.is_on:
                self.plug.turn_off()
        except Exception:
            self.logger.warning("Outlet is down")
        self.logger.info("Turned fan off")
        self.changing = False

    def should_be(self, heat):
        if heat == HEAT_ON:
            self.logger.info("Turned fan on")
            try:
                if self.plug.is_off:
                    self.plug.turn_on()
            except Exception:
                self.logger.warning("Outlet is down")
            self.logger.info("Turned fan off")
            self.state = True
        if heat == HEAT_OFF and self.changing is False:
            self.logger.info("Turning fan off")
            self.changing = True
            Timer(self.FAN_OFF_DELAY, self.fan_off).start()
