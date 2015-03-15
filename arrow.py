import pygame


class Arrow(object):
	"""

	"""
	def __init__(self, image_path, tilesize):
		self.image = pygame.image.load(image_path)
		self.w, self.h = self.size = self.image.get_size()

		self.arrow = {}

		self.path = []
		self.first_coord = None

		self.update_tiles(tilesize)

	def update_tiles(self, tilesize):
		rw, rh = rectsize = (self.w // 4, self.h // 4)

		arrow_parts = []
		for j in range(4):
			for i in range(4):
				pos = (i * rw, j * rh)
				rect = pygame.Rect(pos, rectsize)
				img = pygame.Surface.subsurface(self.image, rect)
				img = pygame.transform.smoothscale(img, tilesize)
				arrow_parts.append(img)

		assert(len(arrow_parts) == 16)

		self.arrow = {
			'horizontal': arrow_parts[1],
			'vertical': arrow_parts[4],
			'topleft': arrow_parts[0],
			'topright': arrow_parts[3],
			'bottomleft': arrow_parts[12],
			'bottomright': arrow_parts[15],
			'up': arrow_parts[5],
			'down': arrow_parts[10],
			'left': arrow_parts[9],
			'right': arrow_parts[6],
		}

	def get_arrow_part(self, coord):
		index = self.path.index(coord)
		a = self.path[index - 1] if index - 1 >= 0 else self.first_coord
		b = self.path[index]
		c = self.path[index + 1] if (index + 1) < len(self.path) else None

		if c is None:
			ax, ay = a
			bx, by = b
			if bx == ax + 1:
				return self.arrow['right']
			elif bx == ax - 1:
				return self.arrow['left']
			elif by == ay + 1:
				return self.arrow['down']
			elif by == ay - 1:
				return self.arrow['up']
		else:
			ax, ay = a
			bx, by = b
			cx, cy = c
			if ax == bx == cx:
				return self.arrow['vertical']
			elif ay == by == cy:
				return self.arrow['horizontal']

			elif (ax == bx and ay < by and bx < cx and by == cy) or (cx == bx and by == ay and cy < by and bx < ax):
				return self.arrow['bottomleft']

			elif (ax == bx and ay < by and bx > cx and by == cy) or (ax < bx and ay == by and bx == cx and by > cy):
				return self.arrow['bottomright']

			elif (ax == bx and ay > by and bx > cx and by == cy) or (ax < bx and ay == by and bx == cx and by < cy):
				return self.arrow['topright']

			elif (ax == bx and ay > by and bx < cx and by == cy) or (ax > bx and ay == by and bx == cx and by < cy):
				return self.arrow['topleft']

			else:
				raise ValueError("ArrowError: " + str((a, b, c)))
