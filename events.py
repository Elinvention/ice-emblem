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


def pump(context="default"):
	"""
	Process new events
	"""
	processed = {}
	for event in pygame.event.get():
		processed[event.type] = process_event(event, context)
	return processed


def wait(event_types=[MOUSEBUTTONDOWN, KEYDOWN], timeout=-1, context="default"):
	"""
	if the timeout argument is positive, returns after the specified
	number of milliseconds.
	"""
	event_types.append(QUIT)
	event_types.append(VIDEORESIZE)

	if timeout > 0:
		pygame.time.set_timer(USEREVENT+1, timeout)
		event_types.append(USEREVENT+1)

	if pygame.event.peek(event_types):  # if events we are looking for are already available
		for event in pygame.event.get(event_types):  # get them
			process_event(event, context)
		pygame.event.clear()  # clear queue from events we don't want
	else:
		event = pygame.event.wait()  # wait for an interesting event
		while event.type not in event_types:
			event = pygame.event.wait()
		process_event(event, context)

	if timeout > 0:
		pygame.time.set_timer(USEREVENT+1, 0)

	return event

def process_event(event, context="default"):
	ret = []
	callbacks = __contexts[context]
	if event.type in callbacks:
		for callback in callbacks[event.type]:
			ret.append(callback(event))
	return ret

def register(event_type, callback, context="default"):
	"""
	Bind a callback function to a specified event type.
	"""
	callbacks = __contexts[context]
	if event_type in callbacks:
		if callback not in callbacks[event_type]:
			callbacks[event_type].append(callback)
	else:
		callbacks[event_type] = [callback]
	__logger.debug('%s: %s registered %s' % (context, pygame.event.event_name(event_type), callback))

def unregister(event_type, callback=None, context="default"):
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
	def f(event):
		for key in keys:
			if event.key == key:
				callback()
	register(KEYDOWN, f, context)

def bind_click(mouse_buttons, callback, area=None, inside=True, context="default"):
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
	__logger.debug('%s reset' % context)
	__contexts[context] = {
		QUIT: [utils.return_to_os],
		VIDEORESIZE: [utils.videoresize_handler],
	}

