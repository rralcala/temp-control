import datetime
import json
import logging
import re
import select
import socket
import time

import mysql.connector
import pytz

import fan
import weather_service


class TempControl:
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger()
        self.fan_outlet = fan.Fan(config["fan"], self.logger)
        self.line = re.compile(r"([0-9]+\.[0-9]+)\s([01])\s([01])")

    def new_data(self, m, dt):
        row = {"temp": m.group(1), "oper": m.group(2), "heat": m.group(3)}
        try:
            row["otemp"] = weather_service.get_temp(self.config["weather"])
        except ValueError:
            row["otemp"] = 0
        row["date"] = dt.strftime("%Y-%m-%d %H:%M")

        return row

    def poll(self):
        data = ""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as temp_source:
            try:
                temp_source.connect(
                    (
                        self.config["temp-control"]["host"],
                        self.config["temp-control"]["port"],
                    )
                )
                temp_source.setblocking(0)
            except Exception as e:
                self.logger.error(e)
                time.sleep(10)
                return
            self.logger.info("Connected to {}".format(config["temp-control"]["host"]))

            last_min = datetime.datetime.now().minute - 1
            while True:
                ready = select.select([temp_source], [], [], 10.0)
                if ready[0]:
                    data += temp_source.recv(1024).decode("utf-8")
                    if not data:
                        self.logger.warning("No data, breaking")
                        break
                    pos = data.find("\r\n")
                    if pos != -1:
                        newline = data[:pos]
                        m = self.line.search(newline)
                        dt = datetime.datetime.now(tz)

                        if m and last_min != dt.minute:
                            row = self.new_data(m, dt)
                            self.save_row(
                                row["date"],
                                row["otemp"],
                                row["temp"],
                                row["oper"],
                                row["heat"],
                            )
                            self.fan_outlet.should_be(row["heat"])
                            last_min = dt.minute
                            data = ""
                        data = data[pos + 2 :]
                else:
                    break
            temp_source.close()
            time.sleep(10)

    def save_row(self, date, otemp, temp, oper, heat):
        connection = False
        my_config = self.config["mysql"]
        try:
            connection = mysql.connector.connect(
                host=my_config["host"],
                port=my_config["port"],
                database=my_config["db"],
                user=my_config["user"],
                password=my_config["passwd"],
            )

            insert_query = f'INSERT INTO temp  VALUES ("{date}", "{otemp}", "{temp}", {oper}, {heat}) '

            cursor = connection.cursor()
            cursor.execute(insert_query)
            connection.commit()
            cursor.close()

            self.logger.info(f'("{date}", "{otemp}", "{temp}", {oper}, {heat})')
        except mysql.connector.Error as error:
            self.logger.error("Failed to insert record {}".format(error))

        finally:
            if connection and connection.is_connected():
                connection.close()


if __name__ == "__main__":
    with open("config/config.json") as conf_file:
        config = json.load(conf_file)

    tz = pytz.timezone("US/Pacific")
    logging.basicConfig(
        format="%(asctime)s %(levelname)-8s %(message)s",
        level=logging.INFO,
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    temp_control = TempControl(config)
    while True:
        temp_control.poll()
