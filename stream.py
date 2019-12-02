import datetime
import json
import logging
import re
import select
import socket
import time

import mysql.connector
from mysql.connector import Error
from mysql.connector import errorcode
import pytz
import requests

import fan

HEATING = "1"

def get_temp(api_key):
    # base_url variable to store url 
    base_url = "http://api.openweathermap.org/data/2.5/weather?"
    
    # Give city name 
    city_name = "5809844"
    
    # complete_url variable to store 
    # complete url address 
    complete_url = base_url + "appid=" + api_key + "&id=" + city_name 
    
    # get method of requests module 
    # return response object 
    response = requests.get(complete_url) 
    
    # json method of response object  
    # convert json format data into 
    # python format data 
    x = response.json() 
    
    # Now x contains list of nested dictionaries 
    # Check the value of "cod" key is equal to 
    # "404", means city is found otherwise, 
    # city is not found 
    if x["cod"] != "404": 
        # store the value of "main" 
        # key in variable y 
        y = x["main"] 
    
        # store the value corresponding 
        # to the "temp" key of y 
        current_temperature = y["temp"] 
    
        return str(round(current_temperature - 273.15, 2))
    
    else: 
        logger.error(" City Not Found ")
        return -273.15

def new_data(m, config, dt):
    row = {}
    row['temp'] = m.group(1)
    row['oper'] = m.group(2)
    row['heat'] = m.group(3)
    row['otemp'] = get_temp(config["weather"])
    row['date'] = dt.strftime("%Y-%m-%d %H:%M")
    
    return row


def poll(config, fan):
    data = ""        
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as temp_source:
        try:
            temp_source.connect((config['temp-control']['host'], config['temp-control']['port']))
            temp_source.setblocking(0)
        except Exception as e:
            logger.error(e)
            time.sleep(10)
            return
        logger.info('Connected to {}'.format( config['temp-control']['host']))
        
        last_min = datetime.datetime.now().minute - 1
        while True:
            ready = select.select([temp_source], [], [], 10.0)
            if ready[0]:
                data += temp_source.recv(1024).decode("utf-8")
                if not data:
                    logger.warn("No data, breaking")
                    break
                pos = data.find("\r\n")
                if pos != -1:
                    newline = data[:pos]
                    m = re.search('([0-9]+\.[0-9]+)\s([01])\s([01])', newline)
                    dt = datetime.datetime.now(tz)

                    if m and last_min != dt.minute:
                        row = new_data(m, config, dt)
                        save_row(config['mysql'], row['date'], row['otemp'], row['temp'], row['oper'], row['heat'])
                        fan.should_be(row['heat'])
                        last_min = dt.minute
                        data = ""
                    data = data[pos+2:]
            else:
                break
        temp_source.close()
        time.sleep(10)


def save_row(config, date, otemp, temp, oper, heat):
    connection = False
    try:
        connection = mysql.connector.connect(
            host=config['host'],
            port=config['port'],
            database=config['db'],
            user=config['user'],
            password=config['passwd']
        )

        mySql_insert_query = f"INSERT INTO temp  VALUES (\"{date}\", \"{otemp}\", \"{temp}\", {oper}, {heat}) "

        cursor = connection.cursor()
        result = cursor.execute(mySql_insert_query)
        connection.commit()
        cursor.close()
        logger.info(f"(\"{date}\", \"{otemp}\", \"{temp}\", {oper}, {heat})")
    except mysql.connector.Error as error:
        logger.error("Failed to insert record {}".format(error))

    finally:
        if (connection and connection.is_connected()):
            connection.close()


if __name__ == "__main__":
    config = None

    with open("config/config.json") as conf_file:
        config = json.load(conf_file)

    tz = pytz.timezone("US/Pacific")
    logging.basicConfig(
        format="%(asctime)s %(levelname)-8s %(message)s",
        level=logging.INFO,
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    logger = logging.getLogger()
    fan = fan.Fan(config["fan"], logger)
    while True:
        poll(config, fan)
