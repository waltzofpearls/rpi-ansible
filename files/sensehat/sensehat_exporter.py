from prometheus_client import start_http_server, Gauge
from sense_hat import SenseHat
import time

gauge_pressure = Gauge('sensehat_pressure', 'Pressure reading from Sense HAT')
gauge_temperature = Gauge('sensehat_temperature', 'Temperature reading from Sense HAT')
gauge_humidity = Gauge('sensehat_humidity', 'Humidity reading from Sense HAT')

sense = SenseHat()
sense.clear()

gauge_pressure.set(sense.get_pressure())
gauge_temperature.set(sense.get_temperature())
gauge_humidity.set(sense.get_humidity())

if __name__ == '__main__':
    start_http_server(8000)
    while True:
        time.sleep(1)
