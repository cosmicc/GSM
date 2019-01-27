from datetime import datetime
import ephem

moondata = {}

date=ephem.Date(datetime.now().date())

moondata.update({'next_autumn_equinox': ephem.next_autumn_equinox(date).datetime()})
moondata.update({'next_atumnal_equinox': ephem.next_autumnal_equinox(date).datetime()})
moondata.update({'next_equinox': ephem.next_equinox(date).datetime()})
moondata.update({'next_fall_equinox': ephem.next_fall_equinox(date).datetime()})
moondata.update({'next_first_quarter_moon': ephem.next_first_quarter_moon(date).datetime()})
moondata.update({'next_full_moon': ephem.next_full_moon(date).datetime()})
moondata.update({'next_last_quarter_moon': ephem.next_last_quarter_moon(date).datetime()})
moondata.update({'next_new_moon': ephem.next_new_moon(date).datetime()})
moondata.update({'next_solstice': ephem.next_solstice(date).datetime()})
moondata.update({'next_spring_equinox': ephem.next_spring_equinox(date).datetime()})
moondata.update({'next_summer_solstice': ephem.next_summer_solstice(date).datetime()})
moondata.update({'next_vernal_equinox': ephem.next_vernal_equinox(date).datetime()})
moondata.update({'next_winter_solstice': ephem.next_winter_solstice(date).datetime()})

'''
print(f'next_autumn_equinox: {next_autumn_equinox}')
print(f'next_equinox: {next_equinox}')
print(f'next_fall_equinox: {next_fall_equinox}')
print(f'next_first_quarter_moon: {next_first_quarter_moon}')
print(f'next_full_moon: {next_full_moon}')
print(f'next_last_quarter_moon: {next_last_quarter_moon}')
print(f'next_new_moon: {next_new_moon}')
print(f'next_solstice: {next_solstice}')
print(f'next_spring_equinox: {next_spring_equinox}')
print(f'next_summer_solstice: {next_summer_solstice}')
print(f'next_vernal_equinox: {next_vernal_equinox}')
print(f'next_winter_solstice: {next_winter_solstice}')
'''


sorted_keys = sorted(moondata.keys(), key=lambda y: (moondata[y]))

print(sorted_keys)
