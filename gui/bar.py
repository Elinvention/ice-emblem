"""

"""


import pygame

import room
import colors as c


class LifeBar(room.Room):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._points = kwargs.get('points', 100)
        self._value = kwargs.get('value', self.points)
        self.block_size = kwargs.get('block_size', (12, 20))
        self.blocks_per_row = kwargs.get('blocks_per_row', 10)
        self.spacing = kwargs.get('spacing', (1, 1))
        self._life = pygame.Surface(self.block_size)
        self._damage = self._life.copy()
        self._life.fill(kwargs.get('life_color', c.GREEN))
        self._damage.fill(kwargs.get('damage_color', c.RED))

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, _value):
        self._value = _value
        self.invalidate()

    @property
    def points(self):
        return self._points

    @points.setter
    def points(self, _points):
        self._points = _points
        self.invalidate()
        self.layout_request()

    def measure(self, spec_width, spec_height):
        w = min(self.points, self.blocks_per_row) * (self.block_size[0] + self.spacing[0])
        h = (((self.points - 1) // self.blocks_per_row) + 1) * (self.block_size[1] + self.spacing[1])
        self.resolve_measure(spec_width, spec_height, w, h)

    def draw(self):
        self.surface.fill((0, 0, 0, 0))
        for i in range(self.points):
            x = (i % self.blocks_per_row) * (self.block_size[0] + self.spacing[0])
            y = (i // self.blocks_per_row) * (self.block_size[1] + self.spacing[1])
            if i < self._value % (self.points + 1):
                self.surface.blit(self._life, (x, y))
            else:
                self.surface.blit(self._damage, (x, y))


if __name__ == "__main__":
    import gui
    import logging
    import fonts as f
    import display

    logging.basicConfig(level=logging.DEBUG)
    display.initialize()

    class TestLifeBar(gui.LinearLayout):
        def __init__(self):
            self.bar = LifeBar(points=11)
            self.label = gui.Label("{0}/{1}", f.SMALL, layout=room.Layout(width=100))
            self.label.format(self.bar.value, self.bar.points)
            super().__init__(wait=True, children=[self.bar, self.label], orientation=gui.Orientation.HORIZONTAL)

        def handle_keydown(self, event: pygame.event.Event):
            if event.key == pygame.K_UP:
                self.bar.value += 1
            elif event.key == pygame.K_DOWN:
                self.bar.value -= 1
            elif event.key == pygame.K_LEFT:
                if self.bar.points > 1:
                    self.bar.points -= 1
            elif event.key == pygame.K_RIGHT:
                self.bar.points += 1
            self.label.format(self.bar.value, self.bar.points)

    room.run_room(TestLifeBar())
