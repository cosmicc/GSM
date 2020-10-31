import board
import neopixel

class stled:
    def __init__(self):
        self.pixel = neopixel.NeoPixel(board.D12, 1, brightness=.1, auto_write=True, pixel_order=neopixel.GRB)
        self.enabled = True

    def green(self):
        if self.enabled:
            self.pixel[0] = (255, 0, 0)
    
    def red(self):
        if self.enabled:
            self.pixel[0] = (0, 255, 0)

    def blue(self):
        if self.enabled:
            self.pixel[0] = (0, 0, 255)

    def cyan(self):
        if self.enabled:
            self.pixel[0] = (255, 0, 255)

    def yellow(self):
        if self.enabled:
            self.pixel[0] = (255, 255, 0)

    def magenta(self):
        if self.enabled:
            self.pixel[0] = (0, 255, 255)

    def off(self):
        if self.enabled:
            self.pixel[0] = (0, 0, 0)

    def disable(self):
        self.enabled = False

    def enable(self):
        self.enabled = True

