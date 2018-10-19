import json
import tempfile

from pathlib import Path

from download import Download
from metrics import Metrics


def main():
    temp = tempfile.mkdtemp()
    monitoring_path = temp + "/monitoring"
    Path(monitoring_path).mkdir(parents=True, exist_ok=True)

    home = str(Path.home())
    with open(home + '/.garmin') as f:
        creds = json.load(f)

    download = Download(creds['tz'])
    metrics = Metrics()

    print('Logging in to garmin connect ...')
    download.login(creds['u'], creds['p'])

    # print('Downloading monitoring data to: {} ...'.format(monitoring_path))
    # download.get_monitoring()
    # download.unzip_files(monitoring_path)

    print('Downloading sleep data ...')
    data = download.get_sleep()
    print('Generating sleep metrics ...')
    metrics.sleep(data)

    print('Downloading weight data ...')
    data = download.get_weight_in_hours(24)
    print('Generating weight metrics ...')
    metrics.weight(data)

    print('Downloading resting heart rate data ...')
    data = download.get_rhr_in_days(1)
    print('Generating resting heart rate metrics ...')
    metrics.resting_heart_rate(data)

    print('Publishing metrics to Pushgateway ...')
    metrics.publish()


if __name__ == '__main__':
    main()
