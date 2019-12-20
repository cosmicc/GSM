import logging
# import pandas as pd
import sqlite3
from datetime import datetime

from flask import Flask, jsonify, redirect, render_template, url_for
from loguru import logger as log
from modules.extras import f2c, float_trunc_1dec
from modules.rpiboard import get_wifi_info
from moon import astralData

app = Flask(__name__)
loggs = logging.getLogger('werkzeug')
# app.logger.disabled = True
# loggs.addHandler(logging.FileHandler('/var/log/access.log'))
# mdb = sqlite3.connect("file::memory:?cache=shared", uri=True)

astdata = astralData()


@app.context_processor
def _convtime():
    def convtime(string):
        datetime_object = datetime.strptime(string, '%Y-%m-%d %H:%M')
        return datetime_object.strftime("%b %d %Y %I:%M%p")
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
        return dbselect('''SELECT timestamp, light, temp, humidity FROM general WHERE name = "livedata"''', fetchall=False)
    return dict(getlivedata=getlivedata)


@app.context_processor
def _getlightdata():
    def getlightdata():
        livedata = dbselect('''SELECT light FROM general WHERE name = "livedata"''', fetchall=False)
        if livedata[0] is not None:
            b = 0 + (100 - 0) * ((livedata[1] - 100000) / (300 - 100000))
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
def _laston():
    def laston():
        return dbselect('''SELECT timestamp, light, temp, humidity FROM general WHERE name = "laston" LIMIT 1''', fetchall=False)
    return dict(laston=laston)


@app.context_processor
def _lastoff():
    def lastoff():
        return dbselect('''SELECT timestamp, light, temp, humidity FROM general WHERE name = "lastoff" LIMIT 1''', fetchall=False)
    return dict(lastoff=lastoff)


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
    try:
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
        if livedata[1] > 300000:
            lightstring = f'All Lights are OFF'
        elif livedata[1] > 1000:
            lightstring = f'Secondary Lights are ON'
        else:
            lightstring = f'All Lights are ON'
        return render_template('index.html', timestamp=livedata[0], light=f'{livedata[1]:,d}', light2=light2, temp=livedata[2], temp2=f2c(livedata[2]), humidity=livedata[3], laston=laston, lastoff=lastoff, lighthours=lighthours[0], currentmoon=astdata.currentphase, nextmoon=astdata.nextphase, moondata=astdata.moondata, npd=td.days, fmd=tr.days, lavg=lavg, tavg=tavg, havg=havg, ttrend=ttrend, htrend=htrend, wifi_info=get_wifi_info(), hasalarms=hasalarms, alarms=alarmdata, lightstring=lightstring)
    except:
        log.exception(f'Error in web index generation')
        return 'Error', 400


@log.catch
@app.route("/data")
def getdata():
    try:
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
    except:
        log.exception(f'Error in web in data generation')
        return 'Error', 400


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
