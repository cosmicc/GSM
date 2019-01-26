#!/usr/bin/env python3.7

import SI1145.si1145 as SI1145
import os
from time import sleep

values = {}

si = SI1145.SI1145()

while True:
    light = si.readVisible()
    ir = si.readIR()
    uv = si.readUV()

    values.update({'uv': uv, 'ir': ir, 'light': light})

    print(values)
    sleep(10)
