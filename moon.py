from datetime import datetime
import ephem


class astralData():
    def __init__(self):
        self.moondata = {}
        self.seasondata = {}
        self.currentphase = []
        self.nextphase = []
        self.currentseason = []
        self.nextseason = []

    def update(self):
        date = ephem.Date(datetime.now().date())
        self.seasondata.update({'Autumnal (Fall) Equinox': ephem.next_autumn_equinox(date).datetime().date()})
        self.moondata.update({'First Quarter': ephem.next_first_quarter_moon(date).datetime().date()})
        self.moondata.update({'Full Moon': ephem.next_full_moon(date).datetime().date()})
        self.moondata.update({'Last Quarter': ephem.next_last_quarter_moon(date).datetime().date()})
        self.moondata.update({'New Moon': ephem.next_new_moon(date).datetime().date()})
        self.seasondata.update({'Vernal (Spring) Equinox': ephem.next_spring_equinox(date).datetime().date()})
        self.seasondata.update({'Summer Solstice': ephem.next_summer_solstice(date).datetime().date()})
        self.seasondata.update({'Winter Solstice': ephem.next_winter_solstice(date).datetime().date()})
        moon_keys = sorted(self.moondata.keys(), key=lambda y: (self.moondata[y]))
        moon_keys.reverse()
        b = {}
        state1 = True
        while moon_keys:
            a = moon_keys.pop()
            b.update({a: self.moondata[a]})
            if self.moondata[a] != datetime.now().date() and state1:
                self.nextphase = [a, self.moondata[a], daysaway(self.moondata[a])]
                state1 = False
                if self.moondata[a] == datetime.now().date():
                    self.currentphase = a
                ##### elif  
        self.moondata = b
        season_keys = sorted(self.seasondata.keys(), key=lambda y: (self.seasondata[y]))
        season_keys.reverse()
        b = {}
        state2 = True
        while season_keys:
            a = season_keys.pop()
            b.update({a: self.seasondata[a]})
            if self.seasondata[a] != datetime.now().date() and state2:
                self.nextseason = [a, self.seasondata[a], daysaway(self.seasondata[a])]
                state2 = False
        self.seasondata = b
        if self.nextphase[0] == 'Last Quarter' and datetime.now().date() < self.nextphase[1]:
            self.currentphase = 'Waning Gibbus'
        if self.nextphase[0] == 'Last Quarter' and datetime.now().date() == self.nextphase[1]:
            self.currentphase = 'Last Quarter'
        if self.nextphase[0] == 'New Moon' and datetime.now().date() < self.nextphase[1]:
            self.currentphase = 'Waning Crescent'
        if self.nextphase[0] == 'New Moon' and datetime.now().date() == self.nextphase[1]:
            self.currentphase = 'New Moon'
        if self.nextphase[0] == 'First Quarter' and datetime.now().date() < self.nextphase[1]:
            self.currentphase = 'Waxing Crescent'
        if self.nextphase[0] == 'First Quarter' and datetime.now().date() == self.nextphase[1]:
            self.currentphase = 'First Quarter'
        if self.nextphase[0] == 'Full Moon' and datetime.now().date() < self.nextphase[1]:
            self.currentphase = 'Waxing Gibbus'
        if self.nextphase[0] == 'Full Moon' and datetime.now().date() == self.nextphase[1]:
            self.currentphase = 'Full Moon'


def daysaway(ndate):
    return (ndate - datetime.now().date()).days


#astdata = astralData()
#astdata.update()

#while moon_keys:
#    a = moon_keys.pop()
#    print(f'{a} {moondata[a]} {daysaway(moondata[a])} Days away')

#for each in range(1):
#    a = season_keys.pop()
#    print(f'{a} {seasondata[a]} {daysaway(seasondata[a])} Days away')

#print(astdata.currentphase)
#print(astdata.nextphase)
#print(astdata.moondata)
