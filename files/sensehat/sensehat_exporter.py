import json
import re
import requests
import subprocess
import sys
import time

from pathlib import Path
from prometheus_client import start_http_server, Gauge
from requests.exceptions import RequestException
from sense_hat import SenseHat


def get_openweathermap_creds():
    home = str(Path.home())
    with open(home + '/.openweathermap') as f:
        return json.load(f)

def get_openweathermap_data(creds):
    '''
    An example of the json returned from current weather endpoint
    {
        "coord": {
            "lon": -122.96,
            "lat": 49.21
        },
        "weather": [{
            "id": 800,
            "main": "Clear",
            "description": "clear sky",
            "icon": "01n"
        }],
        "base": "stations",
        "main": {
            "temp": 9.05,
            "pressure": 1027,
            "humidity": 87,
            "temp_min": 7,
            "temp_max": 11
        },
        "visibility": 16093,
        "wind": {
            "speed": 2.1,
            "deg": 330,
            "gust": 5.1
        },
        "clouds": {
            "all": 1
        },
        "dt": 1539498900,
        "sys": {
            "type": 1,
            "id": 2928,
            "message": 0.0042,
            "country": "CA",
            "sunrise": 1539527509,
            "sunset": 1539566565
        },
        "id": 7798683,
        "name": "New Westminster",
        "cod": 200
    }
    '''
    url = 'https://api.openweathermap.org/data/2.5/weather?appid={}&units=metric&lat={}&lon={}'
    try:
        response = requests.get(url.format(creds['appid'], creds['lat'], creds['lon']),
                                headers={'Connection':'close'})
        response.raise_for_status()
        response.close()
        return json.loads(response.text)
    except RequestException as e:
        print(e)
        sys.stdout.flush()
        return None

def get_cpu_temperature():
    output = subprocess.check_output('cat /sys/class/thermal/thermal_zone0/temp', shell=True)
    return int(output) / 1000

def get_gpu_temperature():
    output = subprocess.check_output('/opt/vc/bin/vcgencmd measure_temp', shell=True)
    matches = re.match(b"^.+=(.+)'C$", output)
    if matches:
        return float(matches.groups()[0])
    return 0

def get_calibrated_temperature(temperature, cpu_temperature):
    factor = 1.3540
    return temperature - ((cpu_temperature - temperature) / factor)

def main():
    sensehat_pressure = Gauge('sensehat_pressure', 'Pressure reading from Sense HAT')
    sensehat_temperature = Gauge('sensehat_temperature', 'Temperature reading from Sense HAT')
    sensehat_humidity = Gauge('sensehat_humidity', 'Humidity reading from Sense HAT')
    cpu_temperature = Gauge('cpu_temperature', 'Temperature reading from Raspberry Pi\'s CPU')
    gpu_temperature = Gauge('gpu_temperature', 'Temperature reading from Raspberry Pi\'s GPU')
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
        gpu_temp = get_gpu_temperature()
        cpu_temperature.set(cpu_temp)
        gpu_temperature.set(gpu_temp)

        calibrated_temp = get_calibrated_temperature(temp, cpu_temp)
        calibrated_temperature.set(calibrated_temp)

        owm = get_openweathermap_data(creds)
        if owm is not None:
            openweathermap_pressure.set(owm['main']['pressure'])
            openweathermap_temperature.set(owm['main']['temp'])
            openweathermap_humidity.set(owm['main']['humidity'])

        time.sleep(20)


if __name__ == '__main__':
    main()
