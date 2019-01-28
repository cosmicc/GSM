from os import getenv, getloadavg, popen, uname
from subprocess import PIPE, Popen, check_output

import netifaces as ni
from modules.extras import float_trunc_1dec


def is_root():
    if getenv("SUDO_USER") is None:
        return False
    else:
        return True


def is_rpi():
    funame = uname()
    if funame[4][:3] == 'arm':
        return True
    else:
        return False


def is_zero():
    if 'Zero' in rpi_board():
        return True
    else:
        return False


def get_ip_address():
    return ni.ifaddresses('wlan0')[ni.AF_INET][0]['addr']


def rpi_mem():
    memory = {}
    armmem = check_output(['/usr/bin/vcgencmd', 'get_mem', 'arm'], shell=False)
    gpumem = check_output(['/usr/bin/vcgencmd', 'get_mem', 'gpu'], shell=False)
    memory.update({'system': armmem, 'gpu': gpumem})
    return memory


def rpi_board():
    try:
        file = open('/sys/firmware/devicetree/base/model', 'r')
        model = file.read()
        file.close()
    except:
        return None
    else:
        return model.rstrip('\x00')


def enable_hdmi():
    try:
        check_output(['/usr/bin/tvservice', '-p'], shell=False)
    except:
        return False
    else:
        return True


def disable_hdmi():
    try:
        check_output(['/usr/bin/tvservice', '-o'], shell=False)
    except:
        return False
    else:
        return True


def get_load():
    a = {}
    x = getloadavg()
    a.update({'1min': x[0]})
    a.update({'5min': x[1]})
    a.update({'15min': x[2]})
    return a


def get_freemem():
    fm = Popen(['/usr/bin/free', '-h'], stdout=PIPE)
    i = 0
    freemem = {}
    while True:
        i += 1
        line = str(fm.stdout.readline())
        if i == 2:
            line = line.split()
            freemem.update({'total': line[1], 'used': line[2], 'free': line[3], 'available': line[6].strip("\\n'")})
        if i == 3:
            line = line.split()
            freemem.update({'swap': line[2]})
            return freemem


def get_diskspace():
    ds = Popen(['/bin/df', '-h', '/'], stdout=PIPE)
    i = 0
    diskspace = {}
    while True:
        i += 1
        line = str(ds.stdout.readline())
        if i == 2:
            line = line.split()
            diskspace.update({'size': line[1], 'available': line[3], 'used': line[2], 'used_percent': line[4]})
            return diskspace


def rpi_info():
    rpiinfo = {}
    runame = uname()
    cores = 0
    rpiinfo.update({'system': runame[0], 'release': runame[2], 'version': runame[3], 'machine': runame[4], 'board': rpi_board()})
    cpuinfofile = open('/proc/cpuinfo')
    for line in cpuinfofile:
        line = line.split(':')
        if line[0].startswith('Serial'):
            rpiinfo.update({'serial': line[1].strip('\n').strip()})
        elif line[0].startswith('Hardware'):
            rpiinfo.update({'hardware': line[1].strip('\n').strip()})
        elif line[0].startswith('processor'):
            cores += 1
        elif line[0].startswith('Revision'):
            rpiinfo.update({'revision': line[1].strip('\n').strip()})
        elif line[0].startswith('model name'):
            rpiinfo.update({'cpu_model': line[1].strip('\n').strip()})
    cpuinfofile.close()
    rpiinfo.update({'cores': cores})
    return rpiinfo


class Led(object):
    def __init__(self, ledtype):
        self.ledtype = ledtype
        if is_zero():
            self.fon = '0'
            self.foff = '1'
        else:
            self.fon = '1'
            self.foff = '0'
        if self.ledtype == 'status' or self.ledtype == 'st':
            self.led = 'led0'
        elif self.ledtype == 'power' or self.ledtype == 'pwd':
            self.led = 'led1'
        else:
            raise NameError('Invalid onboard LED specified')
        # if not is_root():
        #    raise RuntimeError("Controlling onboard LED's requires ROOT")
        trig = open('/sys/class/leds/{}/trigger'.format(self.led), 'w')
        trig.write('none')
        trig.close()
        check_output(['modprobe', 'ledtrig_heartbeat'], shell=False)

    def ledon(self):
        lo = open('/sys/class/leds/{}/brightness'.format(self.led), 'w')
        lo.write(self.fon)
        lo.close()

    def ledoff(self):
        noop = open('/sys/class/leds/{}/trigger'.format(self.led), 'w')
        noop.write('none')
        noop.close()
        loff = open('/sys/class/leds/{}/brightness'.format(self.led), 'w')
        loff.write(self.foff)
        loff.close()

    def ledflash(self):
        fla = open('/sys/class/leds/{}/trigger'.format(self.led), 'w')
        fla.write('heartbeat')
        fla.close()


def cpu_temp():
    tempu = popen("vcgencmd measure_temp").readline()
    tempu = tempu.replace("temp=", "")
    tempu = tempu.replace("'C", "")
    return float_trunc_1dec(float(tempu))


def system_uptime():
    ut = check_output(['uptime', '-p'], shell=False).decode("utf-8").strip()
    ur = ut.split('up ')
    return ur[1]


def get_release():
    y = {}
    a = check_output(['lsb_release', '-a'])
    a = a.split(b'\n')
    for each in a:
        if each != b'':
            p = each.split(b'\t')
            y.update({p[0][:-1].decode('UTF-8'): p[1].decode('UTF-8')})
    return y


def get_cpuspeed():
    a = check_output(['vcgencmd', 'measure_clock', 'arm'])
    a = a.split(b'=')
    a = int(a[1].decode('UTF-8').strip()) / 1000000
    return f'{int(a)}Mhz'


def get_throttled():
    a = check_output(['vcgencmd', 'get_throttled'])
    a = a.split(b'=')
    return a[1].decode('UTF-8').strip()


def get_swap():
    a = check_output(['cat', '/proc/swaps'])
    a = a.decode('UTF-8').split('\n')[1].split('\t')
    return int(int(a[3]) / 1000), int(int(a[2]) / 1000)


def get_wifi_info():
    child = subprocess.Popen(['iwconfig'], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, shell=False)
    streamdata = child.communicate()[0].decode('UTF-8').split('\n')
    if child.returncode == 0:
        for each in streamdata:
            if each.find('ESSID:') != -1:
                ssid = each.split(':')[1].replace('"', '').strip()
            elif each.find('Frequency') != -1:
                apmac = each.split('Access Point: ')[1].strip()
                channel = each.split('Frequency:')[1].split(' Access Point:')[0].strip()
            elif each.find('Link Quality') != -1:
                linkqual = each.split('=')[1].split(' Signal level')[0].strip()
                signal = int(each.split('=')[2].split(' ')[0].strip())
                # -80 -30  0 100
                signal_percent = int(0 + (100 - 0) * ((signal - -80) / (-35 - -80)))
                if signal_percent > 100:
                    signal_percent = 100
            elif each.find('Bit Rate') != -1:
                bitrate = each.split('=')[1].split('Tx-Power')[0].strip()

        return {'ssid': ssid, 'apmac': apmac, 'channel': channel, 'signal': signal, 'signal_percent': signal_percent, 'quality': linkqual, 'bitrate': bitrate}
    else:
        return False
