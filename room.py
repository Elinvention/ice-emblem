import collections
import events
import display
import logging


class Room(object):
	def __init__(self, **kwargs):
		self.fps = kwargs.get('fps', display.fps)
		self.wait = kwargs.get('wait', True)
		self.context = kwargs.get('context', self.__class__.__name__)
		self.logger = logging.getLogger(self.context)
		self.allowed_events = kwargs.get('allowed_events', [])
		self.children = []

	def add_child(self, child):
		child.context = self.context
		for ch in child.children:
			ch.context = self.context
		self.children.append(child)

	def remove_child(self, child):
		self.children.remove(child)

	def add_children(self, children):
		for child in children:
			self.add_child(child)

	def begin_children(self):
		for child in self.children:
			child.begin()

	def begin(self):
		self.begin_children()
		self.logger.debug("begin")

	def loop(self, _events):
		for child in self.children:
			child.loop(_events)
		return False

	def draw_children(self):
		for child in self.children:
			child.draw()

	def draw(self):
		self.draw_children()

	def end_children(self):
		for child in self.children:
			child.end()

	def end(self):
		self.logger.debug("end")
		self.end_children()

	def register(self, event_type, callback):
		events.register(event_type, callback, self.context)

	def unregister(self, event_type, callback):
		events.unregister(event_type, callback, self.context)

	def bind_keys(self, keys, callback):
		events.bind_keys(keys, callback, self.context)

	def bind_click(self, mouse_buttons, callback, area=None, inside=True):
		events.bind_click(mouse_buttons,  callback, area, inside, self.context)


rooms = collections.deque()
quit = False

def queue_room(room):
	rooms.append(room)

def run_next_room(dequeue=True):
	global quit
	if dequeue:
		run_room(rooms.popleft())
	else:
		run_room(rooms[0])
	quit = False

def run_room(room):
	global quit
	quit = False
	events.new_context(room.context)
	if room.allowed_events:
		events.set_allowed(room.allowed_events)
	room.begin()
	room.draw()
	display.flip()
	def loop(_events):
		done = room.loop(_events) or quit
		if not done:
			room.draw()
			display.draw_fps()
			display.flip()
			display.tick(room.fps)
		return done
	events.event_loop(loop, room.wait, room.context)
	if not quit:
		room.end()

def run():
	global quit
	quit = False
	while rooms:
		run_next_room()

def stop():
	global rooms, quit
	rooms = collections.deque()
	quit = True
