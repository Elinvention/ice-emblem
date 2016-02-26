# -*- coding: utf-8 -*-
#
#  menu.py, Ice Emblem's menu class.
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
import events


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

	def register(self, context="default"):
		events.register(MOUSEMOTION, self.handle_mouse_motion, context)
		events.register(MOUSEBUTTONDOWN, self.handle_click, context)
		events.register(KEYDOWN, self.handle_keydown, context)

	def unregister(self, context="default"):
		events.unregister(MOUSEMOTION, self.handle_mouse_motion, context)
		events.unregister(MOUSEBUTTONDOWN, self.handle_click, context)
		events.unregister(KEYDOWN, self.handle_keydown, context)

	def draw(self, surface):
		raise NotImplementedError("GUI.draw is not implemented")

	def get_pos(self):
		return self.rect.topleft

	def get_size(self):
		return self.rect.size

	def get_width(self):
		return self.rect.w

	def get_height(self):
		return self.rect.h


class Menu(GUI):
	K_INDEX_INCREASE = K_DOWN
	K_INDEX_DECREASE = K_UP

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
		if index is None:
			if self.index is not None:
				txt = self.menu_entries[self.index][0]
				r = self.font.render(txt, True, self.txt_color, self.bg_color).convert_alpha()
				self.rendered_entries[self.index] = r
			self.prev_index = self.index
			self.index = None
			return

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
		hover = False
		for i, entry in enumerate(self.rendered_entries):
			rect = pygame.Rect(self.get_entry_pos(i), entry.get_size())

			if rect.collidepoint(event.pos):
				self.set_index(i)
				hover = True
		if not hover:
			self.set_index(None)

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

	def get_entry_pos(self, index):
		x = self.padding[3] + self.rect.x
		i = 0
		while i < index:
			x += self.rendered_entries[i].get_width() + 10
			i += 1
		return x, self.padding[0] + self.rect.y

	def draw(self, dest):
		tmp = pygame.Surface(self.rect.size)
		tmp.fill(self.bg_color)

		x = self.padding[3]
		for i, entry in enumerate(self.rendered_entries):
			tmp.blit(entry, (x, self.padding[0]))
			x += entry.get_width() + 10

		dest.blit(tmp, self.rect)


class Button(GUI):
	def __init__(self, text, font, callback=None, padding=(0,0,0,0), pos=(0,0), txt_color=ICE, sel_color=MENU_SEL, bg_color=MENU_BG):
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
		self._focus = False

	def handle_mouse_motion(self, event):
		super().handle_mouse_motion(event)
		if self.rect.collidepoint(event.pos):
			self.focus()
		else:
			self.unfocus()

	def focus(self):
		if not self._focus:
			self.rendered_text = self.font.render(self.text, True, self.txt_color, self.sel_color)
			self._focus = True

	def unfocus(self):
		if self._focus:
			self.rendered_text = self.font.render(self.text, True, self.txt_color, self.bg_color)
			self._focus = False

	def is_focused(self):
		return self._focus

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


class CheckBox(Button):
	def __init__(self, text, font, on_change, checked=False, padding=(0,0,0,0), pos=(0,0), txt_color=ICE, sel_color=MENU_SEL, bg_color=MENU_BG):
		super().__init__(text, font, on_change, padding, pos, txt_color, sel_color, bg_color)
		self.checked = checked
		self.rect.w += 40

	def handle_click(self, event):
		if event.button == 1:
			if self.rect.collidepoint(event.pos):
				self.checked = not self.checked
				if self.callback is not None:
					self.callback(self.checked)
				self.clicked = True

	def draw(self, surface):
		btn = pygame.Surface(self.rect.size)
		btn.fill(self.bg_color)
		btn_pos = (self.padding[1] + self.rect.h, self.padding[0])
		btn.blit(self.rendered_text, btn_pos)
		checkbox = pygame.Surface((self.rect.h, self.rect.h))
		if self.checked:
			checkbox.fill(GREEN)
		else:
			checkbox.fill(RED)
		btn.blit(checkbox, (self.padding[1], self.padding[0]))
		surface.blit(btn, self.rect.topleft)

class Label(GUI):
	def __init__(self, text, font, pos, padding=10, leading=10, txt_color=WHITE, bg_color=MENU_BG):
		self.font = font
		lines = text.split('\n')
		self.text = [ font.render(r, True, txt_color) for r in lines ]
		w = max(l.get_width() for l in self.text) + padding * 2
		h = (font.get_linesize() + leading) * len(lines) + padding * 2
		self.padding = padding
		self.leading = leading
		self.txt_color = txt_color
		self.bg_color = bg_color
		super().__init__(pygame.Rect(pos, (w, h)))

	def draw(self, surface):
		tmp = pygame.Surface(self.rect.size)
		tmp.fill(MENU_BG)
		for i, line in enumerate(self.text):
			y = i * (self.font.get_linesize() + self.leading)
			tmp.blit(line, (self.padding, self.padding + y))
		surface.blit(tmp, self.rect)

class Dialog(Label):
	def __init__(self, text, font, pos, padding=10, leading=10, txt_color=WHITE, bg_color=MENU_BG):
		super().__init__(text, font, pos, padding, leading, txt_color, bg_color)
		self.ok = False
		self.ok_btn = Button("OK", font, self.dismiss, pos=self.rect.midbottom)
		self.ok_btn.rect.move_ip(-self.ok_btn.rect.w//2, -padding)
		self.rect.w = max(self.rect.w, self.ok_btn.get_width() + padding * 2)
		self.rect.h += self.ok_btn.get_height()
		self.padding = padding
		self.leading = leading

	def dismiss(self):
		self.ok = True

	def register(self, context="default"):
		super().register(context)
		self.ok_btn.register(context)

	def unregister(self, context="default"):
		super().unregister(context)
		self.ok_btn.unregister(context)

	def draw(self, surface):
		super().draw(surface)
		self.ok_btn.draw(surface)

class Modal(Label):
	def __init__(self, text, font, pos, padding=10, leading=10, txt_color=WHITE, bg_color=MENU_BG):
		super().__init__(text, font, pos, padding, leading, txt_color, bg_color)
		self.answer = None
		self.yes_btn = Button("Yes", font, lambda: setattr(self, 'answer', True), pos=self.rect.midbottom)
		self.yes_btn.rect.move_ip(-self.yes_btn.rect.w - 20, -padding)
		self.no_btn = Button("No", font, lambda: setattr(self, 'answer', False), pos=self.rect.midbottom)
		self.no_btn.rect.move_ip(20, -padding)
		self.rect.w = max(self.rect.w, self.no_btn.get_width() + self.yes_btn.get_width() + padding * 2)
		self.rect.h += max(self.yes_btn.get_height(), self.no_btn.get_height())

	def handle_keydown(self, event):
		super().handle_keydown(event)
		if event.key in [K_LEFT, K_RIGHT]:
			if self.yes_btn.is_focused():
				self.yes_btn.unfocus()
				self.no_btn.focus()
			else:
				self.yes_btn.focus()
				self.no_btn.unfocus()
		elif event.key == K_SPACE:
			self.answer = self.yes_btn.is_focused()

	def register(self, context="default"):
		super().register(context)
		self.yes_btn.register(context)
		self.no_btn.register(context)

	def unregister(self, context="default"):
		super().unregister(context)
		self.yes_btn.unregister(context)
		self.no_btn.register(context)

	def draw(self, surface):
		super().draw(surface)
		self.yes_btn.draw(surface)
		self.no_btn.draw(surface)


if __name__ == '__main__':
	import events

	pygame.init()
	screen = pygame.display.set_mode((1280, 720), pygame.RESIZABLE)
	pygame.display.set_caption("Ice Emblem GUI Test")
	clock = pygame.time.Clock()

	f = pygame.font.SysFont("Liberation Sans", 24)
	d = Dialog("Lorem ipsum dolor sit amet. ASD. LOL.\n\nTROLOL", f, (50, 100))
	l = Label("TEST LABEL\nASDASDASD\nLOL\n\n\nTROLOL", f, (500, 100))
	m = Modal("Rispondi SI o NO?\n\nFORSE?", f, (800, 400))
	d.register()
	m.register()

	def event_loop(_events):
		screen.fill(BLACK)
		d.draw(screen)
		l.draw(screen)
		m.draw(screen)
		a = Label("ANSWER: " + ("YES" if m.answer else "NO"), f, m.rect.bottomleft)
		a.draw(screen)
		pygame.display.flip()
		clock.tick(60)
		return d.ok

	events.event_loop([MOUSEMOTION, MOUSEBUTTONDOWN, KEYDOWN], event_loop)

	if m.answer is not None:
		print("Answer: %s" % m.answer)

	pygame.quit()

