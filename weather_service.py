import requests


def get_temp(api_key: str):
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
    if x["cod"] == "404":
        raise ValueError(" City Not Found ")
    # store the value of "main"
    # key in variable y
    y = x["main"]

    # store the value corresponding
    # to the "temp" key of y
    current_temperature = y["temp"]

    return str(round(current_temperature - 273.15, 2))
