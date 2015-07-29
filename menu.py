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


class GUI(object):
	EVENT_TYPES = [MOUSEBUTTONDOWN, KEYDOWN, MOUSEMOTION]
	def __init__(self, rect):
		self.rect = rect

	def handle_keydown(self, event):
		if event.type != KEYDOWN:
			raise ValueError("Event type must be KEYDOWN")

	def handle_click(self, event):
		if event.type != MOUSEBUTTONDOWN:
			raise ValueError("Event type must be MOUSEBUTTONDOWN")

	def handle_mouse_motion(self, event):
		if event.type != MOUSEMOTION:
			raise ValueError("Event type must be MOUSEMOTION")

	def draw(self, surface):
		raise NotImplementedError("GUI class is abstract")


class Menu(GUI):
	K_INDEX_INCREASE = K_UP
	K_INDEX_DECREASE = K_DOWN

	def __init__(self, menu_entries, font, callback=None,
			padding=(0, 0, 0, 0), pos=(0, 0),
			txt_color=ICE, sel_color=MENU_SEL, bg_color=MENU_BG):

		self.menu_entries = menu_entries
		self.n_entries = len(menu_entries)
		self.rendered_entries = []
		self.font = font
		self.callback = callback
		self.txt_color = txt_color
		self.sel_color = sel_color
		self.bg_color = bg_color

		for entry in menu_entries:
			render = font.render(entry[0], True, self.txt_color).convert_alpha()
			self.rendered_entries.append(render)

		if len(padding) == 2:
			self.padding = (padding[0], padding[1], padding[0], padding[1])
		elif len(padding) == 4:
			self.padding = padding
		else:
			raise ValueError("Margins shold be a couple or a quadruple")

		size = self.get_width(), self.get_height()
		rect = pygame.Rect(pos, size)
		super().__init__(rect)

		self.prev_index = self.index = None
		self.choice = None
		self.clicked = False  # tells wether latest click was on menu

	def __getitem__(self, key):
		return self.menu_entries[key]

	def get_width(self):
		max_width = 0
		for entry in self.rendered_entries:
			max_width = max(max_width, entry.get_width())
		return max_width + self.padding[1] + self.padding[3]

	def get_height(self):
		return (self.font.get_linesize() * self.n_entries +
				self.padding[0] + self.padding[2])

	def handle_keydown(self, event):
		super().handle_keydown(event)
		if event.key == self.K_INDEX_DECREASE:
			self.move_index(-1)
		elif event.key == self.K_INDEX_INCREASE:
			self.move_index(1)
		elif event.key == K_ESCAPE:
			if self.callback is not None:
				self.choice = -1
				self.callback()
		elif (event.key == K_RETURN or event.key == K_SPACE) and self.index is not None:
			self.choice = self.index
			if self.menu_entries[self.index][1] is not None:
				return self.menu_entries[self.index][1]()

	def set_index(self, index):
		self.prev_index = self.index
		self.index = index % self.n_entries

		if self.index != self.prev_index:
			for i, entry in enumerate(self.menu_entries):
				entry_text, entry_callback = entry
				if i == self.index:
					render = self.font.render(entry_text, True, self.txt_color, self.sel_color).convert_alpha()
					self.rendered_entries[i] = render
				elif i == self.prev_index:
					render = self.font.render(entry_text, True, self.txt_color, self.bg_color).convert_alpha()
					self.rendered_entries[i] = render

	def move_index(self, amount):
		if self.index is None:
			self.set_index(0)
		else:
			self.set_index(self.index + amount)

	def get_entry_pos(self, i):
		return (self.padding[3] + self.rect.x,
				self.padding[0] + self.rect.y + i * self.font.get_linesize())

	def handle_click(self, event):
		super().handle_click(event)
		if event.button == 1:
			self.clicked = False
			for i, entry in enumerate(self.rendered_entries):
				rect = pygame.Rect(self.get_entry_pos(i), entry.get_size())
				if rect.collidepoint(event.pos):
					self.clicked = True
					self.choice = i
					if self.menu_entries[i][1] is not None:
						return self.menu_entries[i][1]()
		elif event.button == 3:
			if self.callback is not None:
				self.choice = -1
				self.callback()

	def handle_mouse_motion(self, event):
		super().handle_mouse_motion(event)
		for i, entry in enumerate(self.rendered_entries):
			rect = pygame.Rect(self.get_entry_pos(i), entry.get_size())

			if rect.collidepoint(event.pos):
				self.set_index(i)

	def draw(self, dest):
		tmp = pygame.Surface(self.rect.size).convert_alpha()
		tmp.fill(self.bg_color)
		linesize = self.font.get_linesize()

		for i, entry in enumerate(self.rendered_entries):
			tmp.blit(entry, (self.padding[3], i * linesize + self.padding[0]))

		dest.blit(tmp, self.rect)


class HorizontalMenu(Menu):
	K_INDEX_INCREASE = K_LEFT
	K_INDEX_DECREASE = K_RIGHT
	def __init__(self, menu_entries, font, callback=None, padding=(0, 0, 0, 0), pos=(0, 0)):
		super().__init__(menu_entries, font, callback, padding, pos)

	def get_width(self):
		width = 0
		for entry in self.rendered_entries:
			width += entry.get_width() + 10
		return width + self.padding[1] + self.padding[3]

	def get_height(self):
		return self.font.get_linesize() + self.padding[0] + self.padding[2]

	def get_entry_pos(self, i):
		return (self.padding[3] + self.rect.x + i * (self.rendered_entries[i].get_width() + 10),
				self.padding[0] + self.rect.y)

	def draw(self, dest):
		tmp = pygame.Surface(self.rect.size)
		tmp.fill(self.bg_color)

		for i, entry in enumerate(self.rendered_entries):
			tmp.blit(entry, (self.padding[3] + i * (entry.get_width() + 10), self.padding[0]))

		dest.blit(tmp, self.rect)


class Button(GUI):
	def __init__(self, text, font, callback, padding=(0,0,0,0), pos=(0,0), txt_color=ICE, sel_color=MENU_SEL, bg_color=MENU_BG):
		self.text = text
		self.rendered_text = font.render(text, True, txt_color)
		self.font = font
		self.callback = callback
		self.padding = padding
		self.txt_color = txt_color
		self.sel_color = sel_color
		self.bg_color = bg_color
		w = self.rendered_text.get_width() + padding[1] + padding[3]
		h = self.rendered_text.get_height() + padding[0] + padding[2]
		super().__init__(pygame.Rect(pos, (w,h)))
		self.clicked = False
		self.hover = False

	def handle_mouse_motion(self, event):
		super().handle_mouse_motion(event)
		collide = self.rect.collidepoint(event.pos)
		if collide and not self.hover:
			self.rendered_text = self.font.render(self.text, True, self.txt_color, self.sel_color)
			self.hover = True
		elif not collide and self.hover:
			self.rendered_text = self.font.render(self.text, True, self.txt_color, self.bg_color)
			self.hover = False

	def handle_click(self, event):
		super().handle_click(event)
		if event.button == 1:
			if self.rect.collidepoint(event.pos):
				if self.callback is not None:
					self.callback()
				self.clicked = True

	def handle_keydown(self, event):
		super().handle_keydown(event)

	def draw(self, surface):
		btn = pygame.Surface(self.rect.size)
		btn.fill(self.bg_color)
		btn.blit(self.rendered_text, (self.padding[1], self.padding[0]))
		surface.blit(btn, self.rect.topleft)
