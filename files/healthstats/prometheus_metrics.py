import datetime
import os
import pytz

from prometheus_client import CollectorRegistry, Gauge, pushadd_to_gateway


class PrometheusMetrics():
    def __init__(self):
        self.registry = CollectorRegistry()
        self.pushgateway = os.environ.get('PUSHGATEWAY', 'localhost:9091')
        self.job_name = os.environ.get('JOB_NAME', 'healthstats')
        self.timezone = os.environ.get('TIMEZONE', 'UTC')

    def summary(self, data):
        self._weight(data)
        self._resting_heart_rate(data)

        if 'durationInMilliseconds' in data \
            and int(data['durationInMilliseconds']) >= 43200000:
            # only sync when the current day past 12 hours
            # 43200000 = 3600 * 12 * 1000
            self._steps(data)
            self._floors(data)

        if 'durationInMilliseconds' in data \
            and int(data['durationInMilliseconds']) >= 64800000:
            # only sync when the current day past 18 hours
            # 64800000 = 3600 * 18 * 1000
            self._intensity_minutes(data)

    def _weight(self, data):
        if data.get('weight') is None \
            or data.get('bodyFat') is None \
            or data.get('boneMass') is None \
            or data.get('bmi') is None \
            or data.get('bodyWater') is None \
            or data.get('muscleMass') is None:
            return

        # create metrics
        weight_total = self.gauge('weight_total', 'Body weight in KG')
        weight_body_fat = self.gauge('weight_body_fat', 'Body fat in %')
        weight_bone_mass = self.gauge('weight_bone_mass', 'Bone mass in KG')
        weight_bmi = self.gauge('weight_bmi', 'BMI')
        weight_body_water = self.gauge('weight_body_water', 'Body water in %')
        weight_muscle_mass = self.gauge('weight_muscle_mass', 'Muscle mass in KG')

        # set metrics values
        weight_total.set(data['weight'] / 1000.0)
        weight_body_fat.set(data['bodyFat'])
        weight_bone_mass.set(data['boneMass'] / 1000.0)
        weight_bmi.set(data['bmi'])
        weight_body_water.set(data['bodyWater'])
        weight_muscle_mass.set(data['muscleMass'] / 1000.0)

    def _resting_heart_rate(self, data):
        if data.get('restingHeartRate') is None:
            return

        # create metrics
        resting_heart_rate = self.gauge('resting_heart_rate', 'Resting heart rate')

        # set metrics values
        resting_heart_rate.set(data['restingHeartRate'])

    def _steps(self, data):
        if data.get('totalSteps') is None \
            or data.get('dailyStepGoal') is None \
            or data.get('totalKilocalories') is None \
            or data.get('totalDistanceMeters') is None \
            or data.get('sedentarySeconds') is None:
            return

        # create metrics
        steps = self.gauge('steps', 'Total steps')
        steps_daily_goal = self.gauge('steps_daily_goal', 'Daily step goal')
        calories = self.gauge('calories', 'Total calories')
        distance_meters = self.gauge('distance_meters', 'Total distance in meters')
        sedentary_seconds = self.gauge('sedentary_seconds', 'Seconds in sedentary position')

        # set metrics values
        steps.set(data['totalSteps'])
        steps_daily_goal.set(data['dailyStepGoal'])
        calories.set(data['totalKilocalories'])
        distance_meters.set(data['totalDistanceMeters'])
        sedentary_seconds.set(data['sedentarySeconds'])

    def _intensity_minutes(self, data):
        if data.get('moderateIntensityMinutes') is None \
            or data.get('vigorousIntensityMinutes') is None:
            return

        # create metrics
        intensity_minutes_moderate = self.gauge('intensity_minutes_moderate', 'Minutes in moderate intensity activities')
        intensity_minutes_vigorous = self.gauge('intensity_minutes_vigorous', 'Minutes in vigorous intensity activities')

        # set metrics values
        intensity_minutes_moderate.set(data['moderateIntensityMinutes'])
        intensity_minutes_vigorous.set(data['vigorousIntensityMinutes'])

    def _floors(self, data):
        if data.get('floorsAscended') is None \
            or data.get('floorsAscendedInMeters') is None \
            or data.get('floorsDescended') is None \
            or data.get('floorsDescendedInMeters') is None:
            return

        # create metrics
        floors_ascended = self.gauge('floors_ascended', 'Floors ascended')
        floors_ascended_meters = self.gauge('floors_ascended_meters', 'Floors ascended in meters')
        floors_descended = self.gauge('floors_descended', 'Floors descended')
        floors_descended_meters = self.gauge('floors_descended_meters', 'Floors descended in meters')

        # set metrics values
        floors_ascended.set(data['floorsAscended'])
        floors_ascended_meters.set(data['floorsAscendedInMeters'])
        floors_descended.set(data['floorsDescended'])
        floors_descended_meters.set(data['floorsDescendedInMeters'])

    def sleep(self, data):
        utc = datetime.datetime.now()
        now = pytz.timezone(self.timezone).fromutc(utc)
        midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
        duration = (now - midnight).seconds

        if duration < 36000:
            # only sync when the day past 10 hours
            # 36000 = 3600 * 10
            return

        if data.get('sleepTimeSeconds') is None \
            or data.get('deepSleepSeconds') is None \
            or data.get('lightSleepSeconds') is None \
            or data.get('awakeSleepSeconds') is None:
            return

        # create metrics
        sleep_time_sec = self.gauge('sleep_time_sec', 'Total sleep time in seconds')
        sleep_deep_sec = self.gauge('sleep_deep_sec', 'Deep sleep time in seconds')
        sleep_light_sec = self.gauge('sleep_light_sec', 'Light sleep time in seconds')
        sleep_awake_sec = self.gauge('sleep_awake_sec', 'Sleep awake time in seconds')

        # set metrics values
        sleep_time_sec.set(data['sleepTimeSeconds'])
        sleep_deep_sec.set(data['deepSleepSeconds'])
        sleep_light_sec.set(data['lightSleepSeconds'])
        sleep_awake_sec.set(data['awakeSleepSeconds'])

    def gauge(self, name, documentation):
        return Gauge(name, documentation, registry=self.registry)

    def publish(self):
        pushadd_to_gateway(self.pushgateway, job=self.job_name, registry=self.registry)
