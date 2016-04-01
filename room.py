import collections
import events
import display


class Room(object):
	wait = True
	context = "default"

	def __init__(self):
		pass

	def begin(self):
		pass

	def loop(self, _events):
		return True

	def draw(self):
		display.draw_fps()

	def end(self):
		pass


rooms = collections.deque()

def queue_room(room):
	rooms.append(room)

def run_next_room(dequeue=True):
	if dequeue:
		run_room(rooms.popleft())
	else:
		run_room(rooms[0])

def run_room(room):
	room.begin()
	def loop(_events):
		room.draw()
		return room.loop(_events)
	events.event_loop(loop, room.wait, room.context)
	room.end()

def run():
	while rooms:
		run_next_room()

