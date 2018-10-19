from prometheus_client import CollectorRegistry, Gauge, pushadd_to_gateway


class Metrics():
    def __init__(self):
        self.registry = CollectorRegistry()
        self.pushgateway = 'localhost:9091'
        self.job_name = 'healthstats'

    def sleep(self, data):
        '''
        'dailySleepDTO': {
	    	'sleepQualityTypePK': None,
	    	'remSleepSeconds': 0,
	    	'napTimeSeconds': 0,
	    	'autoSleepEndTimestampGMT': 1539874440000,
	    	'userProfilePK': 48251499,
	    	'sleepResultTypePK': None,
	    	'awakeSleepSeconds': 1500,
	    	'sleepEndTimestampGMT': 1539874440000,
	    	'sleepEndTimestampLocal': 1539849240000,
	    	'sleepStartTimestampGMT': 1539828300000,
	    	'autoSleepStartTimestampGMT': 1539828300000,
	    	'sleepStartTimestampLocal': 1539803100000,
	    	'unmeasurableSleepSeconds': 0,
	    	'calendarDate': '2018-10-18',
	    	'sleepTimeSeconds': 44640,
	    	'deepSleepSeconds': 22920,
	    	'sleepWindowConfirmationType': 'auto_confirmed_final',
	    	'lightSleepSeconds': 21720,
	    	'deviceRemCapable': False,
	    	'id': 1539828300000,
	    	'sleepWindowConfirmed': True
	    }
        '''
        if 'dailySleepDTO' not in data:
            return

        daily_sleep = data['dailySleepDTO']

        if daily_sleep['sleepTimeSeconds'] is None \
            or daily_sleep['deepSleepSeconds'] is None \
            or daily_sleep['lightSleepSeconds'] is None \
            or daily_sleep['awakeSleepSeconds'] is None:
            return

        sleep_time_sec = Gauge('sleep_time_sec', 'Total sleep time in seconds', registry=self.registry)
        sleep_deep_sec = Gauge('sleep_deep_sec', 'Deep sleep time in seconds', registry=self.registry)
        sleep_light_sec = Gauge('sleep_light_sec', 'Light sleep time in seconds', registry=self.registry)
        sleep_awake_sec = Gauge('sleep_awake_sec', 'Sleep awake time in seconds', registry=self.registry)

        sleep_time_sec.set(daily_sleep['sleepTimeSeconds'])
        sleep_deep_sec.set(daily_sleep['deepSleepSeconds'])
        sleep_light_sec.set(daily_sleep['lightSleepSeconds'])
        sleep_awake_sec.set(daily_sleep['awakeSleepSeconds'])

    def weight(self, data):
        if len(data) == 0:
            return
        # first one is the latest
        latest = data[0]

        weight_total = Gauge('weight_total', 'Body weight in KG', registry=self.registry)
        weight_body_fat = Gauge('weight_body_fat', 'Body fat in %', registry=self.registry)
        weight_bone_mass = Gauge('weight_bone_mass', 'Bone mass in KG', registry=self.registry)
        weight_bmi = Gauge('weight_bmi', 'BMI', registry=self.registry)
        weight_body_water = Gauge('weight_body_water', 'Body water in %', registry=self.registry)
        weight_muscle_mass = Gauge('weight_muscle_mass', 'Muscle mass in KG', registry=self.registry)

        weight_total.set(latest['weight'] / 1000.0)
        weight_body_fat.set(latest['bodyFat'])
        weight_bone_mass.set(latest['boneMass'] / 1000.0)
        weight_bmi.set(latest['bmi'])
        weight_body_water.set(latest['bodyWater'])
        weight_muscle_mass.set(latest['muscleMass'] / 1000.0)

    def resting_heart_rate(self, data):
        if len(data) == 0:
            return
        # last one is the latest
        latest = data[-1]

        resting_heart_rate = Gauge('resting_heart_rate', 'Resting heart rate', registry=self.registry)
        resting_heart_rate.set(latest['value'])

    def publish(self):
        pushadd_to_gateway(self.pushgateway, job=self.job_name, registry=self.registry)
