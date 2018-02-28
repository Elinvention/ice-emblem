import pygame
from pygame.locals import *
import gui
import state as s
import events
import game
import display
from colors import *
from fonts import SMALL_FONT


class ActionMenu(gui.Menu):
	"""
	Shows the action menu and handles input until it is dismissed.
	"""

	def attack(self):
		done = False

		def mousebuttondown(event):
			nonlocal done
			# user must click on an enemy unit
			if event.button == 1 and s.loaded_map.is_attack_click(event.pos):
				game.battle_wrapper(s.loaded_map.cursor.coord)
				done = True
			elif event.button == 3:
				s.loaded_map.move_undo()
				done = True

		def keydown(event):
			nonlocal done
			# user must choose an enemy unit
			if event.key == pygame.K_SPACE and s.loaded_map.is_enemy_cursor():
				game.battle_wrapper(s.loaded_map.cursor.coord)
				done = True
			elif event.key == pygame.K_ESCAPE:
				s.loaded_map.move_undo()
				done = True
			s.loaded_map.cursor.update(event)

		s.loaded_map.prepare_attack()
		events.new_context("Attack")
		events.register(MOUSEBUTTONDOWN, mousebuttondown, "Attack")
		events.register(KEYDOWN, keydown, "Attack")
		events.register(MOUSEMOTION, s.loaded_map.cursor.update, "Attack")
		def loop(_events):
			self.draw(False)
			display.draw_fps()
			display.flip()
			return done
		events.event_loop(loop, True, "Attack")

	def items(self):
		unit = s.loaded_map.curr_unit
		def setitem(item):
			def set(*args):
				unit.items.active = item
				unit.played = True
				s.loaded_map.reset_selection()
			return set
		self.menu_entries = [(i.name, setitem(i)) for i in unit.items]
		self.user_interacted = False

	def __init__(self, **kwargs):
		actions = [
			(_("Attack"), lambda *_: self.attack()),
			(_("Items"), lambda *_: self.items()),
			(_("Wait"), lambda *_: s.loaded_map.wait()),
		] if len(s.loaded_map.nearby_enemies()) > 0 else [
			(_("Items"), lambda *_: self.items()),
			(_("Wait"), lambda *_: s.loaded_map.wait()),
		]
		super().__init__(actions, SMALL_FONT, callback=lambda *_: s.loaded_map.move_undo(), **kwargs)

	def begin(self):
		super().begin()
		s.loaded_map.still_attack_area()
		s.loaded_map.update_highlight()
		s.loaded_map.draw(display.window)
		game.sidebar.update()

	def draw(self, draw_self=True):
		display.window.fill(BLACK)
		s.loaded_map.draw(display.window)
		game.sidebar.update()
		if draw_self:
			super().draw()

