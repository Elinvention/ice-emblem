"""
This module is central in Ice Emblem's engine since it provides the Room class
and some functions that uniformly act upon Room objects.
"""


import pygame
import pygame.locals as p
import logging

from enum import Flag, Enum, auto
import colors as c

import events
import display
import utils

from basictypes import NESW


class Gravity(Flag):
    NO_GRAVITY = 0  # Constant indicating that no gravity has been set
    TOP = auto()  # Push object to the top of its container, not changing its size.
    BOTTOM = auto()  # Push object to the bottom of its container, not changing its size.
    LEFT = auto()  # Push object to the left of its container, not changing its size.
    RIGHT = auto()  # Push object to the right of its container, not changing its size.
    TOPLEFT = TOP | LEFT
    TOPRIGHT = TOP | RIGHT
    BOTTOMLEFT = BOTTOM | LEFT
    BOTTOMRIGHT = BOTTOM | RIGHT
    CENTER_HORIZONTAL = auto()  # Place object in the horizontal center of its container, not changing its size.
    CENTER_VERTICAL   = auto()  # Place object in the vertical center of its container, not changing its size.
    CENTER = CENTER_HORIZONTAL | CENTER_VERTICAL  # Place the object in the center of its container in both the vertical and horizontal axis, not changing its size.
    FILL_HORIZONTAL = auto()  # Grow the horizontal size of the object if needed so it completely fills its container.
    FILL_VERTICAL = auto()  # Grow the vertical size of the object if needed so it completely fills its container.
    FILL = FILL_HORIZONTAL | FILL_VERTICAL  # Grow the horizontal and vertical size of the object if needed so it completely fills its container.
    VERTICAL = TOP | BOTTOM | CENTER_VERTICAL
    HORIZONTAL = LEFT | RIGHT | CENTER_HORIZONTAL


class LayoutParams(Enum):
    FILL_PARENT = auto()
    WRAP_CONTENT = auto()


class MeasureSpec(Enum):
    EXACTLY = auto()
    AT_MOST = auto()
    UNSPECIFIED = auto()


class MeasureParams(object):
    def __init__(self, mode, value):
        self.mode = mode
        self.value = value

    def __str__(self):
        return "%s, %s" % (self.mode, self.value)

    def exactly(self):
        return MeasureParams(MeasureSpec.EXACTLY, self.value)

    def at_most(self):
        return MeasureParams(MeasureSpec.AT_MOST, self.value)




class Room(object):
    """
    Room class is at the heart of Ice Emblem's engine.
    It provides a tree like data structure that can be run in a uniform way by the
    run_room function and allow to route events to registered callbacks or methods
    named like handle_videoresize.
    """
    def __init__(self, **kwargs):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.fps = kwargs.get('fps', display.fps)
        self.wait = kwargs.get('wait', True)
        self.allowed_events = kwargs.get('allowed_events', [])
        self.die_when_done = kwargs.get('die_when_done', True)
        self.clear_screen = kwargs.get('clear_screen', (0, 0, 0))
        self.children = [self.prepare_child(child) for child in kwargs.get('children', [])]
        self.parent = None
        self.done = False
        self.root = False
        self.valid = False
        self.visible = kwargs.get('visible', True)
        self.rect = pygame.Rect((0, 0), (0, 0))
        self.surface = pygame.Surface(self.rect.size)
        self.callbacks = {}
        self.next = None

        self.layout_width = kwargs.get('layout_width', LayoutParams.WRAP_CONTENT)
        self.layout_height = kwargs.get('layout_height', LayoutParams.WRAP_CONTENT)
        self.layout_gravity = kwargs.get('layout_gravity', Gravity.NO_GRAVITY)
        self.layout_position = kwargs.get('layout_position', (0, 0))
        self.layout_valid = False

        self.padding = NESW(kwargs.get('padding', 0))
        self.border = NESW(kwargs.get('border', 0))
        self.margin = NESW(kwargs.get('margin', 0))

        self.bg_color = kwargs.get('bg_color', c.MENU_BG)
        self.bg_image = kwargs.get('bg_image', None)
        self.bg_size = kwargs.get('bg_size', 'contain')  # Possible values: 'contain', 'cover', (int, int)
        self._bg_image_size = None

    @property
    def layout_wh(self):
        return self.layout_width, self.layout_height

    @property
    def measured_size(self):
        return self.measured_width, self.measured_height

    def prepare_child(self, child):
        child.parent = self
        child.begin()
        for grandchild in child.children:
            child.prepare_child(grandchild)
        return child

    def add_children(self, *children):
        for child in children:
            self.prepare_child(child)
        self.children.extend(children)
        self.layout_request()
        self.invalidate()

    def add_child(self, child):
        self.add_children(child)
        self.layout_request()
        self.invalidate()

    def remove_child(self, child):
        self.children.remove(child)
        child.parent = None
        self.layout_request()
        self.invalidate()

    def invalidate(self):
        node = self
        while node and node.valid:
            node.valid = False
            node = node.parent

    def get_root(self):
        node = self
        while node:
            if node.root:
                assert(node.parent is None)
                return node
            node = node.parent

    def layout_request(self):
        node = self
        while node and node.layout_valid:
            node.layout_valid = False
            node = node.parent

    def measure(self, spec_width, spec_height):
        """
        Top-down traversal of the tree. The parent asks its children to measure their size.
        The measured size should not exceed max_width and max_height otherwise the parent may clip the child.
        """
        for child in self.children:
            child.measure(spec_width.at_most(), spec_height.at_most())
        self.resolve_measure(spec_width, spec_height, self.rect.w, self.rect.h)

    def resolve_measure(self, spec_width, spec_height, content_width, content_height):
        if spec_width.mode == MeasureSpec.EXACTLY:
            self.measured_width = spec_width.value
        else:
            if self.layout_width == LayoutParams.FILL_PARENT:
                self.measured_width = spec_width.value
            elif self.layout_width == LayoutParams.WRAP_CONTENT:
                self.measured_width = content_width
            else:
                self.measured_width = min(spec_width.value, self.layout_width)

        if spec_height.mode == MeasureSpec.EXACTLY:
            self.measured_height = spec_height.value
        else:
            if self.layout_height == LayoutParams.FILL_PARENT:
                self.measured_height = spec_height.value
            elif self.layout_height == LayoutParams.WRAP_CONTENT:
                self.measured_height = content_height
            else:
                self.measured_height = min(spec_height.value, self.layout_height)
        self.logger.debug("W: (%s) -> %s; H: (%s) -> %s", spec_width, self.measured_width, spec_height, self.measured_height)

    def layout(self, rect):
        """
        Top-down traversal of the tree. The parent positions its children.
        This method must be called after measure.
        """
        for child in self.children:
            child.layout(pygame.Rect(child.layout_position, child.measured_size))
        self.resolve_layout(rect)

    def resolve_layout(self, rect):
        self.rect.topleft = rect.topleft
        self.resize(rect.size)
        self.layout_valid = True
        self.logger.debug("layout gravity: %s; rect: %s", self.layout_gravity, self.rect)

    def resize(self, size):
        if self.rect.size != size:
            self.rect.size = size
            self.surface = pygame.Surface(self.rect.size)
            self.fill()
            self.invalidate()

    def handle_videoresize(self, event):
        self.layout_request()

    def begin_children(self):
        for child in self.children:
            child.begin()

    def begin(self):
        self.begin_children()
        self.logger.debug("begin")

    def loop(self, _events, dt):
        for child in self.children:
            child.loop(_events, dt)
            if child.done and child.die_when_done:
                child.end()

    def draw(self):
        self.draw_children()
        self.valid = True

    def draw_children(self):
        for child in self.children:
            if child.visible:
                if not child.valid:
                    child.draw()
                self.surface.blit(child.surface, child.rect)

    def fill(self, area=None):
        if self.bg_color:
            if area:
                surf = pygame.Surface(area.size)
                surf.fill(self.bg_color)
                self.surface.blit(surf, area)
            else:
                self.surface.fill(self.bg_color)
        if self.bg_image:
            resized = self.bg_image_resized()
            pos = resized.get_rect(center=self.rect.center).move(-self.rect.x, -self.rect.y)
            self.surface.blit(resized, pos, area)

    def fill_recursive(self):
        self.fill()
        for child in self.children:
            child.fill_recursive()

    def bg_image_resized(self):
        if self.bg_size == 'contain':
            new_size = utils.resize_keep_ratio(self.bg_image.get_size(), self.rect.size)
        elif self.bg_size == 'cover':
            new_size =  utils.resize_cover(self.bg_image.get_size(), self.rect.size)
        else:
            new_size = (int(self.bg_size[0] / 100 * self.rect.w), int(self.bg_size[1] / 100 * self.rect.h))
        if new_size == self._bg_image_size:
            return self._bg_image_resized
        self._bg_image_resized = pygame.transform.smoothscale(self.bg_image, new_size).convert()
        self._bg_image_size = self.rect.size
        return self._bg_image_resized

    def end_children(self):
        for child in self.children:
            child.end()

    def end(self):
        self.logger.debug("end")
        self.end_children()
        if self.parent and self.die_when_done:
            self.parent.remove_child(self)

    def process_events(self, _events):
        """
        Dispatches an event to registered callbacks or to methods named
        like handle_mousebuttondown.
        """
        processed = False
        for child in self.children:
            processed = processed or child.process_events(_events)
        if processed:
            return
        for event in _events:
            if event.type in self.callbacks:
                for callback in self.callbacks[event.type]:
                    processed = processed or callback(event)
            method = getattr(self, 'handle_' + pygame.event.event_name(event.type).lower(), None)
            if method is not None:
                processed = processed or method(event)
        return processed

    def register(self, event_type, callback):
        """
        Bind a callback function to an event type.
        """
        if event_type in self.callbacks:
            if callback not in self.callbacks[event_type]:
                self.callbacks[event_type].append(callback)
        else:
            self.callbacks[event_type] = [callback]
        self.logger.debug('registered %s -> %s', pygame.event.event_name(event_type), callback)

    def unregister(self, event_type, callback=None):
        """
        Unregister the latest or the specified callback function from event_type.
        """
        if callback:
            if callback in self.callbacks[event_type]:
                self.callbacks[event_type].remove(callback)
        elif len(self.callbacks[event_type]) > 0:
            self.callbacks[event_type].pop()
        self.logger.debug('unregistered %s -> %s',  pygame.event.event_name(event_type), callback)

    def bind_keys(self, keys, callback):
        """
        Binds a keyboard key to a callback function.
        """
        def f(event):
            for key in keys:
                if event.key == key:
                    callback(self)
        self.register(p.KEYDOWN, f)

    def bind_click(self, mouse_buttons, callback, area=None, inside=True):
        """
        Binds a mouse button to a callback functions.
        The call to the callback can be filtered by area (pygame.Rect) and specify if
        the event position must be inside or outside that area.
        """
        def f(event):
            for mouse_button in mouse_buttons:
                if event.button == mouse_button:
                    if area is None:
                        callback(self)
                    else:
                        collide = area.collidepoint(event.pos)
                        if inside and collide:
                            callback(self)
                        elif not inside and not collide:
                            callback(self)
        self.register(p.MOUSEBUTTONDOWN, f)

    def wait_event(self, timeout=-1):
        _events = events.wait(timeout)
        generic_event_handler(_events)
        self.process_events(_events)

    def global_coord(self, coord):
        node = self
        while node:
            coord = coord[0] + node.rect.x, coord[1] + node.rect.y
            node = node.parent
        return coord

    def global_pos(self):
        return self.global_coord((0, 0))

    def global_rect(self):
        return pygame.Rect(self.global_pos(), self.rect.size)

    def local_coord(self, coord):
        node = self
        while node:
            coord = coord[0] - node.rect.x, coord[1] - node.rect.y
            node = node.parent
        return coord

    def local_rect(self):
        return pygame.Rect(self.local_coord((0, 0)), self.rect.size)


class RoomStop(Exception):
    pass


def draw_room(room, first_draw=False):
    if room.clear_screen:
        display.window.fill(room.clear_screen)
    if not room.layout_valid:
        room.measure(MeasureParams(MeasureSpec.EXACTLY, display.get_width()), MeasureParams(MeasureSpec.EXACTLY, display.get_height()))
        room.layout(display.get_rect())
    if first_draw:
        room.fill_recursive()
    if not room.valid:
        room.draw()
    display.window.blit(room.surface, room.rect)
    display.draw_fps()
    display.flip()

def generic_event_handler(_events):
    for event in _events:
        if event.type == pygame.QUIT:
            utils.return_to_os()
        if event.type == pygame.VIDEORESIZE:
            display.handle_videoresize(event)

def run_room(room):
    allowed_events = list(events.get_allowed())
    if room.allowed_events:
        events.set_allowed(room.allowed_events)
    room.root = True
    room.done = False
    room.valid = False
    room.layout_valid = False
    room.begin()
    draw_room(room, first_draw=True)
    dt = display.tick(room.fps)
    def loop(_events):
        nonlocal dt
        generic_event_handler(_events)
        room.process_events(_events)
        room.loop(_events, dt)
        draw_room(room)
        dt = display.tick(room.fps)
        return room.done
    events.event_loop(loop, room.wait)
    room.end()
    if room.allowed_events:
        events.set_allowed(allowed_events)
    room.root = False

def run(first_room):
    room = first_room
    try:
        while room:
            run_room(room)
            room = room.next
    except RoomStop:
        room.root = False

def stop():
    raise RoomStop()
