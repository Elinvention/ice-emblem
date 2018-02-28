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
from pygame.locals import *
from colors import *
import room
import display
import utils


class GUI(room.Room):
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		self.user_interacted = False
		self._padding = (0, 0, 0, 0)
		self._content_size = (0, 0)
		self.rect = pygame.Rect(kwargs.get('pos',  (0, 0)), (0, 0))
		self.padding = kwargs.get('padding', (0, 0, 0, 0))

	@property
	def content_size(self):
		return self._content_size

	@content_size.setter
	def content_size(self, size):
		self._content_size = size
		self.update_size()

	@property
	def padding(self):
		return self._padding

	@padding.setter
	def padding(self, padding):
		self._padding = padding
		if isinstance(padding, int):
			self._padding = (padding,) * 4
		elif len(padding) == 2:
			self._padding = padding * 2
		elif len(padding) == 4:
			self._padding = padding
		else:
			raise ValueError("padding shold be either an int or a couple or a quadruple")
		self.update_size()

	def update_size(self):
		self.rect.size = (self.padding[1] + self.padding[3] + self.content_size[0],
						self.padding[0] + self.padding[2] + self.content_size[1])

	def handle_keydown(self, event):
		if event.type != KEYDOWN:
			raise ValueError("Event type must be KEYDOWN")

	def handle_click(self, event):
		if event.type != MOUSEBUTTONDOWN:
			raise ValueError("Event type must be MOUSEBUTTONDOWN")

	def handle_mouse_motion(self, event):
		if event.type != MOUSEMOTION:
			raise ValueError("Event type must be MOUSEMOTION")

	def begin(self):
		self.register(MOUSEMOTION, self.handle_mouse_motion)
		self.register(MOUSEBUTTONDOWN, self.handle_click)
		self.register(KEYDOWN, self.handle_keydown)
		super().begin()

	def end(self):
		self.unregister(MOUSEMOTION, self.handle_mouse_motion)
		self.unregister(MOUSEBUTTONDOWN, self.handle_click)
		self.unregister(KEYDOWN, self.handle_keydown)
		super().end()

	def draw(self):
		raise NotImplementedError("GUI.draw is not implemented")

	def loop(self, _events):
		return self.user_interacted

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

	def __init__(self, menu_entries, font, **kwargs):
		super().__init__(**kwargs)
		self.font = font
		self.callback = kwargs.get('callback', None)
		self.txt_color = kwargs.get('txt_color', ICE)
		self.sel_color = kwargs.get('sel_color', MENU_SEL)
		self.bg_color = kwargs.get('bg_color', MENU_BG)
		self.leading = kwargs.get('leading', 10)

		self.menu_entries = menu_entries

		self.prev_index = self.index = None
		self.choice = None
		self.clicked = False  # tells wether latest click was on menu

	def __getitem__(self, key):
		return self.menu_entries[key]

	def compute_content_size(self):
		w = 0
		for entry in self.rendered_entries:
			w = max(w, entry.get_width())
		h = self.font.get_linesize() * len(self.menu_entries) + self.leading * (len(self.menu_entries) - 1)
		self.content_size = w, h

	@property
	def menu_entries(self):
		return self._menu_entries

	@menu_entries.setter
	def menu_entries(self, entries):
		self._menu_entries = entries
		self.rendered_entries = [self.font.render(entry[0], True, self.txt_color).convert_alpha() for entry in entries]
		self.compute_content_size()
		self.prev_index = self.index = None

	def call_callback(self, i):
		callback = self.menu_entries[i][1]
		if callable(callback):
			callback(self, self.menu_entries[i][0])

	def handle_keydown(self, event):
		super().handle_keydown(event)
		if event.key == self.K_INDEX_DECREASE:
			self.move_index(-1)
		elif event.key == self.K_INDEX_INCREASE:
			self.move_index(1)
		elif event.key == K_ESCAPE:
			if self.callback is not None:
				self.choice = -1
				self.user_interacted = True
				self.callback(self)
		elif (event.key == K_RETURN or event.key == K_SPACE) and self.index is not None:
			self.choice = self.index
			self.user_interacted = True
			self.call_callback(self.index)

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
		self.index = index % len(self.menu_entries)

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
				self.padding[0] + self.rect.y + i * (self.font.get_linesize() + self.leading))

	def handle_click(self, event):
		super().handle_click(event)
		if event.button == 1:
			self.clicked = False
			for i, entry in enumerate(self.rendered_entries):
				rect = pygame.Rect(self.get_entry_pos(i), entry.get_size())
				if rect.collidepoint(event.pos):
					self.clicked = True
					self.choice = i
					self.user_interacted = True
					self.call_callback(i)
		elif event.button == 3:
			if self.callback is not None:
				self.choice = -1
				self.callback(self)
				self.user_interacted = True

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

	def draw(self):
		tmp = pygame.Surface(self.rect.size).convert_alpha()
		tmp.fill(self.bg_color)
		linesize = self.font.get_linesize()

		for i, entry in enumerate(self.rendered_entries):
			tmp.blit(entry, (self.padding[3], i * (linesize + self.leading) + self.padding[0]))

		display.window.blit(tmp, self.rect)


class HorizontalMenu(Menu):
	K_INDEX_INCREASE = K_LEFT
	K_INDEX_DECREASE = K_RIGHT
	def __init__(self, menu_entries, font, **kwargs):
		super().__init__(menu_entries, font, **kwargs)

	def compute_content_size(self):
		w = 0
		for entry in self.rendered_entries:
			w += entry.get_width()
		w += self.leading * (len(self.menu_entries) - 1)
		h = self.font.get_linesize()
		self.content_size = w, h

	def get_entry_pos(self, index):
		x = self.padding[3] + self.rect.x
		i = 0
		while i < index:
			x += self.rendered_entries[i].get_width() + self.leading
			i += 1
		return x, self.padding[0] + self.rect.y

	def draw(self):
		tmp = pygame.Surface(self.rect.size)
		tmp.fill(self.bg_color)

		x = self.padding[3]
		for i, entry in enumerate(self.rendered_entries):
			tmp.blit(entry, (x, self.padding[0]))
			x += entry.get_width() + 10

		display.window.blit(tmp, self.rect)


class Button(GUI):
	def __init__(self, text, font, **kwargs):
		super().__init__(**kwargs)
		self.font = font
		self.clicked = False
		self._focus = False
		self.callback = kwargs.get('callback', None)
		self.txt_color = kwargs.get('txt_color', ICE)
		self.sel_color = kwargs.get('sel_color', MENU_SEL)
		self.bg_color = kwargs.get('bg_color', MENU_BG)
		self.set_text(text)

	def set_text(self, text):
		self.text = text
		self.rendered_text = self.font.render(text, True, self.txt_color, self.sel_color if self._focus else self.bg_color)
		self.compute_content_size()

	def compute_content_size(self):
		self.content_size = self.rendered_text.get_size()

	def loop(self, _events):
		return self.clicked

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
					self.callback(self)
				self.clicked = True

	def handle_keydown(self, event):
		super().handle_keydown(event)

	def draw(self):
		btn = pygame.Surface(self.rect.size)
		btn.fill(self.bg_color)
		btn.blit(self.rendered_text, (self.padding[3], self.padding[0]))
		display.window.blit(btn, self.rect.topleft)


class CheckBox(Button):
	def __init__(self, text, font, checked=False, **kwargs):
		super().__init__(text, font, **kwargs)
		self.checked = checked
		self.compute_content_size()

	def compute_content_size(self):
		super().compute_content_size()
		self.content_size = (self.content_size[0] + self.content_size[1], self.content_size[1])

	def handle_click(self, event):
		if event.button == 1:
			if self.rect.collidepoint(event.pos):
				self.checked = not self.checked
				if self.callback is not None:
					self.callback(self, self.checked)
				self.clicked = True

	def draw(self):
		btn = pygame.Surface(self.rect.size)
		btn.fill(self.bg_color)
		btn_pos = (self.padding[3] + self.content_size[1], self.padding[0])
		btn.blit(self.rendered_text, btn_pos)
		checkbox = pygame.Surface((self.content_size[1],) * 2)
		if self.checked:
			checkbox.fill(GREEN)
		else:
			checkbox.fill(RED)
		btn.blit(checkbox, (self.padding[3], self.padding[0]))
		display.window.blit(btn, self.rect.topleft)


class Label(GUI):
	def __init__(self, text, font, **kwargs):
		super().__init__(**kwargs)
		self.font = font
		self.leading = kwargs.get('leading', 10)
		self.txt_color = kwargs.get('txt_color', WHITE)
		self.bg_color = kwargs.get('bg_color', MENU_BG)
		self.set_text(text)

	def draw(self):
		tmp = pygame.Surface(self.rect.size)
		tmp.fill(MENU_BG)
		for i, line in enumerate(self.text):
			y = i * (self.font.get_linesize() + self.leading)
			tmp.blit(line, (self.padding[1], self.padding[0] + y))
		display.window.blit(tmp, self.rect)

	def set_text(self, text):
		lines = text.split('\n')
		self.text = [ self.font.render(r, True, self.txt_color) for r in lines ]
		self.compute_content_size()

	def compute_content_size(self):
		w = max(l.get_width() for l in self.text)
		h = self.font.get_linesize() * len(self.text) + self.leading * (len(self.text) - 1)
		self.content_size = w, h


class Dialog(Label):
	def __init__(self, text, font, **kwargs):
		self.ok = False
		self.ok_btn = Button("OK", font, callback=lambda _:self.dismiss())
		self.callback = kwargs.get('callback', None)
		super().__init__(text, font, **kwargs)
		self.ok_btn.rect.midbottom = self.rect.midbottom
		self.add_child(self.ok_btn)

	def dismiss(self):
		self.ok = True
		if callable(self.callback):
			self.callback(self)

	def draw(self):
		super().draw()
		self.draw_children()

	def loop(self, _events):
		return self.ok

	def set_text(self, text):
		super().set_text(text)
		self.ok_btn.rect.midbottom = self.rect.midbottom

	def compute_content_size(self):
		super().compute_content_size()
		self.content_size = self.content_size[0], self.content_size[1] + self.ok_btn.rect.h

class Modal(Label):
	def __init__(self, text, font, **kwargs):
		super().__init__(text, font, **kwargs)
		self.callback = kwargs.get('callback', None)
		self.answer = None
		self.yes_btn = Button("Yes", font, callback=lambda _: self.yes(), pos=self.rect.midbottom)
		self.yes_btn.rect.move_ip(-self.yes_btn.rect.w - 20, -self.padding[3])
		self.no_btn = Button("No", font, callback=lambda _: self.no(), pos=self.rect.midbottom)
		self.no_btn.rect.move_ip(20, -self.padding[3])
		w = max(self.content_size[0], self.no_btn.get_width() + self.yes_btn.get_width())
		h = self.content_size[1] + max(self.yes_btn.get_height(), self.no_btn.get_height())
		self.content_size = (w, h)
		self.add_child(self.yes_btn)
		self.add_child(self.no_btn)

	def yes(self):
		self.answer = True
		if callable(self.callback):
			self.callback(self, self.answer)

	def no(self):
		self.answer = False
		if callable(self.callback):
			self.callback(self, self.answer)

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

	def draw(self):
		super().draw()
		self.draw_children()

	def loop(self, _events):
		return self.answer is not None


if __name__ == '__main__':
	import logging
	logging.basicConfig(level=0)
	pygame.init()
	screen = pygame.display.set_mode((1280, 720), pygame.RESIZABLE)
	pygame.display.set_caption("Ice Emblem GUI Test")

	f = pygame.font.SysFont("Liberation Sans", 24)
	d = Dialog("Lorem ipsum dolor sit amet. ASD. LOL.\n\nTROLOL", f, callback=lambda self: self.set_text("Hai premuto OK"), pos=(50, 100))
	l = Label("TEST LABEL\nASDASDASD\nLOL\n\n\nTROLOL", f, pos=(50, 400))
	a = Label("NO ANSWER", f)
	m = Modal("Rispondi SI o NO?\n\nFORSE?", f, callback=lambda _,ans: a.set_text("SI" if ans else "NO"), pos=(800, 100))
	a.rect.topleft = m.rect.bottomleft
	q = Button("Quit", f, callback=utils.return_to_os)
	c = Label("SELEZIONA DAL MENU", f)
	setc = lambda _,choice: c.set_text(choice)
	h = HorizontalMenu([("A", setc), ("B", setc)], f, pos=(800, 300))
	c.rect.topleft = h.rect.bottomleft
	s = Label("SELEZIONA DAL MENU", f)
	sets = lambda _,choice: s.set_text(choice)
	v = Menu([("A", sets), ("B", sets)] * 2, f, pos=(800, 500), padding=(20, 120))
	s.rect.topleft = v.rect.bottomleft
	cb = CheckBox("N", f, False, callback=lambda obj, chk: obj.set_text(str(chk)), pos=(800, 50))

	class GUITest(room.Room):
		def begin(self):
			self.add_children([d, l, m, a, q, c, h, s, v, cb])
			super().begin()
		def draw(self):
			screen.fill(BLACK)
			super().draw()

	room.run_room(GUITest())

	if m.answer is not None:
		print("Answer: %s" % m.answer)

	pygame.quit()

