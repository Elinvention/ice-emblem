import pygame
from pygame.locals import *
import utils
import display
import logging
from typing import List, Set

"""
This module should provide a uniform and comfortable way to register callback
functions to one or more types of event.
"""


_contexts = {
    "default": {
        QUIT: [utils.return_to_os],
        VIDEORESIZE: [display.handle_videoresize],
    }
}

__logger = logging.getLogger('EventHandler')

ALWAYS_ALLOWED = [QUIT, VIDEORESIZE]

TIMEOUT = USEREVENT + 1
INTERRUPT = USEREVENT + 2
CLOCK = USEREVENT + 3

EMPTYEVENT = pygame.event.Event(NOEVENT, {})


def get_allowed() -> Set[int]:
    """
    Queries pygame and returns the set of allowed event types.
    """
    blocked = map(pygame.event.get_blocked, range(0, NUMEVENTS))
    allowed = map(lambda x: not x, blocked)
    return set(i for i, v in enumerate(allowed) if v)

def get_blocked() -> Set[int]:
    """
    Queries pygame and returns the set of blocked event types.
    """
    blocked = map(pygame.event.get_blocked, range(0, NUMEVENTS))
    return set(i for i, v in enumerate(blocked) if v)

def allow_all():
    """
    All event types are allowed again except SYSWMEVENT (don't know what it is,
    is blocked by default and at the moment is not needed anyhow)
    """
    # workaround to re-enable all events except SYSWMEVENT
    pygame.event.set_allowed(list(range(NOEVENT, NUMEVENTS)))
    pygame.event.set_blocked(SYSWMEVENT)

def block_all():
    """
    All event types are blocked.
    """
    pygame.event.set_allowed(None)
    pygame.event.set_allowed(ALWAYS_ALLOWED)

def post(events):
    """
    Post all events in a list.
    """
    for e in events:
        pygame.event.post(e)

def post_interrupt(*args):
    pygame.event.post(pygame.event.Event(INTERRUPT, {}))

def names(event_types: List[int]) -> List[str]:
    """
    Returns a list of event type names from a list of event types
    """
    return [pygame.event.event_name(e) for e in event_types]

def set_allowed(event_types: List[int]):
    """
    event_types must be a list of event types that will be allowed.
    All other event types will be blocked.
    Allowed events that would be discarded by pygame are kept and reposted.
    """

    event_types.extend(ALWAYS_ALLOWED)

    if set(event_types) == get_allowed():
        return

    discarded_events = pygame.event.get()

    block_all()
    pygame.event.set_allowed(event_types)

    post([e for e in discarded_events if e.type in event_types])

def set_blocked(event_types: List[int]):
    """
    This is the opposite of set_allowed.
    Allowed events that would be discarded by pygame are kept and reposted.
    """
    event_types -= ALWAYS_ALLOWED

    if get_allowed().isdisjoint(set(event_types)):
        return

    discarded_events = pygame.event.get()

    allow_all()
    if event_types:
        pygame.event.set_blocked(event_types)

    post([e for e in discarded_events if e.type not in event_types])

def add_allowed(event_types: List[int]):
    """
    Adds allowed event types without touching the others.
    Allowed events that would be discarded by pygame are kept and reposted.
    """
    discarded = pygame.event.get()
    pygame.event.set_allowed(event_types)
    post([e for e in discarded if e.type in event_types])

def add_blocked(event_types: List[int]):
    """
    This is the opposite of add_allowed.
    Allowed events that would be discarded by pygame are kept and reposted.
    """
    discarded = pygame.event.get()
    pygame.event.set_blocked(event_types)
    post([e for e in discarded if e.type in event_types])

def pump(context="default"):
    """
    Process all new events without waiting.
    """
    for event in pygame.event.get():
        process_event(event, context)

def wait(timeout=-1, context="default"):
    """
    If the timeout argument is positive, returns after the specified
    number of milliseconds
    """

    if timeout > 0:
        pygame.time.set_timer(TIMEOUT, timeout)
        add_allowed([TIMEOUT])

    if pygame.event.peek(list(get_allowed())):  # if we don't have to wait process all events
        for event in pygame.event.get():  # with get we can process many events per frame
            process_event(event, context)
    else:
        event = pygame.event.wait()  # wait and process a single event
        process_event(event, context)

    if timeout > 0:
        pygame.time.set_timer(TIMEOUT, 0)

    return event

def event_loop(callback, wait=True, context="default"):
    """
    Call a function passing all events as an argument until it returns True.
    If wait is True it calls pygame.event.wait if there are no events in
    pygame's queue, otherwise it just calls pygame.event.get.
    """
    done = callback([EMPTYEVENT])
    while not done:
        if wait and not pygame.event.peek(list(get_allowed())):
            events = [pygame.event.wait()]
        else:
            events = pygame.event.get()
        for event in events:
            process_event(event, context)
        done = callback(events)

def process_event(event, context="default"):
    """
    Process a single event by calling the associated callback functions.
    """
    callbacks = _contexts[context]
    if event.type in callbacks:
        for callback in callbacks[event.type]:
            callback(event)

def register(event_type, callback, context="default"):
    """
    Bind a callback function to an event type.
    """
    callbacks = _contexts[context]
    if event_type in callbacks:
        if callback not in callbacks[event_type]:
            callbacks[event_type].append(callback)
    else:
        callbacks[event_type] = [callback]
    __logger.debug('%s: %s registered %s' % (context, pygame.event.event_name(event_type), callback))

def unregister(event_type, callback=None, context="default"):
    """
    Unregister the latest or the specified callback function from event_type.
    """
    callbacks = _contexts[context]
    if callback:
        if callback in callbacks[event_type]:
            callbacks[event_type].remove(callback)
    elif len(callbacks[key]) > 0:
        callbacks[key].pop()
    __logger.debug('%s: %s unregistered %s',  context, pygame.event.event_name(event_type), callback)

def bind_keys(keys, callback, context="default"):
    """
    Binds a keyboard key to a callback function.
    """
    def f(event):
        for key in keys:
            if event.key == key:
                callback()
    register(KEYDOWN, f, context)

def bind_click(mouse_buttons, callback, area=None, inside=True, context="default"):
    """
    Binds a mouse button to a callback functions.
    The call to the callback can be filtered by area (pygame.Rect) and specify if
    the event position must be inside or outside that area.
    """
    def f(event):
        for mouse_button in mouse_buttons:
            if event.button == mouse_button:
                if area is None:
                    callback()
                else:
                    collide = area.collidepoint(event.pos)
                    if inside:
                        if collide:
                            callback()
                    else:
                        if not collide:
                            callback()
    register(MOUSEBUTTONDOWN, f, context)

def new_context(context="default"):
    """
    Adds a new default context.
    """
    __logger.debug('%s reset' % context)
    _contexts[context] = {
        QUIT: [utils.return_to_os],
        VIDEORESIZE: [display.handle_videoresize],
    }

