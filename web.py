from flask import Flask, render_template
#import pandas as pd
import sqlite3

app = Flask(__name__)

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


@app.route("/")
def index():
    db = sqlite3.connect('/var/opt/lightdata.db')
    cursor = db.cursor()
    cursor.execute('''SELECT timestamp, light, temp, humidity FROM data ORDER BY id DESC LIMIT 1''')
    a = cursor.fetchone()
    cursor.execute('''SELECT timestamp, light, type FROM alarms ORDER BY id DESC LIMIT 10''')
    d = cursor.fetchall()
    db.close()
    b = 0 + (100 - 0) * ((a[1] - 250000) / (0 - 250000))
    return render_template('index.html', livedata=f'{a[0]} - Light: {a[1]:,d} ({int(b)}/100)  Temp: {a[2]}C  Humidity: {a[3]}%', alarms=d)

@app.route('/stats')
def _stats(inst):
    return render_template('stats.html')

def web():
	app.run(host='0.0.0.0', port=80)
