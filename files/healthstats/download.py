import cfscrape
import datetime
import json
import os
import pytz
import re
import requests
import sys
import tempfile
import time
import zipfile

from Fit import Conversions


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

    def __init__(self, timezone='UTC'):
        self.temp_dir = tempfile.mkdtemp()
        self.session = cfscrape.create_scraper(
            sess=requests.session(),
            delay=15
        )
        self.timezone = timezone

    def to_localtime(self, datetime_in_utc):
        return pytz.timezone(self.timezone).fromutc(datetime_in_utc)

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

    def get_monitoring(self):
        localtime = self.to_localtime(datetime.datetime.now())
        date = localtime.strftime("%Y-%m-%d")
        url = self.garmin_connect_download_daily_url + '/' + date
        response = self.get(url)
        if response:
            zipfile = self.temp_dir + '/' + str(date) + '.zip'
            self.save_binary_file(zipfile, response)

    def get_weight_chunk(self, start, end):
        params = {
            'from' : str(start),
            "until" : str(end)
        }
        response = self.get(self.garmin_connect_weight_url, params)
        return response.json()

    def get_weight_in_hours(self, hours):
        ms_in_hours = int(3600 * hours * 1000)
        end = Conversions.dt_to_epoch_ms(datetime.datetime.now())
        start = end - ms_in_hours
        data = self.get_weight_chunk(start, end)
        time.sleep(1)
        return data

    def get_sleep(self):
        localtime = self.to_localtime(datetime.datetime.now())
        date = localtime.strftime("%Y-%m-%d")
        url = self.garmin_connect_sleep_daily_url + '/' + self.display_name
        params = {'date': date}
        response = self.get(url, params)
        time.sleep(1)
        return response.json()

    def get_rhr_chunk(self, start, end):
        start_str = self.to_localtime(start).strftime("%Y-%m-%d")
        end_str = self.to_localtime(end).strftime("%Y-%m-%d")
        params = {
            'fromDate' : start_str,
            'untilDate' : end_str,
            'metricId' : 60
        }
        response = self.get(self.garmin_connect_rhr_url + '/' + self.display_name, params)
        data = response.json()
        try:
            rhr_data = data['allMetrics']['metricsMap']['WELLNESS_RESTING_HEART_RATE']
            return [entry for entry in rhr_data if entry['value'] is not None]
        except Exception:
            print("get_rhr_chunk: unexpected format - ", repr(data))

    def get_rhr_in_days(self, days):
        end = datetime.datetime.now()
        start = end - datetime.timedelta(days)
        data = self.get_rhr_chunk(start, end)
        time.sleep(1)
        return data
