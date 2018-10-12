"""
Simple widget that displays elapsed time.
"""

import pygame

from datetime import timedelta

import gui
import events


class Clock(gui.Label):
    def __init__(self, font, **kwargs):
        super().__init__("0", font, **kwargs)
        self.time = 0
        self.playing = kwargs.get('playing', True)

    def begin(self):
        super().begin()
        pygame.time.set_timer(events.CLOCK, 1000)

    def reset(self):
        self.time = 0
        self.playing = False

    def loop(self, _events, dt):
        super().loop(_events, dt)
        if self.playing:
            self.time += dt
            fdate = str(timedelta(seconds=self.time // 1000))
            self.set_text(fdate)

    def end(self):
        super().end()
        pygame.time.set_timer(events.CLOCK, 0)
