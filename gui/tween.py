"""

"""


import math

from basictypes import Point
from .container import LinearLayout


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
        return outQuad(t * 2, initial, change / 2, duration)
    return inQuad((t * 2) - duration, initial + change / 2, change / 2, duration)

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
        return outCubic(t * 2, initial, change / 2, duration)
    return inCubic((t * 2) - duration, initial + change / 2, change / 2, duration)

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
       return outCirc(t * 2, initial, change / 2, duration)
    return inCirc((t * 2) - duration, initial + change / 2, change / 2, duration)

def calculatePAS(c, d, p=None, a=None):
    if not p:
        p = d * 0.3
    if not a:
        a = 0
    if a <= abs(c):
        return p, c, p / 4
    return p, a, p / (2 * math.pi) + math.asin(c / a)

def inElastic(t, initial, change, duration, a=None, p=None):
    if t == 0:
        return initial
    t = t / duration
    if t == 1:
        return initial + change
    p, a, s = calculatePAS(p=p, a=a, c=change, d=duration)
    t -= 1
    return -(a * 2 ** (10 * t) * math.sin((t * duration - s) * (2 * math.pi) / p)) + initial

def outElastic(t, initial, change, duration, a=None, p=None):
    if t == 0:
        return initial
    t = t / duration
    if t == 1:
        return initial + change
    p, a, s = calculatePAS(p=p, a=a, c=change, d=duration)
    return a * 2 ** (-10 * t) * math.sin((t * duration - s) * (2 * math.pi) / p) + initial + change

def inOutElastic(t, initial, change, duration, a=None, p=None):
    if t == 0:
        return initial
    t = t / duration * 2
    if t == 2:
        return initial + change
    p, a, s = calculatePAS(p=p, a=a, c=change, d=duration)
    t -= 1
    if t < 0:
       return -(a * 2 ** (10 * t) * math.sin((t * duration - s) * (2 * math.pi) / p)) / 2 + initial
    return a * 2 ** (-10 * t) * math.sin((t * duration - s) * (2 * math.pi) / p) / 2 + initial + change

def outInElastic(t, initial, change, duration, a=None, p=None):
    if t < duration / 2:
        return outElastic(t * 2, initial, change / 2, duration, a, p)
    return inElastic((t * 2) - duration, initial + change / 2, change / 2, duration, a, p)

def inBack(t, initial, change, duration, s=1.70158):
    t /= duration
    return change * t * t * ((s + 1) * t - s) + initial

def outBack(t, initial, change, duration, s=1.70158):
    t = t / duration - 1
    return change * (t * t * ((s + 1) * t + s) + 1) + initial

def inOutBack(t, initial, change, duration, s=1.70158):
    s *= 1.525
    t = t / duration * 2
    if t < 1:
        return change / 2 * (t * t * ((s + 1) * t - s)) + initial
    t -= 2
    return change / 2 * (t * t * ((s + 1) * t +s) + 2) + initial

def outInBack(t, initial, change, duration, s=1.70158):
    if t < duration / 2:
        return outBack(t * 2, initial, change / 2, duration, s)
    return inBack((t * 2) - duration, initial + change / 2, change / 2, duration, s)

def outBounce(t, initial, change, duration):
    t = t / duration
    if t < 1 / 2.75:
        return change * (7.5625 * t * t) + initial
    if t < 2 / 2.75:
        t -= 1.5 / 2.75
        return change * (7.5625 * t * t + 0.75) + initial
    if t < 2.5 / 2.75:
        t -= 2.25 / 2.75
        return change * (7.5625 * t * t + 0.9375) + initial
    t -= 2.625 / 2.75
    return change * (7.5625 * t * t + 0.984375) + initial

def inBounce(t, initial, change, duration):
    return change - outBounce(duration - t, 0, change, duration) + initial

def inOutBounce(t, initial, change, duration):
    if t < duration / 2:
        return inBounce(t * 2, 0, change, duration) / 2 + initial
    return outBounce(t * 2 - duration, 0, change, duration) / 2 + change / 2 + initial

def outInBounce(t, initial, change, duration):
    if t < duration / 2:
        return outBounce(t * 2, initial, change / 2, duration)
    return inBounce((t * 2) - duration, initial + change / 2, change / 2, duration)


easing_functions = [linear] + [f for name, f in locals().items() if name.startswith('in') or name.startswith('out')]


class Tween(LinearLayout):
    """
    
    """
    def __init__(self, change, duration, **kwargs):
        super().__init__(wait=False, **kwargs)
        self.change = Point(change)
        self.duration = duration
        self.clock = 0
        self.easing = kwargs.get('easing', linear)
        self.callback = kwargs.get('callback', None)
        self.backward = kwargs.get('backward', False)
        self.playing = False

    def layout_children(self, rect):
        super().layout_children(rect)
        self.initial = Point(rect.topleft)
        self.target = self.initial + self.change

    def reset(self, *_):
        self.clock = 0
        self.done = False
        self.playing = False

    def go_backward(self, reset=True):
        self.backward = not self.backward
        self.done = False
        if reset:
            self.reset()

    def loop(self, _events, dt):
        super().loop(_events, dt)
        if not self.playing:
            return
        prev_rect = self.rect.copy()
        if self.clock <= 0:
            self.done = self.backward
            self.rect.topleft = self.initial
            if self.done and callable(self.callback):
                self.callback(self)
        elif self.clock < self.duration:
            self.rect.left = int(self.easing(self.clock, self.initial[0], self.change[0], self.duration))
            self.rect.top = int(self.easing(self.clock, self.initial[1], self.change[1], self.duration))
            #self.rect.topleft = self.easing(self.clock, self.initial, self.change, self.duration)
        else:
            self.done = not self.backward
            self.rect.topleft = self.target
            if self.done and callable(self.callback):
                self.callback(self)
        self.clock = self.clock - dt if self.backward else self.clock + dt

        if prev_rect.topleft != self.rect.topleft:
            self.parent.invalidate()
            self.parent.fill(area=prev_rect)
