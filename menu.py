# -*- coding: utf-8 -*-
#
#  menu.py, Ice Emblem's unit class.
#
#  Copyright 2015 Elia Argentieri <elia.argentieri@openmailbox.org>
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.


import pygame
import logging
from pygame.locals import *
from colors import *


class Menu(object):
	EVENT_TYPES = [MOUSEBUTTONDOWN, QUIT, KEYDOWN, MOUSEMOTION]
	BACKGROUND_COLOR = (51, 51, 51)
	TEXT_COLOR = ICE
	SELECTION_COLOR = (96, 144, 145)

	def __init__(self, menu_entries, font, callback=None, margins=(0, 0, 0, 0), pos=(0, 0)):
		self.menu_entries = menu_entries
		self.callback = callback
		self.n_entries = len(menu_entries)
		self.font = font
		self.rendered_entries = []

		for entry in menu_entries:
			render = font.render(entry[0], True, self.TEXT_COLOR).convert_alpha()
			self.rendered_entries.append(render)

		if len(margins) == 2:
			self.margins = (margins[0], margins[1], margins[0], margins[1])
		elif len(margins) == 4:
			self.margins = margins
		else:
			raise ValueError("Margins shold be a couple or a quadruple")
		self.size = (self.get_width(), self.get_height())
		self.rect = pygame.Rect(pos, self.size)
		self.w, self.h = self.size
		self.prev_index = self.index = None
		self.choice = None

	def __getitem__(self, key):
		return self.menu_entries[key]

	def get_width(self):
		max_width = 0
		for entry in self.rendered_entries:
			max_width = max(max_width, entry.get_width())
		return max_width + self.margins[1] + self.margins[3]

	def get_height(self):
		return (self.font.get_linesize() * self.n_entries +
				self.margins[0] + self.margins[2])

	def handle_keydown(self, event):
		if event.type != KEYDOWN:
			raise ValueError("Event type must be KEYDOWN")
		elif event.key == K_UP:
			self.move_index(-1)
		elif event.key == K_DOWN:
			self.move_index(1)
		elif event.key == K_ESCAPE:
			if self.callback is not None:
				self.choice = -1
				self.callback()
		elif (event.key == K_RETURN or event.key == K_SPACE) and self.index is not None:
			if self.menu_entries[self.index][1] is not None:
				return self.menu_entries[self.index][1]()
			self.choice = self.index

	def set_index(self, index):
		self.prev_index = self.index
		self.index = index % self.n_entries

		if self.index != self.prev_index:
			for i, entry in enumerate(self.menu_entries):
				entry_text, entry_callback = entry
				if i == self.index:
					render = self.font.render(entry_text, True, self.TEXT_COLOR, self.SELECTION_COLOR).convert_alpha()
					self.rendered_entries[i] = render
				elif i == self.prev_index:
					render = self.font.render(entry_text, True, self.TEXT_COLOR, self.BACKGROUND_COLOR).convert_alpha()
					self.rendered_entries[i] = render

	def move_index(self, amount):
		if self.index is None:
			self.set_index(0)
		else:
			self.set_index(self.index + amount)

	def handle_click(self, event):
		if event.type != MOUSEBUTTONDOWN:
			raise ValueError("Event type must be MOUSEBUTTONDOWN")
		elif event.button == 1:
			for i, entry in enumerate(self.rendered_entries):
				pos = (self.margins[3] + self.rect.x, self.margins[0] + self.rect.y + (i * self.font.get_linesize()))
				rect = pygame.Rect(pos, entry.get_size())

				if rect.collidepoint(event.pos):
					self.choice = i
					if self.menu_entries[i][1] is not None:
						return self.menu_entries[i][1]()
		elif event.button == 3:
			if self.callback is not None:
				self.choice = -1
				self.callback()

	def handle_mouse_motion(self, event):
		if event.type != MOUSEMOTION:
			raise ValueError("Event type must be MOUSEMOTION")
		for i, entry in enumerate(self.rendered_entries):
			pos = (self.margins[3] + self.rect.x, self.margins[0] + self.rect.y + (i * self.font.get_linesize()))
			rect = pygame.Rect(pos, entry.get_size())

			if rect.collidepoint(event.pos):
				self.set_index(i)

	def render(self, surface=None):
		if surface is None:
			surface = pygame.Surface(self.size)

		surface.fill(self.BACKGROUND_COLOR)

		for i, entry in enumerate(self.rendered_entries):
			surface.blit(entry, (self.margins[3], i * self.font.get_linesize() + self.margins[0]))

		return surface
