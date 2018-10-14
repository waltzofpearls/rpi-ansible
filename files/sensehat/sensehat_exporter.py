import json
import re
import requests
import subprocess
import time

from pathlib import Path
from prometheus_client import start_http_server, Gauge
from sense_hat import SenseHat


def get_openweathermap_creds():
    home = str(Path.home())
    with open(home + '/.openweathermap') as f:
        return json.load(f)

def get_openweathermap_data(creds):
    url = 'https://api.openweathermap.org/data/2.5/weather?appid={}&units=metric&lat={}&lon={}'
    response = requests.get(url.format(creds['appid'], creds['lat'], creds['lon']))
    response.raise_for_status()
    return json.loads(response.text)

def get_cpu_temperature():
    output = subprocess.check_output("vcgencmd measure_temp", shell=True)
    matches = re.match(b"^.+=(.+)'C$", output)
    if matches:
        return float(matches.groups()[0])
    return 0

def get_calibrated_temperature(temperature, cpu_temperature):
    factor = 2.8146
    return temperature - ((cpu_temperature - temperature) / factor)

def main():
    sensehat_pressure = Gauge('sensehat_pressure', 'Pressure reading from Sense HAT')
    sensehat_temperature = Gauge('sensehat_temperature', 'Temperature reading from Sense HAT')
    sensehat_humidity = Gauge('sensehat_humidity', 'Humidity reading from Sense HAT')
    cpu_temperature = Gauge('cpu_temperature', 'Temperature reading from Raspberry Pi\'s CPU')
    calibrated_temperature = Gauge('calibrated_temperature', 'Calibrated temperature')
    openweathermap_pressure = Gauge('openweathermap_pressure', 'Pressure reading from OpenWeatherMap API')
    openweathermap_temperature = Gauge('openweathermap_temperature', 'Temperature reading from OpenWeatherMap API')
    openweathermap_humidity = Gauge('openweathermap_humidity', 'Humidity reading from OpenWeatherMap API')

    sensehat = SenseHat()
    sensehat.clear()

    creds = get_openweathermap_creds()

    start_http_server(8000)

    while True:
        temp = sensehat.get_temperature_from_pressure()
        sensehat_pressure.set(sensehat.get_pressure())
        sensehat_temperature.set(temp)
        sensehat_humidity.set(sensehat.get_humidity())

        cpu_temp = get_cpu_temperature()
        cpu_temperature.set(cpu_temp)

        calibrated_temp = get_calibrated_temperature(temp, cpu_temp)
        calibrated_temperature.set(calibrated_temp)

        owm = get_openweathermap_data(creds)
        openweathermap_pressure.set(owm['main']['pressure'])
        openweathermap_temperature.set(owm['main']['temp'])
        openweathermap_humidity.set(owm['main']['humidity'])

        time.sleep(20)


if __name__ == '__main__':
    main()
