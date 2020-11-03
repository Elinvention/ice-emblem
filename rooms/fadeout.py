import pygame

import room
import gui.tween
import display
import colors as c


class Fadeout(room.Room):
    def __init__(self, duration, stop_mixer=True, percent=1.0, **kwargs):
        super().__init__(wait=False, **kwargs)
        self.duration = duration
        self.clock = 0
        self.stop_mixer = stop_mixer
        self.percent = percent

    def begin(self):
        super().begin()
        if self.stop_mixer:
            pygame.mixer.music.fadeout(self.duration)
        self.fade = display.window.copy()
        self.resize(self.fade.get_size())
        display.tick()

    def loop(self, _events, dt):
        super().loop(_events, dt)
        alpha = int(gui.tween.linear(self.clock, 255, -int(255 * self.percent), self.duration))
        self.fade.set_alpha(alpha)
        self.clock += dt
        self.done = self.clock >= self.duration
        self.valid = False

    def draw(self):
        self.surface.fill(c.BLACK)
        self.surface.blit(self.fade, (0, 0))

    def end(self):
        super().end()
        if self.stop_mixer:
            pygame.mixer.music.stop()
