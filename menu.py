import pygame
from pygame.locals import *


class Menu(object):
	BACKGROUND_COLOR = (51,51,51)
	TEXT_COLOR =  (255, 255, 153)
	SELECTION_COLOR = (153,102,255)

	def __init__(self, menu_entries, font, pos=(0, 0)):
		self.menu_entries = menu_entries
		self.n_entries = len(menu_entries)
		self.font = font
		self.rendered_entries = []

		for i, entry in enumerate(menu_entries):
			render = font.render(entry, True, self.TEXT_COLOR).convert()
			render_rect = pygame.Rect(render.get_size(), (0, i * font.get_fontsize()))
			self.rendered_entries.append((render, render_rect))

		self.size = (self.__max_width(), font.get_fontsize() * self.n_entries)
		self.pos = pos
		self.rect = pygame.Rect(self.size, self.pos)
		self.w, self.h = self.size
		self.prev_index = self.index = 0
		self.choice = None

	def __getitem__(self, key):
		return self.menu_entries[key]

	def __max_width(self):
		max_width = 0
		for entry in rendered_entries:
			max_width = max(max_width, entry.get_width())
		return max_width

	def handle_keydown(self, event):
		if even.type != KEYDOWN:
			raise ValueError("Event type must be KEYDOWN")
		elif event.key == K_UP:
			amount = -1
		elif event.key == K_DOWN:
			amount = 1
		elif event.key == K_RETURN:
			self.choice = self.index
			return self.index

		self.prev_index = self.index
		self.index += amount
		self.index %= self.n_entries

	def handle_click(self, event):
		if even.type != MOUSEDOWN:
			raise ValueError("Event type must be MOUSEDOWN")
		elif event.button == 1:
			

	def render(self):
		surface = pygame.Surface(self.size)
		surface.fill(self.BACKGROUND_COLOR)

		for i, entry in enumerate(self.menu_entries):
			if self.index != self.prev_index:
				if i == self.index:
					render = font.render(entry, True, self.TEXT_COLOR, self.SELECTION_COLOR).convert()
					entry[1] = self.menu_entries[i][1] = render
				elif i == self.prev_index:
					render = font.render(entry, True, self.TEXT_COLOR).convert()
					entry[1] = self.menu_entries[i][1] = render
				self.prev_index = self.index

			surface.blit(entry, (0, self.font.get_size() * i))

		return surface
