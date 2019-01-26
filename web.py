import logging
# import pandas as pd
import sqlite3

from flask import Flask, redirect, render_template, url_for
from loguru import logger as log

app = Flask(__name__)
loggs = logging.getLogger('werkzeug')
# app.logger.disabled = True
# loggs.addHandler(logging.FileHandler('/var/log/access.log'))


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
        if fetchall == False:
            a = cursor.fetchone()
        else:
            a = cursor.fetchall()
        db.close()
    except:
        log.exception('Error querying DB')
    else:
        return a


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
        livedata = dbselect('''SELECT timestamp, light, temp, humidity FROM data ORDER BY id DESC LIMIT 1''', fetchall=False)
        alarmdata = dbselect('''SELECT timestamp, value, type FROM alarms ORDER BY id DESC LIMIT 10''', fetchall=True)
        # print(livedata)
        b = 0 + (100 - 0) * ((livedata[1] - 250000) / (0 - 250000))
        return render_template('index.html', timestamp=livedata[0], light=f'{livedata[1]:,d}', light2=int(b), temp=livedata[2], humidity=livedata[3], alarms=alarmdata)
    except:
        log.exception(f'Error in web index generation')
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
