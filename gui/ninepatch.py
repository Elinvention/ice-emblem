"""

"""


import pygame
import itertools
import math

import gui

from typing import Tuple, List


class NinePatch(gui.LinearLayout):
    """
    This class implements a simple NinePatch texture.
    """
    def __init__(self, image: pygame.Surface, corners_size: Tuple[int, int], **kwargs):
        """
        Build a NinePatch background.
        :param image: NinePatch texture
        :param patch: A tuple of 2 ints that represents the corners' size. The 4 corners are assumed to have the same
        size.
        """
        super().__init__(**kwargs)
        self.corners_size = corners_size
        # slice the image in 9 parts
        rects = self.ninepatch_rects(image.get_size())
        self.nine = [pygame.Surface.subsurface(image, rect) for rect in rects]

    def ninepatch_rects(self, area: Tuple[int, int]) -> List[pygame.Rect]:
        """
        Outputs 9 pygame.Rect so that the whole area is sliced in 9. Each rect is a part of the NinePatch.
        rect 0: top-left corner
        rect 1: left side
        rect 2: bottom-left corner
        rect 3: top side
        rect 4: central area
        rect 5: bottom side
        rect 6: top-right corner
        rect 7: right side
        rect 8: bottom-right corner
        :param area: a tuple of 2 ints
        :return: 9 pygame.Rect so that the whole area is sliced in 9.
        """
        w, h = area
        pw, ph = self.corners_size
        # Use cartesian product the 9 required top-left positions and sizes
        positions = itertools.product((0, pw, w - pw), (0, ph, h - ph))
        sizes = itertools.product((pw, w - 2 * pw, pw), (ph, h - 2 * ph, ph))
        return [pygame.Rect(pos, size) for pos, size in zip(positions, sizes)]

    def fill(self, area=None):
        super().fill(area)
        rects = self.ninepatch_rects(self.rect.size)
        for i, (nine, rect) in enumerate(zip(self.nine, rects)):
            # avoid to redraw parts that didn't change
            if area and not area.colliderect(rect):
                continue
            # surface too small for nine patch?
            if rect.w <= 0 or rect.h <= 0:
                continue

            if i in [0, 2, 6, 8]:
                # just blit corners
                self.surface.blit(nine, rect)
            else:
                # If it's not the corners we have to repeat until all surface is covered
                patch_rect: pygame.Rect = nine.get_rect(topleft=rect.topleft)  # how big we sliced the texture
                area_rect:  pygame.Rect = nine.get_rect()  # we may need to blit less than whole sliced texture
                y_repeat = math.ceil(rect.h / patch_rect.h)
                x_repeat = math.ceil(rect.w / patch_rect.w)
                for j in range(x_repeat):
                    for k in range(y_repeat):
                        # check if the sliced texture is bigger than the surface we have to cover
                        if k == x_repeat - 1 and patch_rect.bottom > rect.bottom:
                            area_rect.height -= patch_rect.bottom - rect.bottom
                        if j == y_repeat - 1 and patch_rect.right > rect.right:
                            area_rect.width -= patch_rect.right - rect.right
                        self.surface.blit(nine, patch_rect, area=area_rect)
                        patch_rect.top = patch_rect.bottom
                    patch_rect.top = rect.top
                    patch_rect.left = patch_rect.right


if __name__ == "__main__":
    def test():
        import resources
        import room
        import fonts as f
        import logging
        logging.basicConfig(level=logging.DEBUG)
        nine = NinePatch(resources.load_image('WindowBorder.png'), (70, 70), wait=False, padding=100,
                         layout=room.Layout(gravity=room.Gravity.FILL))
        nine.add_child(gui.Label("test", f.MAIN))
        nine.add_child(gui.Clock(f.MAIN))
        room.run_room(nine)
    test()
