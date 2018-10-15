import cfscrape
import datetime
import json
import logging
import os
import re
import requests
import sys
import tempfile
import time
import zipfile

sys.path.append('/usr/lib/python3/dist-packages/Fit')

from Fit import Conversions
from pathlib import Path
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway

logger = logging.getLogger()


class Download():
    garmin_connect_base_url = "https://connect.garmin.com"

    garmin_connect_sso_url = 'https://sso.garmin.com/sso'
    garmin_connect_sso_login_url = garmin_connect_sso_url + '/signin'
    garmin_connect_login_url = garmin_connect_base_url + "/en-US/signin"
    garmin_connect_css_url = 'https://static.garmincdn.com/com.garmin.connect/ui/css/gauth-custom-v1.2-min.css'

    garmin_connect_modern_url = garmin_connect_base_url + '/modern'
    garmin_connect_modern_proxy_url = garmin_connect_modern_url + '/proxy'

    garmin_connect_download_url = garmin_connect_modern_proxy_url + '/download-service/files'
    garmin_connect_download_daily_url = garmin_connect_download_url + '/wellness'
    garmin_connect_user_profile_url = garmin_connect_modern_proxy_url + '/userprofile-service/userprofile'
    garmin_connect_personal_info_url = garmin_connect_user_profile_url + '/personal-information'
    garmin_connect_wellness_url = garmin_connect_modern_proxy_url + '/wellness-service/wellness'
    garmin_connect_sleep_daily_url = garmin_connect_wellness_url + '/dailySleepData'
    garmin_connect_rhr_url = garmin_connect_modern_proxy_url + '/userstats-service/wellness/daily'
    garmin_connect_weight_url = garmin_connect_personal_info_url + '/weightWithOutbound/filterByDay'

    def __init__(self):
        self.temp_dir = tempfile.mkdtemp()
        self.session = cfscrape.create_scraper(
            sess=requests.session(),
            delay=15
        )

    def get(self, url, params={}):
        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response

    def post(self, url, params, data):
        response = self.session.post(url, params=params, data=data)
        response.raise_for_status()
        return response

    def get_json(self, page_html, key):
        found = re.search(key + r" = JSON.parse\(\"(.*)\"\);", page_html, re.M)
        if found:
            json_text = found.group(1).replace('\\"', '"')
            return json.loads(json_text)

    def login(self, username, password):
        params = {
            'service': self.garmin_connect_modern_url,
            'webhost': self.garmin_connect_base_url,
            'source': self.garmin_connect_login_url,
            'redirectAfterAccountLoginUrl': self.garmin_connect_modern_url,
            'redirectAfterAccountCreationUrl': self.garmin_connect_modern_url,
            'gauthHost': self.garmin_connect_sso_url,
            'locale': 'en_US',
            'id': 'gauth-widget',
            'cssUrl': self.garmin_connect_css_url,
            'clientId': 'GarminConnect',
            'rememberMeShown': 'true',
            'rememberMeChecked': 'false',
            'createAccountShown': 'true',
            'openCreateAccount': 'false',
            'usernameShown': 'false',
            'displayNameShown': 'false',
            'consumeServiceTicket': 'false',
            'initialFocus': 'true',
            'embedWidget': 'false',
            'generateExtraServiceTicket': 'false'
        }
        self.get(self.garmin_connect_sso_login_url, params)
        data = {
            'username': username,
            'password': password,
            'embed': 'true',
            'lt': 'e1s1',
            '_eventId': 'submit',
            'displayNameRequired': 'false'
        }
        response = self.post(self.garmin_connect_sso_login_url, params, data)
        found = re.search(r"\?ticket=([\w-]*)", response.text, re.M)
        if not found:
            return False
        params = {'ticket' : found.group(1)}
        response = self.get(self.garmin_connect_modern_url, params)
        self.user_prefs = self.get_json(response.text, 'VIEWER_USERPREFERENCES')
        self.display_name = self.user_prefs['displayName']
        self.english_units = (self.user_prefs['measurementSystem'] == 'statute_us')
        self.social_profile = self.get_json(response.text, 'VIEWER_SOCIAL_PROFILE')
        self.full_name = self.social_profile['fullName']
        return True

    def save_binary_file(self, filename, response):
        with open(filename, 'wb') as file:
            for chunk in response:
                file.write(chunk)

    def convert_to_json(self, object):
        return object.__str__()

    def save_json_file(self, json_filename, json_data):
        with open(json_filename + '.json', 'w') as file:
            file.write(json.dumps(json_data, default=self.convert_to_json))

    def unzip_files(self, outdir):
        for filename in os.listdir(self.temp_dir):
            match = re.search('.*\.zip', filename)
            if match:
                files_zip = zipfile.ZipFile(self.temp_dir + "/" + filename, 'r')
                files_zip.extractall(outdir)
                files_zip.close()

    def get_monitoring_day(self, date):
        logger.info("get_monitoring_day: %s", str(date))
        response = self.get(self.garmin_connect_download_daily_url + '/' + date.strftime("%Y-%m-%d"))
        if response:
            self.save_binary_file(self.temp_dir + '/' + str(date) + '.zip', response)

    def get_monitoring(self, date, days):
        logger.info("get_monitoring: %s : %d", str(date), days)
        for day in range(0, days):
            day_date = date + datetime.timedelta(day)
            self.get_monitoring_day(day_date)
            # pause for a second between every page access
            time.sleep(1)

    def get_weight_chunk(self, start, end):
        params = {
            'from' : str(start),
            "until" : str(end)
        }
        response = self.get(self.garmin_connect_weight_url, params)
        return response.json()

    def get_weight(self):
        data = []
        chunk_size = int((86400 * 365) * 1000)
        end = Conversions.dt_to_epoch_ms(datetime.datetime.now())
        while True:
            start = end - chunk_size
            chunk_data = self.get_weight_chunk(start, end)
            if len(chunk_data) <= 1:
                break
            data.extend(chunk_data)
            end -= chunk_size
            # pause for a second between every page access
            time.sleep(1)
        return data

    def get_weight_in_hours(self, hours):
        ms_in_hours = int(3600 * hours * 1000)
        end = Conversions.dt_to_epoch_ms(datetime.datetime.now())
        start = end - ms_in_hours
        data = self.get_weight_chunk(start, end)
        time.sleep(1)
        return data

    def get_sleep_day(self, directory, date):
        filename = directory + '/sleep_' + str(date) + '.json'
        if not os.path.isfile(filename):
            params = {'date': date.strftime("%Y-%m-%d")}
            response = self.get(self.garmin_connect_sleep_daily_url + '/' + self.display_name, params)
            self.save_binary_file(filename, response)

    def get_sleep(self, directory, date, days):
        for day in range(0, days):
            day_date = date + datetime.timedelta(day)
            self.get_sleep_day(directory, day_date)
            # pause for a second between every page access
            time.sleep(1)

    def get_rhr_chunk(self, start, end):
        start_str = start.strftime("%Y-%m-%d")
        end_str = end.strftime("%Y-%m-%d")
        params = {
            'fromDate' : start_str,
            'untilDate' : end_str,
            'metricId' : 60
        }
        response = self.get(self.garmin_connect_rhr_url + '/' + self.display_name, params)
        json_data = response.json()
        try:
            rhr_data = json_data['allMetrics']['metricsMap']['WELLNESS_RESTING_HEART_RATE']
            return [entry for entry in rhr_data if entry['value'] is not None]
        except Exception:
            print("get_rhr_chunk: unexpected format - ", repr(json_data))

    def get_rhr(self):
        data = []
        chunk_size = datetime.timedelta(30)
        end = datetime.datetime.now()
        while True:
            start = end - chunk_size
            chunk_data = self.get_rhr_chunk(start, end)
            if chunk_data is None or len(chunk_data) == 0:
                break
            data.extend(chunk_data)
            end -= chunk_size
            # pause for a second between every page access
            time.sleep(1)
        return data


class Metrics():
    def __init__(self):
        self.registry = CollectorRegistry()
        self.pushgateway = 'localhost:9091'
        self.job_name = 'healthstats'

    def weight(self, data):
        if len(data) == 0:
            return

        weight = Gauge('weight', 'Body weight in KG', registry=self.registry)
        body_fat = Gauge('body_fat', 'Body fat in %', registry=self.registry)
        bone_mass = Gauge('bone_mass', 'Bone mass in KG', registry=self.registry)
        bmi = Gauge('bmi', 'BMI', registry=self.registry)
        body_water = Gauge('body_water', 'Body water in %', registry=self.registry)
        muscle_mass = Gauge('muscle_mass', 'Muscle mass in KG', registry=self.registry)

        weight.set(data[0]['weight'] / 1000.0)
        body_fat.set(data[0]['bodyFat'])
        bone_mass.set(data[0]['boneMass'] / 1000.0)
        bmi.set(data[0]['bmi'])
        body_water.set(data[0]['bodyWater'])
        muscle_mass.set(data[0]['muscleMass'] / 1000.0)

    def publish(self):
        push_to_gateway(self.pushgateway, job=self.job_name, registry=self.registry)


def main(argv):
    days = 1
    date = datetime.datetime.now().date() - datetime.timedelta(days)

    temp = tempfile.mkdtemp()
    monitoring_path = temp + "/monitoring"
    sleep_path = temp + "/sleep"
    weight_path = temp + "/weight"
    rhr_path = temp + "/rhr"

    Path(monitoring_path).mkdir(parents=True, exist_ok=True)
    Path(sleep_path).mkdir(parents=True, exist_ok=True)
    Path(weight_path).mkdir(parents=True, exist_ok=True)
    Path(rhr_path).mkdir(parents=True, exist_ok=True)

    home = str(Path.home())
    with open(home + '/.garmin') as f:
        creds = json.load(f)

    download = Download()
    metrics = Metrics()

    print('Logging in to garmin connect ...')
    download.login(creds['u'], creds['p'])

    # print('Saving monitoring data to: {} ...'.format(monitoring_path))
    # download.get_monitoring(date, days)
    # download.unzip_files(monitoring_path)

    # print('Saving sleep data to: {} ...'.format(sleep_path))
    # download.get_sleep(sleep_path, date, days)

    print('Downloading weight data ...')
    weight = download.get_weight_in_hours(24)
    print('Generating weight metrics ...')
    metrics.weight(weight)

    # print('Saving resting heart rate data to: {} ...'.format(rhr_path))
    # rhr = download.get_rhr()
    # download.save_json_file(rhr_path + '/rhr_' + str(int(time.time())), rhr)

    print('Publishing metrics to Pushgateway ...')
    metrics.publish()


if __name__ == '__main__':
    main(sys.argv[1:])
