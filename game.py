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

from item import Item, Weapon
from map import Map
from unit import Unit, Player
from menu import Menu
from colors import *
from utils import *


class EventHandler(object):
	"""
	This class should provide a uniform and comfortable way to handle
	events.
	"""

	def __init__(self):
		self.handler = {pygame.QUIT: [return_to_os]}

	def __call__(self):
		"""
		Process new events
		"""
		processed = []
		for event in pygame.event.get():
			if event.type in self.handler:
				ret = self.handler[event.type][0](event)
				processed.append((event.type, ret))
		return processed

	def wait(self, event_types=[MOUSEBUTTONDOWN, KEYDOWN], timeout=-1):
		"""
		if the timeout argument is positive, returns after the specified
		number of milliseconds.
		"""

		event_types.append(QUIT)

		if timeout > 0:
			pygame.time.set_timer(USEREVENT+1, timeout)
			event_types.append(USEREVENT+1)

		pygame.event.set_allowed(None)  # only allow specified events
		pygame.event.set_allowed(event_types)

		event = pygame.event.wait()

		ret = None
		if event.type in self.handler:
			ret = self.handler[event.type][0](event)

		# workaround to re-enable all events except SYSWMEVENT
		pygame.event.set_allowed(list(range(NOEVENT, NUMEVENTS)))
		pygame.event.set_blocked(SYSWMEVENT)

		pygame.time.set_timer(USEREVENT+1, 0)

		return (event, ret)

	def register(self, event_type, callback):
		"""
		Bind a callback function to a specified event type.
		"""
		if event_type in self.handler:
			self.handler[event_type].insert(0, callback)
		else:
			self.handler[event_type] = [callback]
		logging.debug(_('%s registered') % pygame.event.event_name(event_type))

	def unregister(self, event_type, callback=None):
		for key in list(self.handler):  # iterate over a copy of the dictionary's keys
			if key == event_type:
				if callback is not None:
					self.handler[key].remove(callback)
				else:
					self.handler[key].pop(0)
				if len(self.handler[key]) == 0:
					del self.handler[key]  # to allow dictionary modification
				logging.debug(_('%s unregistered') % pygame.event.event_name(event_type))

	def register_menu(self, menu):
		self.register(MOUSEMOTION, menu.handle_mouse_motion)
		self.register(MOUSEBUTTONDOWN, menu.handle_click)
		self.register(KEYDOWN, menu.handle_keydown)
		logging.debug(_('Registered Menu'))

	def unregister_menu(self, menu):
		self.unregister(MOUSEMOTION, menu.handle_mouse_motion)
		self.unregister(MOUSEBUTTONDOWN, menu.handle_click)
		self.unregister(KEYDOWN, menu.handle_keydown)
		logging.debug(_('Unregistered Menu'))

	def reset(self):
		self.handler = {pygame.QUIT: [return_to_os]}


class Sidebar(object):
	BG = (100, 100, 100)
	def __init__(self, screen_size, font):
		self.screen_resize(screen_size)
		self.start_time = pygame.time.get_ticks()
		self.font = font

	def update(self, unit, terrain, coord, player):
		self.surface.fill(self.BG)

		turn_s = self.font.render(_('%s phase') % player.name, True, player.color)
		pos = turn_s.get_rect(top=40, left=5)
		self.surface.blit(turn_s, pos)

		if terrain is not None:
			t_name = self.font.render(terrain.name, True, WHITE)
			t_def = self.font.render(_("Def: %d") % terrain.defense, True, WHITE)
			t_avoid = self.font.render(_("Avoid: %d") % terrain.avoid, True, WHITE)
			t_allowed = self.font.render(_("Allowed: %s") % terrain.allowed, True, WHITE)
			pos = t_name.get_rect(top=pos.y + 40, left=5)
			self.surface.blit(t_name, pos)
			pos.left += pos.w + 5
			self.surface.blit(terrain.surface, pos)
			pos = t_def.get_rect(top=pos.y + 40, left=5)
			self.surface.blit(t_def, pos)
			pos = t_avoid.get_rect(top=pos.y + 40, left=5)
			self.surface.blit(t_avoid, pos)
			pos = t_allowed.get_rect(top=pos.y + 40, left=5)
			self.surface.blit(t_allowed, pos)

		if unit is not None:
			unit_name = self.font.render(unit.name, True, unit.color)
		else:
			unit_name = self.font.render(_("No units"), True, WHITE)
		pos = unit_name.get_rect(top=pos.y + 40, left=5)
		self.surface.blit(unit_name, pos)

		cell_label = self.font.render('X: %d Y: %d' % coord, True, WHITE)
		pos = cell_label.get_rect(top=pos.y + 40, left=5)
		self.surface.blit(cell_label, pos)

		time = pygame.time.get_ticks() - self.start_time
		time //= 1000
		sec = time % 60
		minutes = time / 60 % 60
		hours = time / 3600 % 24
		time_s = self.font.render("%02d:%02d:%02d" % (hours, minutes, sec), True, WHITE)
		pos = time_s.get_rect(top=pos.y + 40, left=5)
		self.surface.blit(time_s, pos)

	def screen_resize(self, screen_size):
		pos = (screen_size[0] - 200, 0)
		size = (200, screen_size[1])
		self.rect = pygame.Rect(pos, size)
		self.surface = pygame.Surface(size).convert()
		self.surface.fill(self.BG)


class Game(object):
	TIME_BETWEEN_ATTACKS = 2000  # Time to wait between each attack animation

	def __init__(self, screen, units, players, map_path, music, colors):
		self.screen = screen
		self.clock = pygame.time.Clock()

		font_path = os.path.abspath('fonts/Medieval Sharp/MedievalSharp.ttf')
		self.MAIN_MENU_FONT = pygame.font.Font(font_path, 48)
		self.MAIN_FONT = pygame.font.Font(font_path, 36)
		self.SMALL_FONT = pygame.font.Font(font_path, 24)
		self.FPS_FONT = pygame.font.SysFont("Liberation Sans", 12)

		self.players = players
		self.active_player = self.get_active_player()
		self.units = units
		self.colors = colors

		self.load_map(map_path)

		#pygame.mixer.set_reserved(2)
		self.overworld_music_ch = pygame.mixer.Channel(0)
		self.battle_music_ch = pygame.mixer.Channel(1)

		self.main_menu_music = pygame.mixer.Sound(os.path.abspath(music['menu']))
		self.overworld_music = pygame.mixer.Sound(os.path.abspath(music['overworld']))
		self.battle_music = pygame.mixer.Sound(os.path.abspath(music['battle']))

		# load every .ogg file from sounds directory
		sounds_path = os.path.relpath('sounds')
		sounds_dir = os.listdir(sounds_path)
		sound_files = [ f for f in sounds_dir if os.path.isfile(os.path.join(sounds_path, f)) and f.endswith('.ogg')]
		# filename without extension : sound object
		self.sounds = { f[:-4] : pygame.mixer.Sound(os.path.relpath(os.path.join('sounds', f))) for f in sound_files}

		self.sidebar = Sidebar(self.screen.get_size(), self.SMALL_FONT)
		self.event_handler = EventHandler()

		self.winner = None
		self.done = False

	def load_map(self, map_path):
		if map_path is not None:
			self.map = Map(map_path, self.screen.get_size(), self.colors, self.units)

			# discard unused units
			map_units = { sprite.unit.name: self.units[sprite.unit.name] for sprite in self.map.sprites }
			for player in self.players:
				player.units = [ u for u in player.units if u in map_units.values() ]
		else:
			self.map = None

	def play(self):
		while True:
			logging.debug(_('Main game loop started'))
			self.event_handler.register(MOUSEBUTTONDOWN, self.handle_click)
			self.event_handler.register(MOUSEMOTION, self.handle_mouse_motion)
			self.event_handler.register(KEYDOWN, self.handle_keyboard)
			self.event_handler.register(VIDEORESIZE, self.screen_resize)
			
			self.play_overworld_music()

			while not self.done:
				self.event_handler()

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
					self.clock.tick(25)

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
		self.screen.blit(self.map.render(), (0, 0))

	def blit_info(self):
		coord = self.map.cursor.coord
		unit = self.map.get_unit(*coord)
		terrain = self.map.get_terrain(*coord)
		turn = self.whose_turn()
		self.sidebar.update(unit, terrain, coord, turn)
		self.screen.blit(self.sidebar.surface, self.sidebar.rect)

	def blit_fps(self):
		screen_w, screen_h = self.screen.get_size()
		fps = self.clock.get_fps()
		fpslabel = self.FPS_FONT.render(str(int(fps)) + ' FPS', True, WHITE)
		rec = fpslabel.get_rect(top=5, right=screen_w - 5)
		self.screen.blit(fpslabel, rec)

	def screen_resize(self, event):
		"""
		This method takes care to resize and scale everithing to match
		the new window's size. The minum window size is 800x600.
		On Debian Jessie there is an issue that makes the window kind of
		"rebel" while trying to resize it.
		"""
		screen_size = event.size
		if screen_size[0] < 800:
			screen_size = (800, screen_size[1])
		if screen_size[1] < 600:
			screen_size = (screen_size[0], 600)
		self.screen = pygame.display.set_mode(screen_size, pygame.RESIZABLE)
		self.map.screen_resize(screen_size)
		self.sidebar.screen_resize(screen_size)

	def play_overworld_music(self):
		"""Start playing overworld music in a loop."""
		self.overworld_music_ch.play(self.overworld_music, -1)

	def main_menu(self):
		self.main_menu_music.play()
		screen_rect = self.screen.get_rect()
		screen_w, screen_h = self.screen.get_size()

		self.screen.fill(BLACK)

		elinvention = self.MAIN_MENU_FONT.render("Elinvention", 1, WHITE)
		presents = self.MAIN_MENU_FONT.render(_("PRESENTS"), 1, WHITE)

		self.screen.blit(elinvention, center(screen_rect, elinvention.get_rect()))

		self.screen.blit(presents, center(screen_rect, presents.get_rect(), yoffset=self.MAIN_MENU_FONT.get_linesize()))

		pygame.display.flip()

		self.event_handler.wait(timeout=6000)


		path = os.path.abspath('images/Ice Emblem.png')
		main_menu_image = pygame.image.load(path).convert_alpha()
		main_menu_image = pygame.transform.smoothscale(main_menu_image, (screen_w, screen_h))

		click_to_start = self.MAIN_MENU_FONT.render(_("Click to Start"), 1, ICE)
		click_license = self.SMALL_FONT.render(_("License"), 1, WHITE)

		self.screen.blit(main_menu_image, (0, 0))
		self.screen.blit(click_to_start, center(screen_rect, click_to_start.get_rect(), yoffset=200))
		license_w, license_h = click_license.get_size()
		self.screen.blit(click_license, (screen_w - license_w, screen_h - license_h))

		pygame.display.flip()

		click_x, click_y = self.event_handler.wait([MOUSEBUTTONDOWN])[0].pos

		if click_x > screen_w - license_w and click_y > screen_h - license_h:
			path = os.path.abspath('images/GNU GPL.jpg')
			gpl_image = pygame.image.load(path).convert()
			gpl_image = pygame.transform.smoothscale(gpl_image, (screen_rect.w, screen_rect.h))
			self.screen.blit(gpl_image, (0, 0))
			pygame.display.flip()
			self.event_handler.wait()

		if self.map is None:
			choose_label = self.MAIN_FONT.render(_("Choose a map!"), True, ICE, BACKGROUND)
			self.screen.blit(choose_label, choose_label.get_rect(top=50, centerx=self.screen.get_width() // 2))
			
			maps_path = os.path.abspath('maps')
			files = [ (f, None) for f in os.listdir(maps_path) if os.path.isfile(os.path.join(maps_path, f)) and f.endswith('.tmx')]

			menu = Menu(files, self.MAIN_FONT, None, (25, 25))
			menu.rect.center = (self.screen.get_width() // 2, self.screen.get_height() // 2)
			self.event_handler.register_menu(menu)

			while menu.choice is None:
				self.screen.blit(menu.render(), menu.rect.topleft)
				pygame.display.flip()
				self.event_handler.wait(Menu.EVENT_TYPES)

			self.event_handler.unregister_menu(menu)

			self.load_map(os.path.join('maps', files[menu.choice][0]))

		pygame.mixer.fadeout(2000)
		self.fadeout(2000)
		pygame.mixer.stop() # Make sure mixer is not busy
		self.sidebar.start_time = pygame.time.get_ticks()


	def whose_unit(self, unit):
		for player in self.players:
			for player_unit in player.units:
				if player_unit == unit:
					return player
		return None

	def whose_turn(self):
		for player in self.players:
			if player.my_turn:
				return player
		return None

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
			self.check_quit_event()

	def check_quit_event(self):
		for event in pygame.event.get(pygame.QUIT):
			if event.type == pygame.QUIT:  # If user clicked close
				return_to_os()

	def experience_animation(self, unit, bg):
		img_pos = center(self.screen.get_rect(), unit.image.get_rect())
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
			self.check_quit_event()

		self.sounds['exp'].stop()
		self.event_handler.wait(timeout=2000)

	def battle(self, attacking, defending, dist):
		attacking_player = self.whose_unit(attacking)
		defending_player = self.whose_unit(defending)

		attacking.prepare_battle()
		defending.prepare_battle()

		at, dt = attacking.number_of_attacks(defending, dist)

		print("\r\n" + "#" * 12 + " Fight!!! " + "#" * 12)
		att_str = _("%s is going to attack %d %s")
		print(att_str % (attacking.name, at, _("time") if at == 1 else _("times")))
		print(att_str % (defending.name, dt, _("time") if dt == 1 else _("times")))

		self.overworld_music_ch.pause()  # Stop music and loop fight music
		self.battle_music_ch.play(self.battle_music, -1)

		latest_attack = start = pygame.time.get_ticks()

		self.fadeout(1000, 10)  # Darker atmosphere

		battle_background = self.screen.copy()

		animation_duration = self.TIME_BETWEEN_ATTACKS * (at + dt + 1)

		att_swap = attacking
		def_swap = defending

		life_percent_background = pygame.Surface((100, 10))
		life_percent_background.fill(RED)
		life_percent_background.convert()

		att_life_pos = (100, 120 + attacking.image.get_height())
		def_life_pos = (400, 120 + defending.image.get_height())

		att_name = self.MAIN_FONT.render(attacking.name, 1, attacking_player.color)
		def_name = self.MAIN_FONT.render(defending.name, 1, defending_player.color)
		att_name_pos = (100, 30 + att_life_pos[1])
		def_name_pos = (400, 30 + def_life_pos[1])

		att_info_pos = (100, att_name_pos[1] + att_name.get_height() + 20)
		def_info_pos = (400, def_name_pos[1] + def_name.get_height() + 20)

		att_image_pos = ATT_IMAGE_POS = (100, 100)
		def_image_pos = DEF_IMAGE_POS = (400, 100)

		animate_attack = True
		animate_miss = False
		latest_tick = 0

		time_since_anim_start = pygame.time.get_ticks() - start
		time_since_latest_attack = pygame.time.get_ticks() - latest_attack

		missed_text = self.SMALL_FONT.render(_("MISSED"), 1, YELLOW).convert_alpha()
		void_text = self.SMALL_FONT.render(_("VOID ATTACK"), 1, BLUE).convert_alpha()
		ATT_TEXT_POS = (200, 100)
		DEF_TEXT_POS = (300, 100)

		while time_since_anim_start < animation_duration:
			def_text = att_text = None
			if at > 0 or dt > 0:
				if def_swap.hp == 0 or att_swap.hp == 0:
					at = dt = 0
					animation_duration = time_since_anim_start + self.TIME_BETWEEN_ATTACKS

				elif time_since_latest_attack > self.TIME_BETWEEN_ATTACKS:
					if animate_attack:
						speed = int(100 / 250 * latest_tick)
						if att_swap == attacking:
							att_image_pos = (att_image_pos[0] + speed, 100)
							#print(attacking.name + str(att_image_pos))
							if att_image_pos[0] >= 200:
								self.sounds['hit'].play()
								att_image_pos = ATT_IMAGE_POS
								animate_attack = False
						else:
							def_image_pos = (def_image_pos[0] - speed, 100)
							#print(defending.name + str(def_image_pos))
							if def_image_pos[0] <= 300:
								self.sounds['hit'].play()
								def_image_pos = DEF_IMAGE_POS
								animate_attack = False
					elif animate_miss:
						speed = int(50 / 250 * latest_tick)
						if att_swap == defending:
							def_text = missed_text
							att_image_pos = (att_image_pos[0], att_image_pos[1] - speed)
							#print(attacking.name + str(att_image_pos))
							if att_image_pos[1] <= 50:
								att_image_pos = ATT_IMAGE_POS
								animate_miss = False
						else:
							att_text = missed_text
							def_image_pos = (def_image_pos[0], def_image_pos[1] - speed)
							#print(defending.name + str(def_image_pos))
							if def_image_pos[1] <= 50:
								def_image_pos = DEF_IMAGE_POS
								animate_miss = False
						if not animate_miss:
							latest_attack = pygame.time.get_ticks()
							at -= 1

							if dt > 0:
								att_swap, def_swap = def_swap, att_swap
								at, dt = dt, at
							animate_attack = True
					else:
						outcome = att_swap.attack(def_swap)

						if outcome == 0:  # Missed
							animate_miss = True
						elif outcome == 1:
							latest_attack = pygame.time.get_ticks()
							at -= 1

							if dt > 0:
								att_swap, def_swap = def_swap, att_swap
								at, dt = dt, at

							animate_attack = True

			att_life_percent = pygame.Surface((attacking.life_percent(), 10))
			att_life_percent.fill(GREEN)
			def_life_percent = pygame.Surface((defending.life_percent(), 10))
			def_life_percent.fill(GREEN)
			att_info = attacking.render_info(self.SMALL_FONT)
			def_info = defending.render_info(self.SMALL_FONT)

			self.screen.blit(battle_background, (0, 0))
			if att_text is not None:
				self.screen.blit(att_text, DEF_TEXT_POS)
			if def_text is not None:
				self.screen.blit(def_text, ATT_TEXT_POS)
			self.screen.blit(attacking.image, att_image_pos)
			self.screen.blit(defending.image, def_image_pos)
			self.screen.blit(att_name, att_name_pos)
			self.screen.blit(def_name, def_name_pos)
			self.screen.blit(life_percent_background, att_life_pos)
			self.screen.blit(life_percent_background, def_life_pos)
			self.screen.blit(att_life_percent, att_life_pos)
			self.screen.blit(def_life_percent, def_life_pos)
			self.screen.blit(att_info, att_info_pos)
			self.screen.blit(def_info, def_info_pos)
			self.blit_fps()
			self.check_quit_event()
			pygame.display.flip()

			latest_tick = self.clock.tick(60)

			time_since_anim_start = pygame.time.get_ticks() - start
			time_since_latest_attack = pygame.time.get_ticks() - latest_attack

		if attacking.hp > 0:
			attacking.experience(defending)
			self.experience_animation(attacking, battle_background)

		if defending.hp > 0:
			defending.experience(attacking)
			self.experience_animation(defending, battle_background)

		self.battle_music_ch.fadeout(500)
		pygame.time.wait(500)
		self.overworld_music_ch.unpause()
		attacking.played = True

		if defending.hp == 0:
			self.kill(defending)
		elif attacking.hp == 0:
			self.kill(attacking)

		if defending_player.is_defeated():
			self.winner = attacking_player
		elif attacking_player.is_defeated():
			self.winner = defending_player

		print("#" * 12 + " Battle ends " + "#" * 12 + "\r\n")

	def kill(self, unit):
		self.map.kill_unit(unit)
		self.whose_unit(unit).units.remove(unit)

	def get_active_player(self):
		for player in self.players:
			if player.my_turn:
				return player
		return None

	def switch_turn(self):
		for i, player in enumerate(self.players):
			if player.my_turn:
				player.end_turn()
				active_player_index = (i + 1) % len(self.players)
				self.active_player = self.players[active_player_index]
				self.active_player.begin_turn()
				break
		self.map.reset_selection()
		self.blit_map()
		self.blit_info()
		phase_str = self.active_player.name + ' phase'
		phase = self.MAIN_MENU_FONT.render(phase_str, 1, self.active_player.color)
		self.screen.blit(phase, center(self.screen.get_rect(), phase.get_rect()))
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
		self.screen.blit(victory, center(self.screen.get_rect(), victory.get_rect(), yoffset=-50))
		self.screen.blit(thank_you, center(self.screen.get_rect(), thank_you.get_rect(), yoffset=50))

		pygame.display.flip()

		pygame.event.clear()
		self.event_handler.wait()

	def get_mouse_coord(self, pos=None):
		if pos is None:
			pos = pygame.mouse.get_pos()
		try:
			return self.map.mouse2cell(pos)
		except ValueError:
			return None

	def action_menu(self, actions, rollback, pos):
		self.blit_map()

		menu = Menu(actions, self.SMALL_FONT, rollback, (5, 10), pos)
		self.event_handler.register_menu(menu)

		action = None

		while action is None:
			self.screen.blit(menu.render(), menu.rect.topleft)
			pygame.display.flip()
			self.event_handler.wait(Menu.EVENT_TYPES)
			action = menu.choice

		self.event_handler.unregister_menu(menu)

		return action

	def battle_wrapper(self, coord):
		defending = self.map.get_unit(*coord)
		attacking = self.map.get_unit(*self.map.curr_sel)

		# enemy chosen by the user... let the battle begin!
		self.battle(attacking, defending, distance(coord, self.map.curr_sel))

		att_sprite = self.map.find_sprite(attacking)
		if att_sprite is not None:
			att_sprite.update()
		def_sprite = self.map.find_sprite(defending)
		if def_sprite is not None:
			def_sprite.update()

		self.map.reset_selection()

	def __attack_mousebuttondown(self, event):
		# user must click on an enemy unit
		if event.button == 1 and self.map.is_attack_click(event.pos):
			self.event_handler.unregister(KEYDOWN, self.__attack_keydown)
			self.event_handler.unregister(MOUSEBUTTONDOWN, self.__attack_mousebuttondown)
			self.battle_wrapper(self.get_mouse_coord())
		elif event.button == 3:
			self.__attack_abort()

	def __attack_keydown(self, event):
		# user must choose an enemy unit
		if event.key == pygame.K_SPACE and self.map.is_enemy_cursor():
			self.event_handler.unregister(KEYDOWN, self.__attack_keydown)
			self.event_handler.unregister(MOUSEBUTTONDOWN, self.__attack_mousebuttondown)
			self.battle_wrapper(self.map.cursor.coord)
		elif event.key == pygame.K_ESCAPE:
			self.__attack_abort()
		self.map.cursor.update(event)

	def __attack_abort(self):
		self.event_handler.unregister(KEYDOWN, self.__attack_keydown)
		self.event_handler.unregister(MOUSEBUTTONDOWN, self.__attack_mousebuttondown)
		self.map.move(self.map.curr_sel, self.map.prev_sel)
		self.map.reset_selection()

	def reset(self):
		pygame.mixer.fadeout(1000)
		self.fadeout(1000)
		self.done = True

	def pause_menu(self):
		menu_entries = [('Return to Game', None), ('Return to Main Menu', self.reset), ('Return to O.S.', return_to_os)]
		menu = Menu(menu_entries, self.MAIN_FONT)
		menu.rect.center = self.screen.get_rect().center

		self.event_handler.register_menu(menu)

		while menu.choice is None:
			self.screen.blit(menu.render(), menu.rect.topleft)
			pygame.display.flip()
			self.event_handler.wait(Menu.EVENT_TYPES)

		self.event_handler.unregister_menu(menu)

	def check_turn(self):
		if self.active_player.is_turn_over():
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
				self.event_handler.register(MOUSEBUTTONDOWN, self.__attack_mousebuttondown)
				self.event_handler.register(KEYDOWN, self.__attack_keydown)

	def handle_click(self, event):
		menu_entries = self.map.handle_click(event, self.active_player)
		pos = pygame.mouse.get_pos()
		self.action_menu_wrapper(menu_entries, pos)

	def handle_keyboard(self, event):
		if event.key == pygame.K_ESCAPE:
			self.pause_menu()
		else:
			menu_entries = self.map.handle_keyboard(event, self.active_player)
			pos = self.map.tilemap.pixel_at(*self.map.cursor.coord)
			pos = (pos[0] + self.map.tilemap.tile_width, pos[1] + self.map.tilemap.tile_height)

			self.action_menu_wrapper(menu_entries, pos)
