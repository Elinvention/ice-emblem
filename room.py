"""
This module is central in Ice Emblem's engine since it provides the Room class
and some functions that uniformly act upon Room objects.
"""


import pygame
import pygame.locals as p
import logging

import events
import display
import utils

from basictypes import Rect, Point


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
        self.rect = Rect(**kwargs)
        self.surface = kwargs.get('surface', pygame.Surface(self.rect.size))
        self.callbacks = {}
        self.next = None

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

    def add_child(self, child):
        self.add_children(child)

    def remove_child(self, child):
        self.children.remove(child)
        child.parent = None

    def invalidate(self):
        node = self
        while node and node.valid:
            node.valid = False
            node = node.parent

    def resize(self, size):
        self.rect.settings['size'] = size
        self.rect.apply()
        self.logger.debug("Requested resize to %s, actual %s" % (size, self.rect.size))
        self.surface = pygame.Surface(self.rect.size)
        self.invalidate()

    def handle_videoresize(self, event):
        if self.root:
            self.resize(event.size)

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

    def draw_children(self):
        for child in self.children:
            if child.visible:
                if not child.valid:
                    child.draw()
                self.surface.blit(child.surface, child.rect)

    def draw(self):
        self.draw_children()
        self.valid = True

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
        coord = Point(coord)
        node = self
        while node:
            coord += Point(node.rect.topleft)
            node = node.parent
        return coord

    def global_pos(self):
        return self.global_coord((0, 0))

    def global_rect(self):
        return Rect(rect=[self.global_pos(), self.rect.size])


class RoomStop(Exception):
    pass


def draw_room(room):
    if room.clear_screen:
        display.window.fill(room.clear_screen)
    if not room.valid:
        room.draw()
    display.window.blit(room.surface, room.rect)
    display.draw_fps()
    display.flip()
    return display.tick(room.fps)

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
    room.begin()
    draw_room(room)
    dt = display.tick(room.fps)
    def loop(_events):
        nonlocal dt
        generic_event_handler(_events)
        room.process_events(_events)
        room.loop(_events, dt)
        dt = draw_room(room)
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
        pass

def stop():
    raise RoomStop()
