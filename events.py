import pygame
from pygame.locals import *
import utils
import logging


"""
This module should provide a uniform and comfortable way to register callback
functions to one or more types of event.
"""


__contexts = {
	"default": {
		QUIT: [utils.return_to_os],
		VIDEORESIZE: [utils.videoresize_handler],
	}
}

__logger = logging.getLogger('EventHandler')

ALWAYS_ALLOWED = [QUIT, VIDEORESIZE]

TIMEOUT = USEREVENT + 1
INTERRUPT = USEREVENT + 2
CLOCK = USEREVENT + 3

EMPTYEVENT = pygame.event.Event(NOEVENT, {})

allowed = set()

def allow_all():
	"""
	All event types are allowed again except SYSWMEVENT (don't know what it is,
	is blocked by default and at the moment is not needed anyhow)
	"""
	# workaround to re-enable all events except SYSWMEVENT
	pygame.event.set_allowed(list(range(NOEVENT, NUMEVENTS)))
	pygame.event.set_blocked(SYSWMEVENT)
	allowed = set(range(NOEVENT, NUMEVENTS))
	allowed.remove(SYSWMEVENT)

def block_all():
	"""
	All event types are blocked.
	"""
	pygame.event.set_allowed(None)
	pygame.event.set_allowed(ALWAYS_ALLOWED)
	allowed = set(ALWAYS_ALLOWED)

def post(events):
	"""
	Post all events in a list.
	"""
	for e in events:
		pygame.event.post(e)

def post_interrupt(*args):
	# To be removed when it will be possible to bind arguments to callback functions
	pygame.event.post(pygame.event.Event(INTERRUPT, {}))

def get_allowed():
	"""
	Queries pygame and returns the list of allowed event types.
	"""
	global allowed
	blocked = list(map(pygame.event.get_blocked, range(0, NUMEVENTS)))
	allowed = list(map(lambda x: not x, blocked))
	allowed = set(i for i, v in enumerate(allowed) if v)
	return allowed

def get_blocked():
	"""
	Queries pygame and returns the list of blocked event types.
	"""
	global allowed
	blocked = list(map(pygame.event.get_blocked, range(0, NUMEVENTS)))
	allowed = set(i for i, v in enumerate(allowed) if v)
	return blocked

def names(event_types):
	"""
	Returns a list of event type names from a list of event types
	"""
	return [pygame.event.event_name(e) for e in event_types]

def set_allowed(event_types):
	"""
	evnt_types must be a list of event types that will be allowed.
	All other event types will be blocked.
	Allowed events that would be discarded by pygame are kept and reposted.
	"""
	global allowed

	event_types.extend(ALWAYS_ALLOWED)

	if set(event_types) == allowed:
		return

	discarded_events = pygame.event.get()

	block_all()
	if event_types:
		pygame.event.set_allowed(event_types)

	post([e for e in discarded_events if e.type in event_types])

def set_blocked(event_types):
	"""
	This is the opposite of set_allowed.
	Allowed events that would be discarded by pygame are kept and reposted.
	"""
	global allowed
	event_types -= ALWAYS_ALLOWED

	if allowed.isdisjoint(set(event_types)):
		return

	discarded_events = pygame.event.get()

	allow_all()
	if event_types:
		pygame.event.set_blocked(event_types)

	post([e for e in discarded_events if e.type not in event_types])

def add_allowed(event_types):
	"""
	Adds allowed event types without touching the others.
	Allowed events that would be discarded by pygame are kept and reposted.
	"""
	global allowed
	event_types = filter(pygame.event.get_blocked, event_types)
	if event_types:
		discarded = pygame.event.get()
		pygame.event.set_allowed(list(event_types))
		allowed.update(set(event_types))
		post([e for e in discarded if e.type in event_types])

def add_blocked(event_types):
	"""
	This is the opposite of add_allowed.
	Allowed events that would be discarded by pygame are kept and reposted.
	"""
	global allowed
	event_types = filter(lambda e: not pygame.event.get_blocked(e), event_types)
	if event_types:
		discarded = pygame.event.get()
		pygame.event.set_blocked(list(event_types))
		allowed.difference_update(set(event_types))
		post([e for e in discarded if e.type in event_types])

def pump(context="default"):
	"""
	Process all new events without waiting.
	"""
	for event in pygame.event.get():
		process_event(event, context)

def wait(timeout=-1, event_types=[MOUSEBUTTONDOWN, KEYDOWN], context="default"):
	"""
	If the timeout argument is positive, returns after the specified
	number of milliseconds. event_types must be a list of event types
	that are allowed to interrupt the wait.
	"""
	event_types.extend(ALWAYS_ALLOWED)
	set_allowed(event_types)

	if timeout > 0:
		pygame.time.set_timer(TIMEOUT, timeout)
		add_allowed([TIMEOUT])

	if pygame.event.peek(event_types):  # if we don't have to wait process all events
		for event in pygame.event.get():  # with get we can process many events per frame
			process_event(event, context)
	else:
		event = pygame.event.wait()  # wait and process a single event
		process_event(event, context)

	if timeout > 0:
		pygame.time.set_timer(TIMEOUT, 0)

	return event

def event_loop(callback, event_types, context="default"):
	"""
	Call a function passing all events as an argument until it returns True.
	event_types must be a list of allowed event types.
	"""
	set_allowed(event_types)
	done = callback([EMPTYEVENT])
	while not done:
		events = pygame.event.get()
		for event in events:
			process_event(event, context)
		done = callback(events)

def process_event(event, context="default"):
	"""
	Process a single event by calling the associated callback functions.
	"""
	callbacks = __contexts[context]
	if event.type in callbacks:
		for callback in callbacks[event.type]:
			callback(event)

def register(event_type, callback, context="default"):
	"""
	Bind a callback function to an event type.
	"""
	callbacks = __contexts[context]
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
	callbacks = __contexts[context]
	for key in callbacks:
		if key == event_type:
			if callback:
				if callback in callbacks[key]:
					callbacks[key].remove(callback)
			elif len(callbacks[key]) > 0:
				callbacks[key].pop()
			__logger.debug('%s: %s unregistered %s' % (context, pygame.event.event_name(event_type), callback))
			break

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
	__contexts[context] = {
		QUIT: [utils.return_to_os],
		VIDEORESIZE: [utils.videoresize_handler],
	}
