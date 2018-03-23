"""

"""


import math

from .common import TupleOp
from .container import Container


def linear(t, initial, change, duration):
    return initial + change * t / duration

def inQuad(t, initial, change, duration):
    return initial + change * (t / duration) ** 2

def outQuad(t, initial, change, duration):
    t = t / duration
    return initial - change * t * (t - 2)

def inOutQuad(t, initial, change, duration):
    t = t / duration * 2
    if t < 1:
        return initial + change / 2 * (t ** 2)
    return initial - change / 2 * ((t - 1) * (t - 3) - 1)

def outInQuad(t, initial, change, duration):
    if t < duration / 2:
        return Tween.outQuad(t * 2, initial, change / 2, duration)
    return Tween.inQuad((t * 2) - duration, initial + change / 2, change / 2, duration)

def inCubic(t, initial, change, duration):
    return initial + change * (t / duration) ** 3

def outCubic(t, initial, change, duration):
    return initial + change * (((t / duration - 1) ** 3) + 1)

def inOutCubic(t, initial, change, duration):
    t = t / duration * 2
    if t < 1:
        return initial + change / 2 * (t ** 3)
    t = t - 2
    return initial + change / 2 * (t ** 3 + 2)

def outInCubic(t, initial, change, duration):
    if t < duration / 2:
        return Tween.outCubic(t * 2, initial, change / 2, duration)
    return Tween.inCubic((t * 2) - duration, initial + change / 2, change / 2, duration)

def inCirc(t, initial, change, duration):
    return initial - change * (math.sqrt(1 - (t / duration) ** 2) - 1)

def outCirc(t, initial, change, duration):
    return initial + change * math.sqrt(1 - (t / duration - 1) ** 2)

def inOutCirc(t, initial, change, duration):
    t = t / duration * 2
    if t < 1:
        return initial - change / 2 * (math.sqrt(1 - t ** 2) - 1)
    t = t - 2
    return initial + change / 2 * (math.sqrt(1 - t ** 2) + 1)

def outInCirc(t, initial, change, duration):
    if t < duration / 2:
       return Tween.outCirc(t * 2, initial, change / 2, duration)
    return Tween.inCirc((t * 2) - duration, initial + change / 2, change / 2, duration)

easing_functions = [linear] + [f for f in locals() if f.startswith('in') or f.startswith('out')]


class Tween(Container):
    """
    
    """
    def __init__(self, change, duration, **kwargs):
        super().__init__(wait=False, **kwargs)
        self.change = TupleOp(change)
        self.duration = duration
        self.clock = 0
        self.easing = kwargs.get('easing', linear)
        self.callback = kwargs.get('callback', None)
        self.backward = kwargs.get('backward', False)

    def begin(self):
        self.initial = TupleOp(self.rect.topleft)
        self.target = self.initial + TupleOp(self.change)


    def reset(self, *_):
        self.clock = 0
        self.done = False

    def go_backward(self):
        self.backward = not self.backward
        self.done = False

    def loop(self, _events, dt):
        super().loop(_events, dt)
        if self.clock <= 0:
            self.done = self.backward
            self.rect.topleft = self.initial
            if self.done and callable(self.callback):
                self.callback(self)
        elif self.clock < self.duration:
            self.rect.topleft = self.easing(self.clock, self.initial, self.change, self.duration)
        else:
            self.done = not self.backward
            self.rect.topleft = self.target
            if self.done and callable(self.callback):
                self.callback(self)
        self.clock = self.clock - dt if self.backward else self.clock + dt
        return self.done
