"""

"""


import pygame

from enum import Enum, auto

import room

from room import Gravity, LayoutParams, MeasureSpec, MeasureParams


class Orientation(Enum):
    VERTICAL = auto()
    HORIZONTAL = auto()


class LinearLayout(room.Room):
    def __init__(self, **kwargs):
        self.spacing = kwargs.get('spacing', 10)
        self.orientation = kwargs.get('orientation', Orientation.VERTICAL)
        self.gravity = kwargs.get('gravity', Gravity.TOP | Gravity.CENTER_HORIZONTAL if self.orientation == Orientation.VERTICAL else Gravity.LEFT | Gravity.CENTER_VERTICAL)

        super().__init__(**kwargs)

    def measure(self, spec_width, spec_height):
        if self.orientation == Orientation.VERTICAL:
            w, h = self.measure_vertical(spec_width, spec_height)
        elif self.orientation == Orientation.HORIZONTAL:
            w, h = self.measure_horizontal(spec_width, spec_height)
        self.resolve_measure(spec_width, spec_height, w, h)

    def measure_vertical(self, spec_width, spec_height):
        w, h = spec_width.value, spec_height.value

        spacing = self.spacing * (len(self.children) - 1)
        width_children = self.padding.we
        height_children = self.padding.ns + spacing
        fill_parent_children = []

        for child in self.children:
            if child.layout_height == LayoutParams.WRAP_CONTENT:
                child.measure(MeasureParams(MeasureSpec.AT_MOST, w), MeasureParams(MeasureSpec.AT_MOST, h))
                h -= child.measured_height
            elif child.layout_height == LayoutParams.FILL_PARENT:
                fill_parent_children.append(child)
            else:
                child_height = min(h, child.layout_height)
                child.measure(MeasureParams(MeasureSpec.AT_MOST, w), MeasureParams(MeasureSpec.EXACTLY, child_height))
                h -= child_height
        if fill_parent_children:
            h //= len(fill_parent_children)
            for child in fill_parent_children:
                child.measure(MeasureParams(MeasureSpec.AT_MOST, w), MeasureParams(MeasureSpec.EXACTLY, h))
        for child in self.children:
            width_children = max(width_children, child.measured_width + self.padding.we)
            height_children += child.measured_height

        return width_children, height_children


    def measure_horizontal(self, spec_width, spec_height):
        w, h = spec_width.value, spec_height.value

        spacing = self.spacing * (len(self.children) - 1)
        width_children = self.padding.we + spacing
        height_children = self.padding.ns
        fill_parent_children = []

        for child in self.children:
            if child.layout_width == LayoutParams.WRAP_CONTENT:
                child.measure(MeasureParams(MeasureSpec.AT_MOST, w), MeasureParams(MeasureSpec.AT_MOST, h))
                w -= child.measured_width
            elif child.layout_width == LayoutParams.FILL_PARENT:
                fill_parent_children.append(child)
            else:
                child_w = min(w, child.layout_width)
                child.measure(MeasureParams(MeasureSpec.EXACTLY, child_w), MeasureParams(MeasureSpec.AT_MOST, h))
                w -= child_w
        if fill_parent_children:
            w //= len(fill_parent_children)
            for child in fill_parent_children:
                child.measure(MeasureParams(MeasureSpec.EXACTLY, w), MeasureParams(MeasureSpec.AT_MOST, h))
        for child in self.children:
            width_children += child.measured_width
            height_children = max(height_children, child.measured_height + self.padding.ns)

        return width_children, height_children

    def layout(self, rect):
        size = rect.size
        if self.orientation == Orientation.VERTICAL:
            top = self.padding.n
            nbottoms, bottom = 0, size[1] - self.padding.s
            ncenterys, centery = 0, size[1] // 2

            for child in self.children:
                gravity = child.layout_gravity
                if not gravity & Gravity.VERTICAL:
                    gravity |= self.gravity & Gravity.VERTICAL
                if not gravity & Gravity.HORIZONTAL:
                    gravity |= self.gravity & Gravity.HORIZONTAL

                if Gravity.BOTTOM in gravity:
                    bottom -= child.measured_height + self.spacing
                    nbottoms += 1
                elif Gravity.CENTER_VERTICAL in gravity:
                    centery -= (child.measured_height + self.spacing) // 2
                    ncenterys += 1

            for child in self.children:
                gravity = child.layout_gravity
                gravity &= ~Gravity.FILL
                if not gravity & Gravity.VERTICAL:
                    gravity |= self.gravity & Gravity.VERTICAL
                if not gravity & Gravity.HORIZONTAL:
                    gravity |= self.gravity & Gravity.HORIZONTAL

                child_rect = pygame.Rect((self.padding.w, top), (child.measured_width, child.measured_height))

                if Gravity.TOP in gravity:
                    child_rect.top = top
                    top += child_rect.h + self.spacing
                elif Gravity.CENTER_VERTICAL in gravity:
                    child_rect.top = centery
                    centery += child_rect.h + self.spacing
                elif Gravity.BOTTOM in gravity:
                    bottom += child_rect.h + self.spacing
                    child_rect.bottom = bottom

                if Gravity.CENTER_HORIZONTAL in gravity:
                    child_rect.centerx = size[0] // 2
                elif Gravity.LEFT in gravity:
                    child_rect.left = self.padding.w
                elif Gravity.RIGHT in gravity:
                    child_rect.right = size[0] - self.padding.e

                child.layout(child_rect)
        else:
            left = self.padding.w
            nrights, right = 0, size[0] - self.padding.e
            ncenterxs, centerx = 0, size[0] // 2

            for child in self.children:
                gravity = child.layout_gravity
                if not gravity & Gravity.VERTICAL:
                    gravity |= self.gravity & Gravity.VERTICAL
                if not gravity & Gravity.HORIZONTAL:
                    gravity |= self.gravity & Gravity.HORIZONTAL

                if Gravity.RIGHT in gravity:
                    right -= child.measured_width + self.spacing
                    nrights += 1
                elif Gravity.CENTER_VERTICAL in gravity:
                    centerx -= (child.measured_width + self.spacing) // 2
                    ncenterxs += 1

            for child in self.children:
                gravity = child.layout_gravity
                gravity &= ~Gravity.FILL
                if not gravity & Gravity.VERTICAL:
                    gravity |= self.gravity & Gravity.VERTICAL
                if not gravity & Gravity.HORIZONTAL:
                    gravity |= self.gravity & Gravity.HORIZONTAL

                child_rect = pygame.Rect((left, self.padding.n), (child.measured_width, child.measured_height))

                if Gravity.LEFT in gravity:
                    child_rect.left = left
                    left += child_rect.w + self.spacing
                elif Gravity.CENTER_HORIZONTAL in gravity:
                    child_rect.left = centerx
                    centerx += child_rect.w + self.spacing
                elif Gravity.RIGHT in gravity:
                    right += child_rect.w + self.spacing
                    child_rect.right = right

                if Gravity.TOP in gravity:
                    child_rect.top = self.padding.n
                elif Gravity.CENTER_VERTICAL in gravity:
                    child_rect.centery = size[1] // 2
                elif Gravity.BOTTOM in gravity:
                    child_rect.right = size[1] - self.padding.s

                child.layout(child_rect)

        super().layout(rect)

