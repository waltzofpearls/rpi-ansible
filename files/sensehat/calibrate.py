import re
import subprocess

from sense_hat import SenseHat

output = subprocess.check_output("vcgencmd measure_temp", shell=True)
matches = re.match(b"^.+=(.+)'C$", output)
cpu_temp = 0
if matches:
    cpu_temp = float(matches.groups()[0])

temp_calibrated = 20

sense = SenseHat()
temp = sense.get_temperature_from_pressure()
factor = (cpu_temp - temp) / (temp - temp_calibrated)

print('cpu temp: {}'.format(cpu_temp))
print('temp: {}'.format(temp))
print('factor: {}'.format(factor))
