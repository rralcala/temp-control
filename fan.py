import logging
from pyHS100 import SmartBulb, SmartPlug
from threading import Timer

class Fan:
    FAN_OFF_DELAY = 400.0

    def __init__(self, fan_ip, logger):
        self.logger = logger
        self.state = False
        self.changing = False
        self.fan_ip = fan_ip
        plug = SmartPlug(self.fan_ip)
        plug.turn_off()

    def fan_off(self):
        if self.state == True:
            plug = SmartPlug(self.fan_ip)
            plug.turn_off()
            self.logger.info("Turned fan off")
            self.state = False
            self.changing = False

    def should_be(self, heat):
        self.logger.debug(f"Want:{heat} State:{self.state} Changing:{self.changing}")
        if heat == "1" and self.state == False:
            self.logger.info("Turned fan on")
            SmartPlug(self.fan_ip).turn_on()
            self.state = True
        if heat == "0" and self.state == True and self.changing == False:
            self.logger.info("Turning fan off")
            self.changing = True
            Timer(self.FAN_OFF_DELAY, self.fan_off).start()
