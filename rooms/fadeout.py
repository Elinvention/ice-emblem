import pygame

import room
import gui
import display
import colors as c


class Fadeout(room.Room):
    def __init__(self, duration, stop_mixer=True, **kwargs):
        super().__init__(wait=False, **kwargs)
        self.duration = duration
        self.clock = 0
        self.stop_mixer = stop_mixer

    def begin(self):
        if self.stop_mixer:
            pygame.mixer.music.fadeout(self.duration)
        self.fade = display.window.copy()
        display.clock.tick(60)

    def loop(self, _events, dt):
        alpha = int(gui.Tween.linear(self.clock, 255, -255, self.duration))
        self.fade.set_alpha(alpha)
        self.clock += dt
        return alpha < 0

    def draw(self):
        display.window.fill(c.BLACK)
        display.window.blit(self.fade, (0, 0))

    def end(self):
        if self.stop_mixer:
            pygame.mixer.music.stop()
