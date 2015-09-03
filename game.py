# -*- coding: utf-8 -*-
#
#  Game.py, Ice Emblem's main game class.
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
import sys
import os
import logging
import time

import map
import unit
import gui
import utils
import ai
from colors import *


class EventHandler(object):
	"""
	This class should provide a uniform and comfortable way to handle
	events.
	"""

	def __init__(self, name=""):
		self._callbacks = {
			QUIT: [utils.return_to_os],
			VIDEORESIZE: [utils.videoresize_handler],
		}
		self.name = ""
		self.logger = logging.getLogger('EventHandler' + name)

	def __call__(self):
		"""
		Process new events
		"""
		processed = {}
		for event in pygame.event.get():
			processed[event.type] = self._process_event(event)
		return processed

	def wait(self, event_types=[MOUSEBUTTONDOWN, KEYDOWN], timeout=-1):
		"""
		if the timeout argument is positive, returns after the specified
		number of milliseconds.
		"""
		event_types.append(QUIT)
		event_types.append(VIDEORESIZE)

		if timeout > 0:
			pygame.time.set_timer(USEREVENT+1, timeout)
			event_types.append(USEREVENT+1)

		if pygame.event.peek(event_types):  # if events we are looking for are already available
			for event in pygame.event.get(event_types):  # get them
				self._process_event(event)
			pygame.event.clear()  # clear queue from events we don't want
		else:
			event = pygame.event.wait()  # wait for an interesting event
			while event.type not in event_types:
				event = pygame.event.wait()
			self._process_event(event)

		if timeout > 0:
			pygame.time.set_timer(USEREVENT+1, 0)

		return event

	def _process_event(self, event):
		ret = []
		if event.type in self._callbacks:
			for callback in self._callbacks[event.type]:
				ret.append(callback(event))
		return ret

	def register(self, event_type, callback):
		"""
		Bind a callback function to a specified event type.
		"""
		if event_type in self._callbacks:
			if callback not in self._callbacks[event_type]:
				self._callbacks[event_type].append(callback)
		else:
			self._callbacks[event_type] = [callback]
		self.logger.debug('%s registered %s' % (pygame.event.event_name(event_type), callback))

	def unregister(self, event_type, callback=None):
		for key in self._callbacks:
			if key == event_type:
				if callback:
					if callback in self._callbacks[key]:
						self._callbacks[key].remove(callback)
				elif len(self._callbacks[key]) > 0:
					callback = self._callbacks[key].pop()
				self.logger.debug('%s unregistered %s' % (pygame.event.event_name(event_type), callback))
				break

	def bind_key(self, key, callback):
		def f(event):
			if key == event.key:
				callback()
		self.register(KEYDOWN, f)

	def bind_click(self, mouse_button, callback, area=None, inside=True):
		def f(event):
			if event.button == mouse_button:
				if (area is None or (inside and area.collidepoint(event.pos)) or
						(not inside and not area.collidepoint(event.pos))):
					callback()
		self.register(MOUSEBUTTONDOWN, f)

	def reset(self):
		self.logger.debug('Reset')
		self._callbacks = {
			QUIT: [utils.return_to_os],
			VIDEORESIZE: [utils.videoresize_handler],
		}


class Sidebar(object):
	def __init__(self, screen, font, unit_manager):
		self.screen = screen
		self.rect = pygame.Rect((screen.get_width() - 200, 0), (200, screen.get_height()))
		self.start_time = pygame.time.get_ticks()
		self.font = font
		self.endturn_btn = gui.Button(_("End Turn"), self.font, unit_manager.switch_turn)

	def update(self, unit, terrain, coord, team):
		self.rect.h = self.screen.get_height()
		self.rect.x = self.screen.get_width() - self.rect.w
		self.endturn_btn.rect.bottomright = self.rect.bottomright

		sidebar = pygame.Surface(self.rect.size)
		sidebar.fill((100, 100, 100))

		turn_s = self.font.render(_('%s phase') % team.name, True, team.color)
		pos = turn_s.get_rect(top=40, left=5)
		sidebar.blit(turn_s, pos)

		if terrain is not None:
			t_name = self.font.render(terrain.name, True, WHITE)
			t_def = self.font.render(_("Def: %d") % terrain.defense, True, WHITE)
			t_avoid = self.font.render(_("Avoid: %d") % terrain.avoid, True, WHITE)
			t_allowed = self.font.render(_("Allowed: %s") % terrain.allowed, True, WHITE)
			pos = t_name.get_rect(top=pos.y + 40, left=5)
			sidebar.blit(t_name, pos)
			pos.left += pos.w + 5
			sidebar.blit(terrain.surface, pos)
			pos = t_def.get_rect(top=pos.y + 40, left=5)
			sidebar.blit(t_def, pos)
			pos = t_avoid.get_rect(top=pos.y + 40, left=5)
			sidebar.blit(t_avoid, pos)
			pos = t_allowed.get_rect(top=pos.y + 40, left=5)
			sidebar.blit(t_allowed, pos)

		if unit is not None:
			unit_name = self.font.render(unit.name, True, unit.color)
		else:
			unit_name = self.font.render(_("No units"), True, WHITE)
		pos = unit_name.get_rect(top=pos.y + 40, left=5)
		sidebar.blit(unit_name, pos)

		cell_label = self.font.render('X: %d Y: %d' % coord, True, WHITE)
		pos = cell_label.get_rect(top=pos.y + 40, left=5)
		sidebar.blit(cell_label, pos)

		time = pygame.time.get_ticks() - self.start_time
		time //= 1000
		sec = time % 60
		minutes = time / 60 % 60
		hours = time / 3600 % 24
		time_s = self.font.render("%02d:%02d:%02d" % (hours, minutes, sec), True, WHITE)
		pos = time_s.get_rect(top=pos.y + 40, left=5)
		sidebar.blit(time_s, pos)

		self.screen.blit(sidebar, self.rect)
		self.endturn_btn.draw(self.screen)


class ResizableImage(object):
	def __init__(self, path, size, pos, keep_ratio=True, smooth=True):
		self.path = path
		self.original_image = pygame.image.load(path).convert_alpha()
		self.__size = self.original_image.get_size()
		self.rect = self.original_image.get_rect(topleft=pos)
		self.resize(size, keep_ratio, smooth)

	def resize(self, new_size, keep_ratio=True, smooth=True):
		try:
			new_size = new_size.size  # might be a pygame.event.Event
		except AttributeError:
			pass
		if new_size == self.__size:
			return
		if keep_ratio:
			img_size = utils.resize_keep_ratio(self.original_image.get_size(), new_size)
		else:
			img_size = new_size
		if smooth:
			self.image = pygame.transform.smoothscale(self.original_image, img_size)
		else:
			self.image = pygame.transform.scale(self.original_image, img_size)
		self.rect.size = img_size
		self.__size = new_size

	def draw(self, surface):
		surface.blit(self.image, self.rect)


class Game(object):
	TIME_BETWEEN_ATTACKS = 2000  # Time to wait between each attack animation
	TIMEOUTEVENT = USEREVENT + 1
	INTERRUPTEVENT = USEREVENT + 2

	def __init__(self, screen, units, map_path):
		self.screen = screen
		self.clock = pygame.time.Clock()

		font_path = os.path.abspath('fonts/Medieval Sharp/MedievalSharp.ttf')
		self.MAIN_MENU_FONT = pygame.font.Font(font_path, 48)
		self.MAIN_FONT = pygame.font.Font(font_path, 36)
		self.SMALL_FONT = pygame.font.Font(font_path, 24)
		self.FPS_FONT = pygame.font.SysFont("Liberation Sans", 12)

		team1_units = [units['Boss'], units['Skeleton'], units['Soldier']]
		team2_units = [units['Pirate Tux'], units['Ninja'], units['Pirate']]

		team1 = unit.Team(name=_("Blue Team"), color=BLUE, relation=10, ai=None, units=team1_units, boss=units['Boss'])
		team2 = unit.Team(name=_("Red Team"), color=RED, relation=20, ai=None, units=team2_units, boss=units['Pirate Tux'])

		self.units_manager = unit.UnitsManager([team1, team2])

		self.load_map(map_path)

		#pygame.mixer.set_reserved(2)
		self.overworld_music_ch = pygame.mixer.Channel(0)
		self.battle_music_ch = pygame.mixer.Channel(1)

		self.main_menu_music = pygame.mixer.Sound(os.path.join('music', 'Beyond The Clouds (Dungeon Plunder).ogg'))
		self.overworld_music = pygame.mixer.Sound(os.path.join('music', 'Ireland\'s Coast - Video Game.ogg'))
		self.battle_music = pygame.mixer.Sound(os.path.join('music', 'The Last Encounter Short Loop.ogg'))

		# load every .ogg file from sounds directory
		sounds_path = os.path.relpath('sounds')
		sounds_dir = os.listdir(sounds_path)
		sound_files = [ f for f in sounds_dir if os.path.isfile(os.path.join(sounds_path, f)) and f.endswith('.ogg')]
		# filename without extension : sound object
		self.sounds = { f[:-4] : pygame.mixer.Sound(os.path.relpath(os.path.join('sounds', f))) for f in sound_files}

		self.event_handler = EventHandler("Main")
		self.sidebar = Sidebar(self.screen, self.SMALL_FONT, self.units_manager)

		self.winner = None
		self.done = False
		self.resolution = self.screen.get_size()
		self.mode = pygame.RESIZABLE

	def load_map(self, map_path):
		if map_path is not None:
			self.map = map.Map(map_path, self.screen.get_size(), self.units_manager)
			self.event_handler.register(VIDEORESIZE, self.map.handle_videoresize)
			enemy_team = self.units_manager.teams[1]
			enemy_team.ai = ai.AI(self.map, self.units_manager, enemy_team, self.battle)
		else:
			self.map = None

	def play(self):
		while True:
			logging.debug(_('Main game loop started'))

			self.play_overworld_music()

			if self.units_manager.active_team.ai is None:
				self.enable_controls()

			while not self.done:
				if self.winner is not None:
					self.victory_screen()
					self.done = True
				else:
					self.check_turn()
					self.screen.fill(BLACK)
					self.blit_map()
					self.blit_info()
					self.blit_fps()
					pygame.display.flip()
					self.clock.tick(30)

				if callable(self.units_manager.active_team.ai):
					self.units_manager.active_team.ai()
				else:
					self.event_handler.wait([KEYDOWN, MOUSEBUTTONDOWN, MOUSEMOTION])

			logging.debug(_('Returning to main menu'))
			self.map = None
			self.winner = None
			self.done = False
			self.event_handler.reset()
			self.main_menu()

	def blit_map(self):
		"""
		This method renders and blits the map on the screen.
		"""
		self.map.draw(self.screen)

	def blit_info(self):
		coord = self.map.cursor.coord
		unit = self.map.get_unit(coord)
		terrain = self.map[coord]
		turn = self.units_manager.active_team
		self.sidebar.update(unit, terrain, coord, turn)

	def blit_fps(self):
		screen_w, screen_h = self.screen.get_size()
		fps = self.clock.get_fps()
		fpslabel = self.FPS_FONT.render(str(int(fps)) + ' FPS', True, WHITE)
		rec = fpslabel.get_rect(top=5, right=screen_w - 5)
		self.screen.blit(fpslabel, rec)

	def play_overworld_music(self):
		"""Start playing overworld music in a loop."""
		self.overworld_music_ch.play(self.overworld_music, -1)

	def show_license(self):
		event_handler = EventHandler("License")
		path = os.path.abspath('images/GNU GPL.jpg')
		gpl_image = pygame.image.load(path).convert()
		gpl_image = pygame.transform.smoothscale(gpl_image, self.screen.get_size())
		self.screen.blit(gpl_image, (0, 0))
		pygame.display.flip()
		event_handler.wait()

	def update_display(self):
		self.screen = pygame.display.set_mode(self.resolution, self.mode)

	def set_fullscreen(self, enable):
		if enable:
			self.mode = pygame.FULLSCREEN
		else:
			self.mode = pygame.RESIZABLE
		self.update_display()

	def post_interrupt(self, event=None):
		pygame.event.post(pygame.event.Event(self.INTERRUPTEVENT, {}))

	def set_resolution(self, res):
		self.resolution = res

	def resolution_setter(self, res):
		def set_res():
			self.set_resolution(res)
			self.update_display()
		return set_res

	def settings_menu(self):
		event_handler = EventHandler("Settings")
		logging.debug(_("Settings menu"))
		event_handler.bind_key(K_ESCAPE, self.post_interrupt)
		back_btn = gui.Button(_("Go Back"), self.MAIN_FONT, self.post_interrupt)
		back_btn.rect.bottomright = self.screen.get_size()
		fullscreen_btn = gui.CheckBox(_("Toggle Fullscreen"), self.MAIN_FONT, self.set_fullscreen)
		fullscreen_btn.rect.midtop = self.screen.get_rect(top=50).midtop
		resolutions = [("{0[0]}x{0[1]}".format(res), self.resolution_setter(res)) for res in pygame.display.list_modes()]
		resolutions_menu = gui.Menu(resolutions, self.MAIN_FONT)
		resolutions_menu.rect.midtop = self.screen.get_rect(top=100).midtop
		back_btn.register(event_handler)
		fullscreen_btn.register(event_handler)
		resolutions_menu.register(event_handler)
		event = pygame.event.Event(NOEVENT, {})
		while event.type != self.INTERRUPTEVENT:
			self.screen.fill(BLACK)
			back_btn.draw(self.screen)
			fullscreen_btn.draw(self.screen)
			resolutions_menu.draw(self.screen)
			self.blit_fps()
			pygame.display.flip()
			self.clock.tick(30)
			event = event_handler.wait(gui.Button.EVENT_TYPES + [self.INTERRUPTEVENT])

	def main_menu(self):
		self.main_menu_music.play()
		screen_rect = self.screen.get_rect()
		screen_w, screen_h = self.screen.get_size()

		self.screen.fill(BLACK)
		elinvention = self.MAIN_MENU_FONT.render("Elinvention", 1, WHITE)
		presents = self.MAIN_MENU_FONT.render(_("PRESENTS"), 1, WHITE)
		self.screen.blit(elinvention, utils.center(screen_rect, elinvention.get_rect()))
		self.screen.blit(presents, utils.center(screen_rect, presents.get_rect(), yoffset=self.MAIN_MENU_FONT.get_linesize()))
		pygame.display.flip()
		self.event_handler.wait(timeout=6000)

		path = os.path.abspath(os.path.join('images', 'Ice Emblem.png'))
		main_menu_image = ResizableImage(path, (screen_w, screen_h), (0, 0))
		self.event_handler.register(VIDEORESIZE, main_menu_image.resize)

		click_to_start = self.MAIN_MENU_FONT.render(_("Click to Start"), 1, ICE)
		hmenu = gui.HorizontalMenu([(_("License"), self.show_license), (_("Settings"), self.settings_menu)], self.SMALL_FONT)
		hmenu.rect.bottomright = self.screen.get_size()

		hmenu.register(self.event_handler)
		self.event_handler.bind_key(K_RETURN, self.post_interrupt)
		self.event_handler.bind_click(1, self.post_interrupt, hmenu.rect, False)

		event = pygame.event.Event(NOEVENT, {})
		while event.type != USEREVENT+2:
			self.screen.fill(BLACK)
			main_menu_image.rect.center = self.screen.get_rect().center
			main_menu_image.draw(self.screen)
			self.screen.blit(click_to_start, utils.center(self.screen.get_rect(), click_to_start.get_rect(), yoffset=200))
			hmenu.rect.bottomright = self.screen.get_size()
			hmenu.draw(self.screen)
			self.blit_fps()
			pygame.display.flip()
			self.clock.tick(30)
			event = self.event_handler.wait(hmenu.EVENT_TYPES + [self.INTERRUPTEVENT])

		self.event_handler.reset()
		self.screen.fill(BLACK)
		self.screen.blit(main_menu_image.image, (0, 0))

		self.map_menu(main_menu_image)

		pygame.mixer.fadeout(2000)
		self.fadeout(2000)
		pygame.mixer.stop() # Make sure mixer is not busy
		self.sidebar.start_time = pygame.time.get_ticks()

	def map_menu(self, main_menu_image):
		if self.map is not None:
			return
		event_handler = EventHandler("MapMenu")
		choose_label = self.MAIN_FONT.render(_("Choose a map!"), True, ICE, MENU_BG)
		maps_path = os.path.abspath('maps')
		files = [ (f, None) for f in os.listdir(maps_path) if os.path.isfile(os.path.join(maps_path, f)) and f.endswith('.tmx')]
		menu = gui.Menu(files, self.MAIN_FONT, None, (25, 25))
		menu.rect.center = (self.screen.get_width() // 2, self.screen.get_height() // 2)
		menu.register(event_handler)
		event_handler.register(VIDEORESIZE, main_menu_image.resize)

		while menu.choice is None:
			self.screen.fill(BLACK)
			main_menu_image.rect.center = self.screen.get_rect().center
			main_menu_image.draw(self.screen)
			self.screen.blit(choose_label, choose_label.get_rect(top=50, centerx=self.screen.get_rect().centerx))
			menu.rect.center = self.screen.get_rect().center
			menu.draw(self.screen)
			self.blit_fps()
			pygame.display.flip()
			event_handler.wait(gui.Menu.EVENT_TYPES)
			self.clock.tick(30)

		try:
			self.load_map(os.path.join('maps', files[menu.choice][0]))
		except:
			print("Error loading map! Wrong format. " + sys.exc_info()[0])
			self.map_menu(main_menu_image)

	def fadeout(self, fadeout_time, percent=0):
		start = pygame.time.get_ticks()
		fade = self.screen.copy()
		state_time = 0
		percent = (100 - percent) / 100.0

		while state_time < fadeout_time:
			alpha = int(255.0 - 255.0 * state_time / fadeout_time * percent)
			fade.set_alpha(alpha)
			self.screen.fill(BLACK)
			self.screen.blit(fade, (0, 0))
			pygame.display.flip()
			self.clock.tick(60)
			state_time = pygame.time.get_ticks() - start
			self.event_handler()

	def experience_animation(self, unit, bg):
		img_pos = utils.center(self.screen.get_rect(), unit.image.get_rect())
		exp_pos = (img_pos[0], img_pos[1] + unit.image.get_height() + 50)

		self.sounds['exp'].play(-1)

		gained_exp = unit.gained_exp()
		curr_exp = unit.prev_exp
		while curr_exp <= gained_exp + unit.prev_exp:
			if unit.levelled_up() and curr_exp == 100:
				self.sounds['levelup'].play()
			exp = pygame.Surface((curr_exp % 100, 20))
			exp.fill(YELLOW)

			exp_text = self.SMALL_FONT.render(_("EXP: %d") % (curr_exp % 100), True, YELLOW)
			lv_text = self.SMALL_FONT.render(_("LV: %d") % unit.lv, True, BLUE)

			self.screen.blit(bg, (0, 0))
			self.screen.blit(unit.image, img_pos)
			self.screen.blit(exp, exp_pos)
			self.screen.blit(exp_text, (exp_pos[0], exp_pos[1] + 25))
			self.screen.blit(lv_text, (exp_pos[0] + exp_text.get_width() + 10, exp_pos[1] + 25))

			curr_exp += 1
			pygame.display.flip()
			self.clock.tick(60)
			self.event_handler()

		self.sounds['exp'].stop()
		self.event_handler.wait(timeout=2000)

	def battle(self, attacking, defending):
		event_handler = EventHandler("Battle")
		attacking_team = self.units_manager.get_team(attacking.color)
		defending_team = self.units_manager.get_team(defending.color)

		att_weapon = attacking.get_active_weapon()
		def_weapon = defending.get_active_weapon()

		attacking.prepare_battle()
		defending.prepare_battle()

		dist = utils.distance(attacking.coord, defending.coord)
		at, dt = attacking.number_of_attacks(defending, dist)

		print("\r\n" + "#" * 12 + " Fight!!! " + "#" * 12)
		att_str = _("%s is going to attack %d %s")
		print(att_str % (attacking.name, at, _("time") if at == 1 else _("times")))
		print(att_str % (defending.name, dt, _("time") if dt == 1 else _("times")))

		self.overworld_music_ch.pause()  # Stop music and loop fight music
		self.battle_music_ch.play(self.battle_music, -1)

		self.blit_map()
		self.fadeout(1000, 10)  # Darker atmosphere

		battle_background = self.screen.copy()

		life_percent_background = pygame.Surface((100, 10))
		life_percent_background.fill(RED)
		life_percent_background.convert()

		att_swap = attacking
		def_swap = defending

		att_name = self.MAIN_FONT.render(attacking.name, 1, attacking_team.color)
		def_name = self.MAIN_FONT.render(defending.name, 1, defending_team.color)

		miss_text = self.SMALL_FONT.render(_("MISS"), 1, YELLOW).convert_alpha()
		null_text = self.SMALL_FONT.render(_("NULL"), 1, RED).convert_alpha()
		crit_text = self.SMALL_FONT.render(_("TRIPLE"), 1, RED).convert_alpha()
		screen_rect = self.screen.get_rect()

		att_rect_origin = attacking.image.get_rect(centerx=screen_rect.centerx-screen_rect.centerx//2, bottom=screen_rect.centery-25)
		def_rect_origin = defending.image.get_rect(centerx=screen_rect.centerx+screen_rect.centerx//2, bottom=screen_rect.centery-25)
		att_rect = att_rect_origin.copy()
		def_rect = def_rect_origin.copy()

		att_life_pos = (att_rect_origin.left, screen_rect.centery)
		def_life_pos = (def_rect_origin.left, screen_rect.centery)

		att_name_pos = (att_rect_origin.left, 30 + att_life_pos[1])
		def_name_pos = (def_rect_origin.left, 30 + def_life_pos[1])

		att_info_pos = (att_rect_origin.left, att_name_pos[1] + att_name.get_height() + 20)
		def_info_pos = (def_rect_origin.left, def_name_pos[1] + def_name.get_height() + 20)

		att_text_pos = (att_rect_origin.topright)
		def_text_pos = (def_rect_origin.topleft)

		life_block = pygame.Surface((4, 10))
		life_block_used = pygame.Surface((4, 10))
		life_block.fill(GREEN)
		life_block_used.fill(RED)

		collide = screen_rect.centerx, att_rect.bottom - 1
		broken = False
		for _round in range(at + dt + 1):
			animate_miss = False
			outcome = 0
			def_text = att_text = None
			if (at > 0 or dt > 0) and (def_swap.hp > 0 and att_swap.hp > 0):  # Se ci sono turni e se sono vivi
				print(" " * 6 + "-" * 6 + "Round:" + str(_round + 1) + "-" * 6)
			else:
				break
			at -= 1
			start_animation = pygame.time.get_ticks()
			animation_time = latest_tick = 0
			while animation_time < self.TIME_BETWEEN_ATTACKS:
				speed = int(100 / 250 * latest_tick)
				if att_swap == defending:
					speed = -speed
				if outcome == 0:
					att_rect = att_rect.move(speed, 0)
				if att_rect.collidepoint(collide) and outcome == 0:
					outcome = att_swap.attack(def_swap)
					if outcome == 1:  # Miss
						def_text = miss_text
						animate_miss = animation_time
						self.sounds['miss'].play()
					elif outcome == 2:  # Null attack
						def_text = null_text
						self.sounds['null'].play()
					elif outcome == 3:  # Triple hit
						att_text = crit_text
						self.sounds['critical'].play()
					elif outcome == 4:  # Hit
						self.sounds['hit'].play()

					att_rect = att_rect_origin.copy()
					def_rect = def_rect_origin.copy()
					miss_target = def_rect_origin.y - 50

				if animate_miss:
					t = (animation_time - animate_miss) / 1000
					def_rect.bottom = int(att_rect.bottom - 400 * t + 800 * t * t)
					if def_rect.bottom > att_rect.bottom:
						animate_miss = False
						def_rect.bottom = att_rect.bottom

				animation_time = pygame.time.get_ticks() - start_animation

				att_info = attacking.render_info(self.SMALL_FONT)
				def_info = defending.render_info(self.SMALL_FONT)

				self.screen.blit(battle_background, (0, 0))
				self.screen.blit(att_swap.image, att_rect.topleft)
				self.screen.blit(def_swap.image, def_rect.topleft)
				if att_text is not None:
					self.screen.blit(att_text, att_text_pos)
				if def_text is not None:
					self.screen.blit(def_text, def_text_pos)
				self.screen.blit(att_name, att_name_pos)
				self.screen.blit(def_name, def_name_pos)
				for i in range(attacking.hp_max):
					x = att_life_pos[0] + (i % 30 * 5)
					y = att_life_pos[1] + i // 30 * 11
					if i < attacking.hp:
						self.screen.blit(life_block, (x , y))
					else:
						self.screen.blit(life_block_used, (x , y))
				for i in range(defending.hp_max):
					x = def_life_pos[0] + (i % 30 * 5)
					y = def_life_pos[1] + i // 30 * 11
					if i < defending.hp:
						self.screen.blit(life_block, (x , y))
					else:
						self.screen.blit(life_block_used, (x , y))
				self.screen.blit(att_info, att_info_pos)
				self.screen.blit(def_info, def_info_pos)
				self.blit_fps()
				event_handler()
				pygame.display.flip()
				latest_tick = self.clock.tick(60)

			if dt > 0:
				att_swap, def_swap = def_swap, att_swap
				at, dt = dt, at
				att_rect, def_rect = def_rect, att_rect
				att_rect_origin, def_rect_origin = def_rect_origin, att_rect_origin
				att_text_pos, def_text_pos = def_text_pos, att_text_pos
		if attacking.hp > 0:
			attacking.experience(defending)
			self.experience_animation(attacking, battle_background)
		else:
			self.kill(attacking)

		if defending.hp > 0:
			defending.experience(attacking)
			self.experience_animation(defending, battle_background)
		else:
			self.kill(defending)

		if att_weapon and att_weapon.uses == 0:
			self.sounds['broke'].play()
			broken_text = self.SMALL_FONT.render("%s is broken" % att_weapon.name, True, RED)
			self.screen.blit(broken_text, utils.center(screen_rect, broken_text.get_rect()))
			pygame.display.flip()
			event_handler.wait(timeout=3000)
		if def_weapon and def_weapon.uses == 0:
			self.sounds['broke'].play()
			broken_text = self.SMALL_FONT.render("%s is broken" % def_weapon.name, True, RED)
			self.screen.blit(broken_text, utils.center(screen_rect, broken_text.get_rect()))
			pygame.display.flip()
			event_handler.wait(timeout=3000)

		self.battle_music_ch.fadeout(500)
		pygame.time.wait(500)
		self.battle_music_ch.stop()
		self.overworld_music_ch.unpause()
		self.screen.blit(battle_background, (0, 0))
		attacking.played = True

		if defending_team.is_defeated():
			self.winner = attacking_team
		elif attacking_team.is_defeated():
			self.winner = defending_team

		print("#" * 12 + " Battle ends " + "#" * 12 + "\r\n")

	def kill(self, unit):
		self.map.kill_unit(unit=unit)
		self.units_manager.kill_unit(unit)

	def disable_controls(self):
		self.event_handler.unregister(MOUSEBUTTONDOWN, self.handle_click)
		self.event_handler.unregister(MOUSEMOTION, self.handle_mouse_motion)
		self.event_handler.unregister(KEYDOWN, self.handle_keyboard)
		self.sidebar.endturn_btn.unregister(self.event_handler)

	def enable_controls(self):
		self.event_handler.register(MOUSEBUTTONDOWN, self.handle_click)
		self.event_handler.register(MOUSEMOTION, self.handle_mouse_motion)
		self.event_handler.register(KEYDOWN, self.handle_keyboard)
		self.sidebar.endturn_btn.register(self.event_handler)

	def switch_turn(self):
		active_team = self.units_manager.switch_turn()
		if active_team.ai is None:
			self.enable_controls()
		else:
			self.disable_controls()
		self.map.reset_selection()
		self.screen.fill(BLACK)
		self.blit_map()
		self.blit_info()
		phase_str = _('%s phase') % active_team.name
		phase = self.MAIN_MENU_FONT.render(phase_str, 1, active_team.color)
		self.screen.blit(phase, utils.center(self.screen.get_rect(), phase.get_rect()))
		pygame.display.flip()
		self.event_handler.wait(timeout=5000)

	def victory_screen(self):
		print(_("%s wins") % self.winner.name)
		pygame.mixer.stop()
		pygame.mixer.music.load(os.path.join('music', 'Victory Track.ogg'))
		pygame.mixer.music.play()
		self.fadeout(1000)

		victory = self.MAIN_MENU_FONT.render(self.winner.name + ' wins!', 1, self.winner.color)
		thank_you = self.MAIN_MENU_FONT.render(_('Thank you for playing Ice Emblem!'), 1, ICE)

		self.screen.fill(BLACK)
		self.screen.blit(victory, utils.center(self.screen.get_rect(), victory.get_rect(), yoffset=-50))
		self.screen.blit(thank_you, utils.center(self.screen.get_rect(), thank_you.get_rect(), yoffset=50))

		pygame.display.flip()

		pygame.event.clear()
		self.event_handler.wait()
		pygame.mixer.fadeout(2000)
		self.fadeout(2000)
		pygame.mixer.stop()

	def get_mouse_coord(self, pos=None):
		if pos is None:
			pos = pygame.mouse.get_pos()
		try:
			return self.map.mouse2cell(pos)
		except ValueError:
			return None

	def action_menu(self, actions, rollback, pos):
		event_handler = EventHandler("ActionMenu")

		menu = gui.Menu(actions, self.SMALL_FONT, rollback, (5, 10), pos)
		menu.register(event_handler)

		self.blit_map()

		action = None
		while action is None:
			menu.draw(self.screen)
			pygame.display.flip()
			event_handler.wait(gui.Menu.EVENT_TYPES)
			action = menu.choice
		return action

	def battle_wrapper(self, coord):
		defending = self.map.get_unit(coord)
		attacking = self.map.get_unit(self.map.curr_sel)

		# enemy chosen by the user... let the battle begin!
		self.battle(attacking, defending)

		self.map.reset_selection()

	def __attack_mousebuttondown(self, event):
		# user must click on an enemy unit
		if event.button == 1 and self.map.is_attack_click(event.pos):
			self.event_handler = EventHandler("Main")
			self.enable_controls()
			self.battle_wrapper(self.get_mouse_coord())
		elif event.button == 3:
			self.__attack_abort()

	def __attack_keydown(self, event):
		# user must choose an enemy unit
		if event.key == pygame.K_SPACE and self.map.is_enemy_cursor():
			self.event_handler = EventHandler("Main")
			self.enable_controls()
			self.battle_wrapper(self.map.cursor.coord)
		elif event.key == pygame.K_ESCAPE:
			self.__attack_abort()
		self.map.cursor.update(event)

	def __attack_abort(self):
		self.event_handler = EventHandler("Main")
		self.enable_controls()
		self.map.move(self.map.get_unit(self.map.curr_sel), self.map.prev_sel)
		self.map.reset_selection()

	def reset(self):
		pygame.mixer.fadeout(1000)
		self.fadeout(1000)
		self.done = True

	def pause_menu(self):
		event_handler = EventHandler("PauseMenu")
		menu_entries = [('Return to Game', None), ('Return to Main Menu', self.reset), ('Return to O.S.', utils.return_to_os)]
		menu = gui.Menu(menu_entries, self.MAIN_FONT)
		menu.rect.center = self.screen.get_rect().center

		menu.register(event_handler)

		while menu.choice is None:
			menu.draw(self.screen)
			pygame.display.flip()
			event_handler.wait(gui.Menu.EVENT_TYPES)

	def check_turn(self):
		if self.units_manager.active_team.is_turn_over():
			self.switch_turn()

	def handle_mouse_motion(self, event):
		self.map.handle_mouse_motion(event)

	def action_menu_wrapper(self, menu_entries, pos):
		# Check if have to display action menu
		if menu_entries is not None and len(menu_entries) > 0:
			# rollback will be called if the user aborts the
			# action menu by right clicking
			rollback = self.map.rollback_callback
			action = self.action_menu(menu_entries, rollback, pos)

			if action == 0 and menu_entries[0][0] is _("Attack"):
				# user choose to attack.
				# Now he has to choose the enemy to attack
				# so the next click must be an enemy unit
				self.event_handler = EventHandler("Attack")
				self.event_handler.register(MOUSEBUTTONDOWN, self.__attack_mousebuttondown)
				self.event_handler.register(KEYDOWN, self.__attack_keydown)
				self.event_handler.register(MOUSEMOTION, self.map.cursor.update)

	def handle_click(self, event):
		menu_entries = self.map.handle_click(event)
		self.action_menu_wrapper(menu_entries, event.pos)

	def handle_keyboard(self, event):
		if event.key == pygame.K_ESCAPE:
			self.pause_menu()
		else:
			menu_entries = self.map.handle_keyboard(event)
			pos = self.map.tilemap.pixel_at(*self.map.cursor.coord)
			pos = (pos[0] + self.map.tilemap.tile_width, pos[1] + self.map.tilemap.tile_height)

			self.action_menu_wrapper(menu_entries, pos)
