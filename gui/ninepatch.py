"""

"""


import pygame
import itertools
import math

import gui


class NinePatch(gui.LinearLayout):
    def __init__(self, image, patch, **kwargs):
        super().__init__(**kwargs)

        self.patch = patch
        rects = self.make_rects(image.get_size())
        self.nine = [pygame.Surface.subsurface(image, rect) for rect in rects]

    def make_rects(self, area):
        w, h = area
        pw, ph = self.patch
        positions = itertools.product((0, pw, w - pw), (0, ph, h - ph))
        sizes = itertools.product((pw, w - 2 * pw, pw), (ph, h - 2 * ph, ph))
        return [pygame.Rect(pos, size) for pos, size in zip(positions, sizes)]

    def fill(self):
        super().fill()
        for i, (nine, rect) in enumerate(zip(self.nine, self.make_rects(self.rect.size))):
            self.surface.blit(nine, rect)
            if i in [1, 3, 4, 5, 7]:
                patch_rect = nine.get_rect(topleft=rect.topleft)
                y_repeat = math.ceil(rect.h / patch_rect.h)
                x_repeat = math.ceil(rect.w / patch_rect.w)
                for _ in range(x_repeat):
                    for _ in range(y_repeat):
                        self.surface.blit(nine, patch_rect)
                        patch_rect.top = patch_rect.bottom
                    patch_rect.top = rect.top
                    patch_rect.left = patch_rect.right


if __name__ == "__main__":
    import resources, room, fonts as f
    nine = NinePatch(resources.load_image('WindowBorder.png'), (70, 70), wait=False, padding=100, layout_gravity=gui.Gravity.FILL)
    nine.add_child(gui.Label("test", f.MAIN))
    nine.add_child(gui.Clock(f.MAIN))
    room.run_room(nine)
