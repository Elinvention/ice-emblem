"""
Wrapper of pygame.event with useful functions
"""

import pygame
import pygame.locals as p
import logging
from typing import List, Iterator


ALWAYS_ALLOWED = [p.QUIT, p.VIDEORESIZE]

EMPTY_EVENT = pygame.event.Event(p.NOEVENT, {})

available_events = set(range(p.USEREVENT, p.NUMEVENTS))

__logger = logging.getLogger('EventHandler')


def new_timer(time: int):
    event_type = available_events.pop()
    pygame.time.set_timer(event_type, time)
    __logger.debug("New %d ms timer (%d)", time, event_type)
    return event_type


def stop_timer(event_type: int) -> None:
    pygame.time.set_timer(event_type, 0)
    available_events.add(event_type)
    __logger.debug("Timer %d stopped", event_type)


def get_allowed() -> Iterator[int]:
    """
    Queries pygame and returns the generator of allowed event types.
    """
    blocked = map(pygame.event.get_blocked, range(0, p.NUMEVENTS))
    allowed = map(lambda x: not x, blocked)
    return (i for i, v in enumerate(allowed) if v)


def get_blocked() -> Iterator[int]:
    """
    Queries pygame and returns the set of blocked event types.
    """
    blocked = map(pygame.event.get_blocked, range(0, p.NUMEVENTS))
    return (i for i, v in enumerate(blocked) if v)


def allow_all() -> None:
    """
    All event types are allowed again except SYSWMEVENT (don't know what it is,
    is blocked by default and at the moment is not needed anyhow)
    """
    # workaround to re-enable all events except SYSWMEVENT
    pygame.event.set_allowed(list(range(p.NOEVENT, p.NUMEVENTS)))
    pygame.event.set_blocked(p.SYSWMEVENT)


def block_all() -> None:
    """
    All event types are blocked.
    """
    pygame.event.set_allowed(None)
    pygame.event.set_allowed(ALWAYS_ALLOWED)


def post(events) -> None:
    """
    Post all events in a list.
    """
    for e in events:
        pygame.event.post(e)


def names(event_types: List[int]) -> List[str]:
    """
    Returns a list of event type names from a list of event types
    """
    return [pygame.event.event_name(e) for e in event_types]


def set_allowed(event_types: List[int]) -> None:
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


def set_blocked(event_types: List[int]) -> None:
    """
    This is the opposite of set_allowed.
    Allowed events that would be discarded by pygame are kept and reposted.
    """
    event_types -= ALWAYS_ALLOWED

    if set(get_allowed()).isdisjoint(set(event_types)):
        return

    discarded_events = pygame.event.get()

    allow_all()
    if event_types:
        pygame.event.set_blocked(event_types)

    post([e for e in discarded_events if e.type not in event_types])


def add_allowed(event_types: List[int]) -> None:
    """
    Adds allowed event types without touching the others.
    Allowed events that would be discarded by pygame are kept and reposted.
    """
    discarded = pygame.event.get()
    pygame.event.set_allowed(event_types)
    post([e for e in discarded if e.type in event_types])


def add_blocked(event_types: List[int]) -> None:
    """
    This is the opposite of add_allowed.
    Allowed events that would be discarded by pygame are kept and reposted.
    """
    discarded = pygame.event.get()
    pygame.event.set_blocked(event_types)
    post([e for e in discarded if e.type in event_types])


def event_loop(callback, wait=True) -> None:
    """
    Call a function passing all events as an argument until it returns True.
    If wait is True it calls pygame.event.wait if there are no events in
    pygame's queue, otherwise it just calls pygame.event.get.
    """
    done = callback([EMPTY_EVENT])
    while not done:
        if wait and not pygame.event.peek(list(get_allowed())):
            events = [pygame.event.wait()]
        else:
            events = pygame.event.get()
        done = callback(events)
