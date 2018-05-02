from datetime import timedelta

import gui


class Clock(gui.Label):
    def __init__(self, font, **kwargs):
        super().__init__("0", font, **kwargs)
        self.time = 0
        self.playing = kwargs.get('playing', True)

    def reset(self):
        self.time = 0
        self.playing = False

    def loop(self, _events, dt):
        super().loop(_events, dt)
        if self.playing:
            self.time += dt
            fdate = str(timedelta(seconds=self.time // 1000))
            self.set_text(fdate)
