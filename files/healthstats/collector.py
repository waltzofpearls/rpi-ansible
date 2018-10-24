import json
import logging
import sys
import tempfile
import time

from pathlib import Path

from garmin_connect import GarminConnect
from prometheus_metrics import PrometheusMetrics


def main():
    logging.basicConfig(stream=sys.stdout,
                        level=logging.DEBUG,
                        format='%(asctime)s [%(name)s:%(levelname)s] %(message)s')
    logger = logging.getLogger()

    home = str(Path.home())
    with open(home + '/.garmin') as f:
        creds = json.load(f)

    connect = GarminConnect(creds['tz'])
    metrics = PrometheusMetrics()

    logger.info('Logging in to garmin connect ...')
    connect.login(creds['u'], creds['p'])

    logger.info('Downloading summary data ...')
    data = connect.get_summary()
    logger.info('Generating weight, resting heart rate, steps, floor and calorie metrics ...')
    metrics.summary(data)

    time.sleep(1)

    logger.info('Downloading sleep data ...')
    data = connect.get_sleep()
    logger.info('Generating sleep metrics ...')
    metrics.sleep(data)

    logger.info('Publishing metrics to Pushgateway ...')
    metrics.publish()


if __name__ == '__main__':
    main()
