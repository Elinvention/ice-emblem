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
        if self.orientation == Orientation.VERTICAL:
            self.default_child_gravity = kwargs.get('default_child_gravity', Gravity.TOP | Gravity.CENTER_HORIZONTAL)
        else:
            self.default_child_gravity = kwargs.get('default_child_gravity', Gravity.LEFT | Gravity.CENTER_VERTICAL)

        super().__init__(**kwargs)

    def measure(self, spec_width, spec_height):
        if self.orientation == Orientation.VERTICAL:
            w, h = self.measure_vertical(spec_width, spec_height)
        else:
            w, h = self.measure_horizontal(spec_width, spec_height)
        self.resolve_measure(spec_width, spec_height, w, h)

    def measure_vertical(self, spec_width, spec_height):
        w, h = spec_width.value, spec_height.value

        spacing = self.spacing * (len(self.children) - 1)
        width_children = self.padding.we
        height_children = self.padding.ns + spacing
        fill_parent_children = []

        for child in self.children:
            if child.layout.height == LayoutParams.WRAP_CONTENT:
                child.measure(MeasureParams(MeasureSpec.AT_MOST, w), MeasureParams(MeasureSpec.AT_MOST, h))
                h -= child.measured_height
            elif child.layout.height == LayoutParams.FILL_PARENT:
                fill_parent_children.append(child)
            else:
                child_height = min(h, child.layout.height)
                child.measure(MeasureParams(MeasureSpec.AT_MOST, w), MeasureParams(MeasureSpec.EXACTLY, child_height))
                h -= child_height
        if fill_parent_children:
            h //= len(fill_parent_children)
            for child in fill_parent_children:
                child.measure(MeasureParams(MeasureSpec.AT_MOST, w), MeasureParams(MeasureSpec.EXACTLY, h))
        for child in self.children:
            width_children = max(width_children, child.measured_width + self.padding.we)
            height_children += child.measured_height

        return min(spec_width.value, width_children), min(spec_height.value, height_children)

    def measure_horizontal(self, spec_width, spec_height):
        w, h = spec_width.value, spec_height.value

        spacing = self.spacing * (len(self.children) - 1)
        width_children = self.padding.we + spacing
        height_children = self.padding.ns
        fill_parent_children = []

        for child in self.children:
            if child.layout.width == LayoutParams.WRAP_CONTENT:
                child.measure(MeasureParams(MeasureSpec.AT_MOST, w), MeasureParams(MeasureSpec.AT_MOST, h))
                w -= child.measured_width
            elif child.layout.width == LayoutParams.FILL_PARENT:
                fill_parent_children.append(child)
            else:
                child_w = min(w, child.layout.width)
                child.measure(MeasureParams(MeasureSpec.EXACTLY, child_w), MeasureParams(MeasureSpec.AT_MOST, h))
                w -= child_w
        if fill_parent_children:
            w //= len(fill_parent_children)
            for child in fill_parent_children:
                child.measure(MeasureParams(MeasureSpec.EXACTLY, w), MeasureParams(MeasureSpec.AT_MOST, h))
        for child in self.children:
            width_children += child.measured_width
            height_children = max(height_children, child.measured_height + self.padding.ns)

        return min(spec_width.value, width_children), min(spec_height.value, height_children)

    def layout_children(self, rect):
        size = rect.size
        NOT_FILL = ~Gravity.FILL

        if self.orientation == Orientation.VERTICAL:
            top = self.padding.n
            bottom = size[1] - self.padding.s
            center = size[1] // 2
        else:
            top = self.padding.w
            bottom = size[0] - self.padding.e
            center = size[0] // 2

        for child in self.children:
            gravity = child.layout.gravity
            if not gravity & Gravity.VERTICAL:
                gravity |= self.default_child_gravity & Gravity.VERTICAL
            if not gravity & Gravity.HORIZONTAL:
                gravity |= self.default_child_gravity & Gravity.HORIZONTAL

            if self.orientation == Orientation.VERTICAL:
                if Gravity.BOTTOM in gravity:
                    bottom -= child.measured_height + self.spacing
                elif Gravity.CENTER_VERTICAL in gravity:
                    center -= (child.measured_height + self.spacing) // 2
            else:
                if Gravity.RIGHT in gravity:
                    bottom -= child.measured_width + self.spacing
                elif Gravity.CENTER_HORIZONTAL in gravity:
                    center -= (child.measured_width + self.spacing) // 2

        for child in self.children:
            gravity = child.layout.gravity
            gravity &= NOT_FILL
            if not gravity & Gravity.VERTICAL:
                gravity |= self.default_child_gravity & Gravity.VERTICAL
            if not gravity & Gravity.HORIZONTAL:
                gravity |= self.default_child_gravity & Gravity.HORIZONTAL

            if self.orientation == Orientation.VERTICAL:
                child_rect = pygame.Rect((self.padding.w, top), child.measured_size)

                if Gravity.TOP in gravity:
                    top += child_rect.h + self.spacing
                elif Gravity.CENTER_VERTICAL in gravity:
                    child_rect.top = center
                    center += child_rect.h + self.spacing
                elif Gravity.BOTTOM in gravity:
                    bottom += child_rect.h + self.spacing
                    child_rect.bottom = bottom

                if Gravity.CENTER_HORIZONTAL in gravity:
                    child_rect.centerx = size[0] // 2
                elif Gravity.RIGHT in gravity:
                    child_rect.right = size[0] - self.padding.e
            else:
                child_rect = pygame.Rect((top, self.padding.n), child.measured_size)

                if Gravity.LEFT in gravity:
                    top += child_rect.w + self.spacing
                elif Gravity.CENTER_HORIZONTAL in gravity:
                    child_rect.left = center
                    center += child_rect.w + self.spacing
                elif Gravity.RIGHT in gravity:
                    bottom += child_rect.w + self.spacing
                    child_rect.right = bottom

                if Gravity.CENTER_VERTICAL in gravity:
                    child_rect.centery = size[1] // 2
                elif Gravity.BOTTOM in gravity:
                    child_rect.bottom = size[1] - self.padding.s

            if (child.rect.w > child_rect.w or child.rect.h > child_rect.h
                    or child.rect.topleft != child_rect.topleft):
                self.fill(child.rect)
            child.layout_children(child_rect)

        self.resolve_layout(rect)
