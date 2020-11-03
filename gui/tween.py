"""

"""


import pygame
import math

from basictypes import Point
from .container import LinearLayout


def linear(t, initial, change, duration):
    return initial + change * t / duration


def in_quad(t, initial, change, duration):
    return initial + change * (t / duration) ** 2


def out_quad(t, initial, change, duration):
    t = t / duration
    return initial - change * t * (t - 2)


def in_out_quad(t, initial, change, duration):
    t = t / duration * 2
    if t < 1:
        return initial + change / 2 * (t ** 2)
    return initial - change / 2 * ((t - 1) * (t - 3) - 1)


def out_in_quad(t, initial, change, duration):
    if t < duration / 2:
        return out_quad(t * 2, initial, change / 2, duration)
    return in_quad((t * 2) - duration, initial + change / 2, change / 2, duration)


def in_cubic(t, initial, change, duration):
    return initial + change * (t / duration) ** 3


def out_cubic(t, initial, change, duration):
    return initial + change * (((t / duration - 1) ** 3) + 1)


def in_out_cubic(t, initial, change, duration):
    t = t / duration * 2
    if t < 1:
        return initial + change / 2 * (t ** 3)
    t = t - 2
    return initial + change / 2 * (t ** 3 + 2)


def out_in_cubic(t, initial, change, duration):
    if t < duration / 2:
        return out_cubic(t * 2, initial, change / 2, duration)
    return in_cubic((t * 2) - duration, initial + change / 2, change / 2, duration)


def in_circ(t, initial, change, duration):
    return initial - change * (math.sqrt(1 - (t / duration) ** 2) - 1)


def out_circ(t, initial, change, duration):
    return initial + change * math.sqrt(1 - (t / duration - 1) ** 2)


def in_out_circ(t, initial, change, duration):
    t = t / duration * 2
    if t < 1:
        return initial - change / 2 * (math.sqrt(1 - t ** 2) - 1)
    t = t - 2
    return initial + change / 2 * (math.sqrt(1 - t ** 2) + 1)


def out_in_circ(t, initial, change, duration):
    if t < duration / 2:
       return out_circ(t * 2, initial, change / 2, duration)
    return in_circ((t * 2) - duration, initial + change / 2, change / 2, duration)


def calculate_pas(c, d, p=None, a=None):
    if not p:
        p = d * 0.3
    if not a:
        a = 0
    if a <= abs(c):
        return p, c, p / 4
    return p, a, p / (2 * math.pi) + math.asin(c / a)


def in_elastic(t, initial, change, duration, a=None, p=None):
    if t == 0:
        return initial
    t = t / duration
    if t == 1:
        return initial + change
    p, a, s = calculate_pas(p=p, a=a, c=change, d=duration)
    t -= 1
    return -(a * 2 ** (10 * t) * math.sin((t * duration - s) * (2 * math.pi) / p)) + initial


def out_elastic(t, initial, change, duration, a=None, p=None):
    if t == 0:
        return initial
    t = t / duration
    if t == 1:
        return initial + change
    p, a, s = calculate_pas(p=p, a=a, c=change, d=duration)
    return a * 2 ** (-10 * t) * math.sin((t * duration - s) * (2 * math.pi) / p) + initial + change


def in_out_elastic(t, initial, change, duration, a=None, p=None):
    if t == 0:
        return initial
    t = t / duration * 2
    if t == 2:
        return initial + change
    p, a, s = calculate_pas(p=p, a=a, c=change, d=duration)
    t -= 1
    if t < 0:
       return -(a * 2 ** (10 * t) * math.sin((t * duration - s) * (2 * math.pi) / p)) / 2 + initial
    return a * 2 ** (-10 * t) * math.sin((t * duration - s) * (2 * math.pi) / p) / 2 + initial + change


def out_in_elastic(t, initial, change, duration, a=None, p=None):
    if t < duration / 2:
        return out_elastic(t * 2, initial, change / 2, duration, a, p)
    return in_elastic((t * 2) - duration, initial + change / 2, change / 2, duration, a, p)


def in_back(t, initial, change, duration, s=1.70158):
    t /= duration
    return change * t * t * ((s + 1) * t - s) + initial


def out_back(t, initial, change, duration, s=1.70158):
    t = t / duration - 1
    return change * (t * t * ((s + 1) * t + s) + 1) + initial


def in_out_back(t, initial, change, duration, s=1.70158):
    s *= 1.525
    t = t / duration * 2
    if t < 1:
        return change / 2 * (t * t * ((s + 1) * t - s)) + initial
    t -= 2
    return change / 2 * (t * t * ((s + 1) * t +s) + 2) + initial


def out_in_back(t, initial, change, duration, s=1.70158):
    if t < duration / 2:
        return out_back(t * 2, initial, change / 2, duration, s)
    return in_back((t * 2) - duration, initial + change / 2, change / 2, duration, s)


def out_bounce(t, initial, change, duration):
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


def in_bounce(t, initial, change, duration):
    return change - out_bounce(duration - t, 0, change, duration) + initial


def in_out_bounce(t, initial, change, duration):
    if t < duration / 2:
        return in_bounce(t * 2, 0, change, duration) / 2 + initial
    return out_bounce(t * 2 - duration, 0, change, duration) / 2 + change / 2 + initial


def out_in_bounce(t, initial, change, duration):
    if t < duration / 2:
        return out_bounce(t * 2, initial, change / 2, duration)
    return in_bounce((t * 2) - duration, initial + change / 2, change / 2, duration)


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

    def measure_vertical(self, spec_width, spec_height):
        w, h = super().measure_vertical(spec_width, spec_height)
        # Lie to our parent because we need space to move!
        self.actual_size = w, h
        return min(spec_width.value, w + abs(self.change.x)), min(spec_height.value, h + abs(self.change.y))

    def layout_children(self, rect):
        # we lied to our parent, but we don't actually need all that space
        if self.change.x < 0:
            rect.left -= self.change.x
        if self.change.y < 0:
            rect.top -= self.change.y
        corrected = rect.clip(pygame.Rect(rect.topleft, self.actual_size))
        super().layout_children(corrected)
        self.initial = Point(rect.topleft)
        self.target = self.initial + self.change
        self.reposition()

    def reset(self, *_):
        self.clock = 0
        self.done = False
        self.playing = False

    def go_backward(self, reset=True):
        self.backward = not self.backward
        self.done = False
        if reset:
            self.reset()

    def reposition(self):
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
        if prev_rect.topleft != self.rect.topleft:
            self.parent.invalidate()
            self.parent.fill(area=prev_rect)

    def loop(self, _events, dt):
        super().loop(_events, dt)
        if not self.playing:
            return
        self.reposition()
        self.clock = self.clock - dt if self.backward else self.clock + dt
