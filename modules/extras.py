import subprocess


def c2f(c):
    if c is None:
        return None
    else:
        return float_trunc_1dec((c * 9 / 5) + 32)


def f2c(f):
    if f is None:
        return None
    else:
        return float_trunc_1dec((f - 32) * 5.0/9.0)


def float_trunc_1dec(num):
    try:
        tnum = num // 0.1 / 10
    except:
        return False
    else:
        return tnum
