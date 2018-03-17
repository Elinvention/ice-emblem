import room
import gui
import display
import colors as c


class Fadeout(room.Room):
    def __init__(self, fadeout_time, **kwargs):
        super().__init__(wait=False, **kwargs)
        self.fadeout_time = fadeout_time
        self.clock = 0

    def begin(self):
        self.fade = display.window.copy()
        display.clock.tick(60)

    def loop(self, _events, dt):
        alpha = int(gui.Tween.linear(self.clock, 255, -255, self.fadeout_time))
        self.fade.set_alpha(alpha)
        self.clock += dt
        return alpha < 0

    def draw(self):
        display.window.fill(c.BLACK)
        display.window.blit(self.fade, (0, 0))

