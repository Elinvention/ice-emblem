"""ie_map class."""


import math


class ie_map_node(object):
	"""Node"""
	def __init__(self, unit=None, walkable=True):
		self.walkable = walkable
		self.unit = unit


class ie_map(object):
	"""The map is composed of nodes."""
	def __init__(self, (x, y)):
		self.dim = (x, y)
		self.matrix = [[ie_map_node() for i in range(y)] for j in range(x)]
		self.selection = None
		self.selection_range = []

	def setUnit(self, unit, (x, y)):
		"""Set an unit to the coordinates."""
		self.matrix[x][y].unit = unit

	def mouse2cell(self, scr_rect, pos):
		"""mouse position to matrix indexes."""
		x = pos[0] / (scr_rect.w / self.dim[0])
		y = pos[1] / (scr_rect.h / self.dim[1])
		print("Cell (%d, %d)" % (x, y))
		return (x, y)

	def where_is(self, unit):
		for i in range(self.dim[0]):
			for j in range(self.dim[1]):
				if self.matrix[i][j].unit == unit:
					return (i, j)
		return None

	def move(self, unit, (x, y)):
		(old_x, old_y) = self.where_is(unit)
		self.matrix[old_x][old_y].unit = None
		self.matrix[x][y].unit = unit

	def list_range(self, (x, y), Move):
		for px in range(x - Move, x + Move + 1):
			for py in range(y - Move, y + Move + 1):
				try:
					if self.matrix[px][py].unit is None:
						x_distance = abs(px - x)
						y_distance = abs(py - y)
						y_limit = Move - x_distance
						x_limit = Move - y_distance
						if self.matrix[px][py].walkable and x_distance <= x_limit and y_distance <= y_limit:
							self.selection_range.append((px, py))
				except IndexError:
					pass

	def select(self, scr_rect, (pointer_x, pointer_y)):
		"""set selected."""

		x, y = self.mouse2cell(scr_rect, (pointer_x, pointer_y))

		if self.selection is None:
			unit = self.matrix[x][y].unit
			self.selection = (x, y)
			if unit is None:
				self.selection_range = []
			else:
				self.list_range((x, y), unit.Move)
		else:
			sx, sy = self.selection
			prev_unit = self.matrix[sx][sy].unit
			curr_unit = self.matrix[x][y].unit
			
			if (x, y) == self.selection:
				self.selection = None
				self.selection_range = []
			elif prev_unit is not None and self.is_in_range((x, y)):
				self.move(prev_unit, (x, y))
				self.selection = None
				self.selection_range = []
			else:
				self.selection = (x, y)
				self.selection_range = []
				if curr_unit is not None:
					self.list_range((x, y), curr_unit.Move)

	def is_in_range(self, (x, y)):
		return (x, y) in self.selection_range

	def isSelected(self, (x, y)):
		return (self.selection == (x, y))
