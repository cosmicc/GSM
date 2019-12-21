
import sqlite3
import logging
from configparser import ConfigParser
from datetime import datetime

from flask import Flask, jsonify, redirect, render_template, url_for
from loguru import logger as log
from modules.extras import f2c, float_trunc_1dec
from modules.rpiboard import get_wifi_info
from moon import astralData

config = ConfigParser()
config.read('/etc/gsm.conf')

DARK_THRESHOLD = int(config.get('light', 'dark_threshold'))
HIDLIGHT_THRESHOLD = int(config.get('light', 'hidlight_threshold'))

app = Flask(__name__)
loggs = logging.getLogger('werkzeug')
# app.logger.disabled = True
# loggs.addHandler(logging.FileHandler('/var/log/access.log'))
# mdb = sqlite3.connect("file::memory:?cache=shared", uri=True)

astdata = astralData()

intervals = (
    ("years", 31536000),
    ("months", 2592000),
    # ('weeks', 604800),  # 60 * 60 * 24 * 7
    ("days", 86400),  # 60 * 60 * 24
    ("hours", 3600),  # 60 * 60
    ("minutes", 60),
    ("seconds", 1),
)


def datetimeto(dt, fmt):
    """Convert datetime object
    Args:
        dt (TYPE): Description:
        fmt (TYPE): Description:
        est (bool, [Optional]): Description:
    Returns:
        TYPE: Description:
    """
    if fmt == "epoch":
        return int(dt.timestamp())
    elif fmt == "string":
        return dt.strftime("%a, %b %d, %Y %I:%M %p")


def elapsedTime(start_time, stop_time, append=False):
    """Convert 2 epochs to elapsed time string representation
    Args:
        start_time (string, int, float, datetime): Description: Start time
        stop_time (string, int, float, datetime): Description:  End time
        nowifmin (bool, [Optional]): Description: If less then 1 minute return 'Now'
    Returns:
        STRING: Description: e.g. '1 Hour, 47 Minutes'
    """
    if isinstance(start_time, datetime):
        start_time = datetimeto(start_time, fmt='epoch')
    if isinstance(stop_time, datetime):
        stop_time = datetimeto(stop_time, fmt='epoch')
    result = []
    if start_time > stop_time:
        seconds = int(start_time) - int(stop_time)
    else:
        seconds = int(stop_time) - int(start_time)
    if seconds > 60 and seconds < 3600:
        granularity = 1
    else:
        granularity = 2
    for name, count in intervals:
        value = seconds // count
        if value:
            seconds -= value * count
            if value == 1:
                name = name.rstrip("s")
            result.append("{} {}".format(int(value), name))
    else:
        if append:
            return ", ".join(result[:granularity]) + f" {append}"
        else:
            return ", ".join(result[:granularity])


@app.context_processor
def _current_datestamp():
    def current_datestamp():
        return datetime.now().strftime("%a, %b %d %I:%M %p")
    return dict(current_datestamp=current_datestamp)


@app.context_processor
def _convtime():
    def convtime(string):
        datetime_object = datetime.strptime(string, '%Y-%m-%d %H:%M')
        return datetime_object.strftime("%a, %b %d %I:%M %p")
    return dict(convtime=convtime)


@app.context_processor
def _convdate():
    def convdate(string):
        datetime_object = datetime.strptime(string, '%Y-%m-%d')
        return datetime_object.strftime("%b %d %Y")
    return dict(convdate=convdate)


@log.catch
def dbupdate(cmd):
    try:
        db = sqlite3.connect('/var/opt/lightdata.db')
        cursor = db.cursor()
        cursor.execute(cmd)
        db.commit()
        db.close()
    except:
        log.exception('Error updating DB')


@log.catch
def dbselect(cmd, fetchall=True):
    try:
        db = sqlite3.connect('/var/opt/lightdata.db')
        cursor = db.cursor()
        cursor.execute(cmd)
        if not fetchall:
            a = cursor.fetchone()
        else:
            a = cursor.fetchall()
        db.close()
    except:
        log.exception('Error querying DB')
    else:
        return a


@app.context_processor
def _getlivedata():
    def getlivedata():
        livedata = dbselect('''SELECT timestamp, light, temp, humidity FROM general WHERE name = "livedata"''', fetchall=False)
        last30 = dbselect('''SELECT light, temp, humidity FROM data ORDER BY id DESC LIMIT 12''', fetchall=True)
        t = []
        h = []
        for each in last30:
            t.append(each[1])
            h.append(each[2])
        tavg = float_trunc_1dec(sum(t) / len(t))
        havg = float_trunc_1dec(sum(h) / len(h))
        ttrend = float_trunc_1dec(livedata[2] - tavg)
        htrend = float_trunc_1dec(livedata[3] - havg)
        if ttrend > 0:
            ttrend = f'+{ttrend}'
        if htrend > 0:
            htrend = f'+{htrend}'
        return {'timestamp': livedata[0], 'light': livedata[1], 'temp': livedata[2], 'humidity': livedata[3], 'ttrend': ttrend, 'htrend': htrend}
    return dict(getlivedata=getlivedata)


@app.context_processor
def _getweatherdata():
    def getweatherdata():
        return dbselect('''SELECT tempnow, temphi, templow, humidity, weather, sunrise, sunset FROM outside WHERE name = "current"''', fetchall=False)
    return dict(getweatherdata=getweatherdata)


@log.catch
@app.context_processor
def _getlightstring():
    def getlightstring():
        livedata = dbselect('''SELECT light FROM general WHERE name = "livedata"''', fetchall=False)
        if livedata[1] > 300000:
            return 'All Lights are OFF'
        elif livedata[1] > 1000:
            return 'Secondary Lights are ON'
        else:
            return 'All Lights are ON'
    return dict(getlightstring=getlightstring)


@log.catch
@app.context_processor
def _getlightdata():
    def getlightdata():
        livedata = dbselect('''SELECT light FROM general WHERE name = "livedata"''', fetchall=False)
        if livedata is not None:
            b = 0 + (100 - 0) * ((livedata[0] - 100000) / (300 - 100000))
            if int(b) < 0:
                light2 = 0
            elif int(b) > 100:
                light2 = 100
            else:
                light2 = int(b)
        else:
            light2 = 'N/A'
        return light2
    return dict(getlightdata=getlightdata)


@app.context_processor
def _getastdata():
    def getastdata():
        astdata.update()
        return astdata
    return dict(getastdata=getastdata)


@app.context_processor
def _getmoontime():
    def getmoontime():
        astdata.update()
        td = astdata.nextphase[1] - datetime.now().date()
        tr = astdata.moondata["Full Moon"] - datetime.now().date()
        return [td.days, tr.days]
    return dict(getmoontime=getmoontime)


@app.context_processor
def _getlaston():
    def getlaston():
        return dbselect('''SELECT timestamp, light, temp, humidity FROM general WHERE name = "laston" LIMIT 1''', fetchall=False)
    return dict(getlaston=getlaston)


@app.context_processor
def _getlasthidon():
    def getlasthidon():
        return dbselect('''SELECT timestamp, light, temp, humidity FROM general WHERE name = "lasthidon" LIMIT 1''', fetchall=False)
    return dict(getlasthidon=getlasthidon)


@app.context_processor
def _getlasthidoff():
    def getlasthidoff():
        return dbselect('''SELECT timestamp, light, temp, humidity FROM general WHERE name = "lasthidoff" LIMIT 1''', fetchall=False)
    return dict(getlasthidoff=getlasthidoff)


@app.context_processor
def _getlastonhours():
    def getlastonhours():
        tme = dbselect('''SELECT timestamp FROM general WHERE name = "laston" LIMIT 1''', fetchall=False)
        return elapsedTime(datetime.now(), datetime.strptime(tme[0], '%Y-%m-%d %H:%M'))
    return dict(getlastonhours=getlastonhours)


@app.context_processor
def _getlastoffhours():
    def getlastoffhours():
        tme = dbselect('''SELECT timestamp FROM general WHERE name = "lastoff" LIMIT 1''', fetchall=False)
        return elapsedTime(datetime.now(), datetime.strptime(tme[0], '%Y-%m-%d %H:%M'))
    return dict(getlastoffhours=getlastoffhours)


@app.context_processor
def _getlastoff():
    def getlastoff():
        return dbselect('''SELECT timestamp, light, temp, humidity FROM general WHERE name = "lastoff" LIMIT 1''', fetchall=False)
    return dict(getlastoff=getlastoff)


@log.catch
@app.context_processor
def _statpull():
    def ui_last24avg(inst, dtype):
        if dtype == 'chart1':
            hours = 2
            rate = '10T'
            tstr = '%I:%M%p'
        elif dtype == 'chart2':
            hours = 24
            rate = 'H'
            tstr = '%-I%p'
        elif dtype == 'chart4':
            hours = 192
            rate = 'D'
            tstr = '%a'
        elif dtype == 'chart3':
            hours = 720
            rate = 'D'
            tstr = '%b %-d'
        conn = sqlite3.connect('/var/opt/lightdata.db')
        df = pd.read_sql("SELECT * FROM data WHERE ORDER BY id DESC LIMIT 86400".format(datetime.now() - timedelta(hours=hours)), conn, parse_dates=['date'], index_col='date')
        conn.close()
        df = df.resample(rate).mean()
        datelist = []
        for each in df.index:
            datelist.append(each.strftime(tstr))
        return (datelist, list(chain.from_iterable(df.values.round(1).tolist())))
    return dict(ui_last24avg=ui_last24avg)


@log.catch
@app.route("/")
def index():
    db = sqlite3.connect('/var/opt/lightdata.db')
    cursor = db.cursor()
    cursor.execute('''SELECT timestamp, light, temp, humidity FROM general WHERE name = "livedata"''')
    livedata = cursor.fetchone()
    cursor.execute('''SELECT timestamp, value, type FROM alarms ORDER BY id DESC LIMIT 10''')
    alarmdata = cursor.fetchall()
    cursor.execute('''SELECT timestamp, light, temp, humidity FROM general WHERE name = "laston" LIMIT 1''')
    laston = cursor.fetchone()
    cursor.execute('''SELECT timestamp, light, temp, humidity FROM general WHERE name = "lastoff" LIMIT 1''')
    lastoff = cursor.fetchone()
    cursor.execute('''SELECT light, temp, humidity FROM data ORDER BY id DESC LIMIT 12''')
    last30 = cursor.fetchall()
    cursor.execute('''SELECT temp FROM general WHERE name = "lighthours"''')
    lighthours = cursor.fetchone()
    db.close()
    astdata.update()
    lp = []
    t = []
    h = []
    for each in last30:
        lp.append(each[0])
        t.append(each[1])
        h.append(each[2])
    lavg = int(sum(lp) / len(lp))
    tavg = float_trunc_1dec(sum(t) / len(t))
    havg = float_trunc_1dec(sum(h) / len(h))
    if livedata is not None:
        log.debug(f'Livedata: {livedata}')
        b = 0 + (100 - 0) * ((livedata[1] - 100000) / (300 - 100000))
        if int(b) < 0:
            light2 = 0
        elif int(b) > 100:
            light2 = 100
        else:
            light2 = int(b)
    else:
        light2 = 'N/A'
    td = astdata.nextphase[1] - datetime.now().date()
    tr = astdata.moondata["Full Moon"] - datetime.now().date()
    if len(alarmdata) > 0:
        hasalarms = True
    else:
        hasalarms = False
    ttrend = float_trunc_1dec(livedata[2] - tavg)
    htrend = float_trunc_1dec(livedata[3] - havg)
    if ttrend > 0:
        ttrend = f'+{ttrend}'
    if htrend > 0:
        htrend = f'+{htrend}'
    if livedata[1] > DARK_THRESHOLD:
        lightstring = f'All Lights are OFF'
    elif livedata[1] > HIDLIGHT_THRESHOLD:
        lightstring = f'All Lights are ON'
    else:
        lightstring = f'Secondary Lights are ON'

    return render_template('index.html', timestamp=livedata[0], light=f'{livedata[1]:,d}', light2=light2, temp=livedata[2], temp2=f2c(livedata[2]), humidity=livedata[3], laston=laston, lastoff=lastoff, lighthours=lighthours[0], currentmoon=astdata.currentphase, nextmoon=astdata.nextphase, moondata=astdata.moondata, npd=td.days, fmd=tr.days, lavg=lavg, tavg=tavg, havg=havg, ttrend=ttrend, htrend=htrend, wifi_info=get_wifi_info(), hasalarms=hasalarms, alarms=alarmdata, lightstring=lightstring)


@log.catch
@app.route("/data")
def getdata():
    db = sqlite3.connect('/var/opt/lightdata.db')
    cursor = db.cursor()
    cursor.execute('''SELECT timestamp, light, temp, humidity FROM general WHERE name = "livedata"''')
    livedata = cursor.fetchone()
    cursor.execute('''SELECT timestamp, value, type FROM alarms ORDER BY id DESC LIMIT 1''')
    alarmdata = cursor.fetchone()
    cursor.execute('''SELECT light, temp, humidity FROM data ORDER BY id DESC LIMIT 12''')
    last30 = cursor.fetchall()
    cursor.execute('''SELECT temp FROM general WHERE name = "lighthours"''')
    lighthours = cursor.fetchone()
    db.close()
    lp = []
    t = []
    h = []
    for each in last30:
        lp.append(each[0])
        t.append(each[1])
        h.append(each[2])
    try:
        lavg = int(sum(lp) / len(lp))
        tavg = float_trunc_1dec(sum(t) / len(t))
        havg = float_trunc_1dec(sum(h) / len(h))
    except:
        lavg = 1
        tavg = 1
        havg = 1
    if livedata[1] is not None:
        b = 0 + (100 - 0) * ((livedata[1] - 100000) / (300 - 100000))
        if int(b) < 0:
            light2 = 0
        elif int(b) > 100:
            light2 = 100
        else:
            light2 = int(b)
    else:
        light2 = 'N/A'
    if alarmdata is not None:
        hasalarms = True
    else:
        hasalarms = False
    ttrend = float_trunc_1dec(livedata[2] - tavg)
    htrend = float_trunc_1dec(livedata[3] - havg)
    if ttrend > 0:
        ttrend = f'+{ttrend}'
    if htrend > 0:
        htrend = f'+{htrend}'
    resp = {'timestamp': livedata[0], 'darkness': f'{livedata[1]}', 'lightscale': light2, 'tempc': livedata[2], 'tempf': f2c(livedata[2]), 'humidity': livedata[3], 'lighthours': lighthours[0], 'lightavg': lavg, 'tempavg': tavg, 'humidityavg': havg, 'temptrend': ttrend, 'humiditytrend': htrend, 'hasalarms': hasalarms, 'alarms': alarmdata}
    return jsonify(resp)


@log.catch
@app.route('/stats')
def _stats():
    return render_template('stats.html')


@log.catch
@app.route('/clearalarms')
def _clearalaarms():
    dbupdate('''DELETE from alarms''')
    return redirect(url_for('index'))


@log.catch
def web():
    app.run(host='0.0.0.0', port=80)
