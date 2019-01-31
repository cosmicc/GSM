import argparse
import sqlite3
import sys
import os
import threading
from datetime import datetime, time
from statistics import mean
from time import sleep
from timeit import default_timer as timer

import Adafruit_DHT
import RPi.GPIO as GPIO
from loguru import logger as log
from modules.extras import float_trunc_1dec, c2f
from modules.rpiboard import Led, cpu_temp
from sms import sendsms
from timebetween import is_time_between
from web import web

IN_RC = 17       # Input pin

GPIO.setmode(GPIO.BCM)

logfile = '/var/log/gsm.log'
alarmfile = '/var/log/alarms.log'

boardled = Led('status')
boardled.ledoff()

parser = argparse.ArgumentParser(prog='GSM')
parser.add_argument('-c', '--console', action='store_true', help='supress logging output to console. default: error logging')
parser.add_argument('-d', '--debug', action='store_true', help='extra verbose output (debug)')
parser.add_argument('-i', '--info', action='store_true', help='verbose output (info)')
parser.add_argument('-r', '--reset', action='store_true', help='reset database')
args = parser.parse_args()

if args.debug:
    loglevel = "DEBUG"
elif args.info:
    loglevel = "INFO"
else:
    loglevel = "WARNING"

if args.console:
    log.configure(
        handlers=[dict(sink=sys.stdout, level=loglevel, backtrace=True, format='<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>'),
                  dict(sink=logfile, level="INFO", enqueue=True, serialize=False, rotation="1 MB", retention="14 days", compression="gz")],
                  levels=[dict(name="STARTUP", no=38, icon="¤", color="<yellow>")], extra={"common_to_all": "default"}, activation=[("my_module.secret", False), ("another_library.module", True)])
else:
    log.configure(
        handlers=[dict(sink=sys.stderr, level="CRITICAL", backtrace=True, format='<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>'),
                  dict(sink=logfile, level="INFO", enqueue=True, serialize=False, rotation="1 MB", retention="14 days", compression="gz")],
                  levels=[dict(name="STARTUP", no=38, icon="¤", color="<yellow>")], extra={"common_to_all": "default"}, activation=[("my_module.secret", False), ("another_library.module", True)])

log.log('STARTUP', 'GSM is starting up')

if args.reset:
   os.remove("/var/opt/lightdata.db")

#mdb = sqlite3.connect("file::memory:?cache=shared", uri=True)
db = sqlite3.connect('/var/opt/lightdata.db')
cursor = db.cursor()
#mcursor = mdb.cursor()
#mcursor.execute('CREATE TABLE general(id INTEGER PRIMARY KEY, name TEXT, timestamp TEXT, light INTEGER, temp REAL, humidity REAL)')
cursor.execute('CREATE TABLE IF NOT EXISTS alarms(id INTEGER PRIMARY KEY, timestamp TEXT, value INTEGER, type TEXT)')
cursor.execute('CREATE TABLE IF NOT EXISTS data(id INTEGER PRIMARY KEY, timestamp TEXT, light INTEGER, temp REAL, humidity REAL)')
cursor.execute('CREATE TABLE IF NOT EXISTS general(id INTEGER PRIMARY KEY, name TEXT, timestamp TEXT, light INTEGER, temp REAL, humidity REAL)')
#mcursor.execute('INSERT INTO general (name) VALUES ("lastdata")')
if args.reset:
    cursor.execute('INSERT INTO general (name) VALUES ("laston")')
    cursor.execute('INSERT INTO general (name) VALUES ("lastoff")')
    cursor.execute('INSERT INTO general (name) VALUES ("lighthours")')
    cursor.execute('INSERT INTO general (name) VALUES ("livedata")')
db.commit()
db.close()
if args.reset:
    print('Database has been reset')
    os.remove("/var/log/gsm.log")
    os.remove("/var/log/alarms.log")
    exit(0)


log.debug('Starting web thread')
web_thread = threading.Thread(name='web_thread', target=web, daemon=True)
web_thread.start()

def dbupdate(cmd):
    try:
        db = sqlite3.connect('/var/opt/lightdata.db')
        cursor = db.cursor()
        cursor.execute(cmd)
        db.commit()
        db.close()
    except:
        log.exception('Error updating DB')


def dbselect(cmd, fetchall=True):
    try:
        db = sqlite3.connect('/var/opt/lightdata.db')
        cursor = db.cursor()
        cursor.execute(cmd)
        if fetchall == False:
            a = cursor.fetchone()
        else:
            a = cursor.fetchall()
        db.close()
    except:
        log.exception('Error querying DB')
    else:
        return a


class tempSensor():
    def __init__(self):
        self.sensor_type = 'DHT22'
        self.pin = 23
        self.units = 'F'
        self.temp = 0.0
        self.humidity = 0.0
        if self.sensor_type == "DHT11":
            self.sensor = Adafruit_DHT.DHT11
        elif self.sensor_type == "DHT22":
            self.sensor = Adafruit_DHT.DHT22
        elif self.sensor_type == "AM2302":
            self.sensor = Adafruit_DHT.AM2302
        else:
            log.error(f'1wire temp sensor - invalid sensor type: {self.sensor_type}')
            exit(1)
        log.info(f'Initialized 1wire temp sensor: {self.sensor_type} on pin: {self.pin}')

    def check(self):
        try:
            hum, tmp = Adafruit_DHT.read_retry(self.sensor, self.pin)
        except:
            log.error(f'Error polling temp/humidity sensor')
            return (0, 0)
        else:
            log.debug(f'Temp Values Recieved: {float_trunc_1dec(tmp)}C {float_trunc_1dec(c2f(tmp))}F {self.humidity}%')
            if hum is not None and tmp is not None:
                if self.units == 'C':
                    self.temp = float_trunc_1dec(tmp)
                elif self.units == 'F':
                    self.temp = float_trunc_1dec(c2f(tmp))
                else:
                    log.error(f'Invalid temp units in config file {self.units}')
                self.humidity = float_trunc_1dec(hum)
                # print(self.temp, self.humidity)
                log.debug(f'Tempurature={self.temp}*{self.units}  Humidity={self.humidity}%')
                return (self.temp, self.humidity)
            else:
                log.warning(f'Failed getting temp/humidity sensor reading')
                return (0, 0)

def determinelighthours():
    db = sqlite3.connect('/var/opt/lightdata.db')
    cursor = db.cursor()
    #cursor.execute(''
    db.commit()
    db.close()



def normalizeit(value):
    return (0 + (100 - 0) * ((value - 250000) / (0 - 250000)))


def pc_read(RCpin):
        reading = 0
        GPIO.setup(RCpin, GPIO.OUT)
        GPIO.output(RCpin, GPIO.LOW)
        sleep(0.1)

        GPIO.setup(RCpin, GPIO.IN)
        # This takes about 1 millisecond per loop cycle
        while (GPIO.input(RCpin) == GPIO.LOW) and reading < 500000:
            reading += 1
        return reading


onalarm = timer() - 3600
offalarm = timer() - 3600
tempalarm = timer() - 3600

tempsensor = tempSensor()

lastlight = None
lastlighttimer = timer() - 300
lastlighttimer2 = timer() - 300
lastdatatimer = timer()

while True:
    try:
        times = timer()
        b = []
        temp, humidity = tempsensor.check()
        while timer() - times < 60:
            a = pc_read(IN_RC)
            b.append(a)
            sleep(1)
        if lastlight is None:
            lastlight = int(mean(b))
        else:
            lastlight = light
        light = int(mean(b))
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        if lastlight >= 200000 and light < 200000 and timer() - lastlighttimer > 300:
            lastlighttimer = timer()
            dbupdate(f'''UPDATE general SET timestamp = '{timestamp}', light = {light}, temp = {temp}, humidity = {humidity} WHERE name = "laston"''')
            log.info(f'Light ON has been detected')
        if lastlight < 200000 and light >= 200000 and timer() - lastlighttimer2 > 300:
            lastlighttimer = timer()
            dbupdate(f'''UPDATE general SET timestamp = '{timestamp}', light = {light}, temp = {temp}, humidity = {humidity} WHERE name = "lastoff"''')

            s = dbselect('''SELECT timestamp FROM general WHERE name = "laston"''')
            so = datetime.strptime(s[0][0], '%Y-%m-%d %H:%M')
            eo = datetime.strptime(timestamp, '%Y-%m-%d %H:%M')
            if so is not None and eo is not None:
                td = eo - so
                lh = round(td.total_seconds()/3600, 1)
            else:
                lh = 'N/A'
            log.warning(lh)
            dbupdate(f'''UPDATE general SET temp = {lh} WHERE name = "lighthours"''')
            log.info(f'Light OFF has been detected. Total Light hours: {lh}')
        nlight = int(normalizeit(light))
        log.debug(f'Light Values Recieved: {light} ({nlight}/100)')


        dbupdate(f"""UPDATE general SET timestamp = '{timestamp}', light = {light}, temp = {temp}, humidity = {humidity} WHERE name = 'livedata'""")
        #mdb.commit()
        log.debug('Data saved in livedata database')

        if timer() - lastdatatimer > 300:
            lastdatatimer = timer()
            dbupdate(f'''INSERT INTO data(timestamp, light, temp, humidity) VALUES ('{timestamp}',{light},{temp},{humidity})''')
            log.debug('Data saved in longterm database')


        if is_time_between(datetime.now().time(), time(17, 00), time(5, 30)) and light > 100000:  # on light time
            if timer() - onalarm > 3600:
                onalarm = timer()
                log.warning(f'ALARM: Lights should be on but are NOT ON lightvalue: {light} ({nlight}/100)')
                dbupdate(f'''INSERT INTO alarms(timestamp, value, type) VALUES ('{timestamp}',{light},'light not on')''')
                with open(alarmfile, "a") as myfile:
                    myfile.write(f"{timestamp}: Lights should be on but are NOT ON lightvalue: {light} ({nlight}/100)\n")
                # sendsms(f'ALARM: Lights should be on but are NOT ON lightvalue: {light} ({nlight}/100)')
        elif is_time_between(datetime.now().time(), time(18, 30), time(4, 50)) and light > 5000:  # on hid light time
            if timer() - onalarm > 3600:
                onalarm = timer()
                log.warning(f'ALARM: Lights are on but weak. lightvalue: {light} ({nlight}/100)')
                dbupdate(f'''INSERT INTO alarms(timestamp, value, type) VALUES ('{timestamp}',{light},'light too low')''')
                with open(alarmfile, "a") as myfile:
                    myfile.write(f"{timestamp}: Lights are on but weak. lightvalue: {light} ({nlight}/100)\n")
                # sendsms(f'ALARM: Lights are on but WEAK. lightvalue: {light} ({nlight}/100)')
        elif is_time_between(datetime.now().time(), time(6, 10), time(16, 40)) and light < 400000:  # off light time
            if timer() - offalarm > 3600:
                offalarm = timer()
                log.warning(f'ALARM: Lights should be off but ARE STILL ON lightvalue: {light} ({nlight}/100)')
                dbupdate(f'''INSERT INTO alarms(timestamp, value, type) VALUES ('{timestamp}',{light},'light not off')''')
                with open(alarmfile, "a") as myfile:
                    myfile.write(f"{timestamp}: Lights should be off but ARE STILL ON lightvalue: {light} ({nlight}/100)\n")
                # sendsms(f'ALARM: Lights should be off but ARE STILL ON lightvalue: {light} ({nlight}/100)')
        if tempsensor.temp > 80:
            if timer() - tempalarm > 3600:
                tempalarm = timer()
                log.warning(f'ALARM: Temp is OVER limit: {tempsensor.temp} F')
                dbupdate(f'''INSERT INTO alarms(timestamp, value, type) VALUES ('{timestamp}',{tempsensor.temp},'over temp')''')
                with open(alarmfile, "a") as myfile:
                    myfile.write(f"{timestamp}: Temp is OVER limit: {tempsensor.temp} F\n")
                # sendsms(f'ALARM: Lights should be off but ARE STILL ON lightvalue: {light} ({nlight}/100)')
        elif tempsensor.temp < 45 and tempsensor.temp != 0:
            if timer() - tempalarm > 3600:
                tempalarm = timer()
                log.warning(f'ALARM: Temp is UNDER limit: {tempsensor.temp} F')
                dbupdate(f'''INSERT INTO alarms(timestamp, value, type) VALUES ('{timestamp}',{tempsensor.temp},'under temp')''')
                with open(alarmfile, "a") as myfile:
                     myfile.write(f"{timestamp}: Temp is UNDER limit: {tempsensor.temp} F\n")
                # sendsms(f'ALARM: Lights should be off but ARE STILL ON lightvalue: {light} ({nlight}/100)')

    except KeyboardInterrupt:
        log.critical(f'Keyboard Interrupt')
        exit(0)
    except:
        log.exception(f'Critical Error')
