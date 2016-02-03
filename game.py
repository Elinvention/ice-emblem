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
import os
import logging
import traceback
import random

import resources
import sounds
import events
import map
import gui
import utils
import ai
from colors import *


class Sidebar(object):
	def __init__(self, screen, font, switch_turn):
		self.screen = screen
		self.rect = pygame.Rect((screen.get_width() - 250, 0), (250, screen.get_height()))
		self.start_time = pygame.time.get_ticks()
		self.font = font
		self.endturn_btn = gui.Button(_("End Turn"), self.font, switch_turn)

	def update(self, unit, terrain, coord, team):
		render = lambda x, y: self.font.render(x, True, y)
		self.rect.h = self.screen.get_height()
		self.rect.x = self.screen.get_width() - self.rect.w
		self.endturn_btn.rect.bottomright = self.rect.bottomright

		sidebar = pygame.Surface(self.rect.size)
		sidebar.fill((100, 100, 100))

		turn_s = render(_('%s phase') % team.name, team.color)
		pos = turn_s.get_rect(top=40, left=10)
		sidebar.blit(turn_s, pos)

		t_info = [
			render(terrain.name, WHITE),
			render(_("Def: %d") % terrain.defense, WHITE),
			render(_("Avoid: %d") % terrain.avoid, WHITE),
			render(_("Allowed: %s") % (", ".join(terrain.allowed)), WHITE),
		] if terrain else []

		weapon = unit.get_active_weapon() if unit else None
		weapon_name = weapon.name if weapon else _("No Weapon")
		u_info = [
			render(unit.name, unit.color),
			render(weapon_name, WHITE),
		] if unit else [render(_("No unit"), WHITE)]

		delta = (pygame.time.get_ticks() - self.start_time) // 1000
		hours, remainder = divmod(delta, 3600)
		minutes, seconds = divmod(remainder, 60)

		global_info = [
			render('X: %d Y: %d' % coord, WHITE),
			render('%02d:%02d:%02d' % (hours, minutes, seconds), WHITE),
		]

		out = t_info + u_info + global_info

		for i in out:
			pos.move_ip(0, 40)
			sidebar.blit(i, pos)

		self.screen.blit(sidebar, self.rect)
		self.endturn_btn.draw(self.screen)


class ResizableImage(object):
	def __init__(self, fname, size, pos, keep_ratio=True, smooth=True):
		self.original_image = resources.load_image(fname).convert_alpha()
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
	CLOCKEVENT = USEREVENT + 3

	def __init__(self, screen, map_path):
		self.screen = screen
		self.clock = pygame.time.Clock()

		font_name = os.path.join('Medieval Sharp', 'MedievalSharp.ttf')
		self.MAIN_MENU_FONT = resources.load_font(font_name, 48)
		self.MAIN_FONT = resources.load_font(font_name, 36)
		self.SMALL_FONT = resources.load_font(font_name, 24)
		self.FPS_FONT = pygame.font.SysFont("Liberation Sans", 12)

		sounds.get('cursor').set_volume(0.1)

		self.winner = None
		self.done = False
		self.resolution = self.screen.get_size()
		self.mode = pygame.RESIZABLE

		self.load_map(map_path)

	def load_map(self, map_path):
		if map_path is not None:
			self.map = map.Map(map_path, self.screen.get_size())
			self.units_manager = self.map.units_manager
			for team in self.units_manager.teams:
				if team.ai:
					team.ai = ai.AI(self.map, self.units_manager, team, self.battle)
			events.register(VIDEORESIZE, self.map.handle_videoresize)
		else:
			self.map = None
			self.units_manager = None

	def play(self):
		while True:
			logging.debug(_('Main game loop started'))

			self.units_manager.active_team.play_music('map')
			self.sidebar = Sidebar(self.screen, self.SMALL_FONT, self.switch_turn)

			if not self.units_manager.active_team.ai:
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
				elif self.map.move_x != 0 or self.map.move_y != 0:
					events.pump()
				else:
					# we want to wait but update the clock!
					time = pygame.time.get_ticks() - self.sidebar.start_time
					pygame.time.set_timer(self.CLOCKEVENT, (1000 - time % 1000))
					event = events.wait([KEYDOWN, MOUSEBUTTONDOWN, MOUSEMOTION, self.CLOCKEVENT])
					if event.type != self.CLOCKEVENT:
						# something happened before CLOCKEVENT so we don't want it anymore
						pygame.time.set_timer(self.CLOCKEVENT, 0)

			logging.debug(_('Returning to main menu'))
			self.map = None
			self.winner = None
			self.done = False
			self.sidebar = None
			self.units_manager = None
			events.new_context()
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

	def show_license(self):
		events.new_context("License")
		gpl_image = resources.load_image('GNU GPL.jpg')
		gpl_image = pygame.transform.smoothscale(gpl_image, self.screen.get_size())
		self.screen.blit(gpl_image, (0, 0))
		pygame.display.flip()
		events.wait(context="License")

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
		events.new_context("Settings")
		logging.debug(_("Settings menu"))
		events.bind_keys((K_ESCAPE,), self.post_interrupt, "Settings")
		back_btn = gui.Button(_("Go Back"), self.MAIN_FONT, self.post_interrupt)
		back_btn.rect.bottomright = self.screen.get_size()
		fullscreen_btn = gui.CheckBox(_("Toggle Fullscreen"), self.MAIN_FONT, self.set_fullscreen)
		fullscreen_btn.rect.midtop = self.screen.get_rect(top=50).midtop
		resolutions = [("{0[0]}x{0[1]}".format(res), self.resolution_setter(res)) for res in pygame.display.list_modes()]
		resolutions_menu = gui.Menu(resolutions, self.MAIN_FONT)
		resolutions_menu.rect.midtop = self.screen.get_rect(top=100).midtop
		back_btn.register("Settings")
		fullscreen_btn.register("Settings")
		resolutions_menu.register("Settings")
		event = pygame.event.Event(NOEVENT, {})
		while event.type != self.INTERRUPTEVENT:
			self.screen.fill(BLACK)
			back_btn.draw(self.screen)
			fullscreen_btn.draw(self.screen)
			resolutions_menu.draw(self.screen)
			self.blit_fps()
			pygame.display.flip()
			self.clock.tick(30)
			event = events.wait(gui.Button.EVENT_TYPES + [self.INTERRUPTEVENT], context="Settings")

	def main_menu(self):
		resources.load_music('Beyond The Clouds (Dungeon Plunder).ogg')
		pygame.mixer.music.play()
		screen_rect = self.screen.get_rect()
		screen_w, screen_h = self.screen.get_size()

		self.screen.fill(BLACK)
		elinvention = self.MAIN_MENU_FONT.render("Elinvention", 1, WHITE)
		presents = self.MAIN_MENU_FONT.render(_("PRESENTS"), 1, WHITE)
		self.screen.blit(elinvention, utils.center(screen_rect, elinvention.get_rect()))
		self.screen.blit(presents, utils.center(screen_rect, presents.get_rect(), yoffset=self.MAIN_MENU_FONT.get_linesize()))
		pygame.display.flip()
		events.wait(timeout=6000)

		main_menu_image = ResizableImage('Ice Emblem.png', (screen_w, screen_h), (0, 0))
		events.register(VIDEORESIZE, main_menu_image.resize)

		click_to_start = self.MAIN_MENU_FONT.render(_("Click to Start"), 1, ICE)
		hmenu = gui.HorizontalMenu([(_("License"), self.show_license), (_("Settings"), self.settings_menu)], self.SMALL_FONT)
		hmenu.rect.bottomright = self.screen.get_size()

		hmenu.register()
		events.bind_keys((K_RETURN, K_SPACE), self.post_interrupt)
		events.bind_click((1,), self.post_interrupt, hmenu.rect, False)
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
			event = events.wait(hmenu.EVENT_TYPES + [self.INTERRUPTEVENT])

		events.new_context()
		self.screen.fill(BLACK)
		self.screen.blit(main_menu_image.image, (0, 0))

		self.map_menu(main_menu_image)

		pygame.mixer.music.fadeout(2000)
		self.fadeout(2000)
		pygame.mixer.music.stop() # Make sure mixer is not busy

	def map_menu(self, main_menu_image):
		if self.map is not None:
			return
		events.new_context("MapMenu")
		choose_label = self.MAIN_FONT.render(_("Choose a map!"), True, ICE, MENU_BG)
		files = [(f, None) for f in resources.list_maps()]
		menu = gui.Menu(files, self.MAIN_FONT, None, (25, 25))
		menu.rect.center = (self.screen.get_width() // 2, self.screen.get_height() // 2)
		menu.register("MapMenu")
		events.register(VIDEORESIZE, main_menu_image.resize, "MapMenu")

		while menu.choice is None:
			self.screen.fill(BLACK)
			main_menu_image.rect.center = self.screen.get_rect().center
			main_menu_image.draw(self.screen)
			self.screen.blit(choose_label, choose_label.get_rect(top=50, centerx=self.screen.get_rect().centerx))
			menu.rect.center = self.screen.get_rect().center
			menu.draw(self.screen)
			self.blit_fps()
			pygame.display.flip()
			events.wait(gui.Menu.EVENT_TYPES, context="MapMenu")
			self.clock.tick(30)

		try:
			self.load_map(resources.map_path(files[menu.choice][0]))
		except:
			logging.error("Can't load map %s! Probabily the format is not ok.", files[menu.choice][0])
			traceback.print_exc()
			self.map = None
			self.units_manager = None
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
			events.pump()

	def experience_animation(self, unit, bg):
		img_pos = utils.center(self.screen.get_rect(), unit.image.get_rect())
		exp_pos = (img_pos[0], img_pos[1] + unit.image.get_height() + 50)

		sounds.play('exp', -1)

		gained_exp = unit.gained_exp()
		curr_exp = unit.prev_exp
		while curr_exp <= gained_exp + unit.prev_exp:
			if unit.levelled_up() and curr_exp == 100:
				sounds.play('levelup')
			exp = pygame.Surface((curr_exp % 100, 20))
			exp.fill(YELLOW)

			exp_text = self.SMALL_FONT.render(_("EXP: %d") % (curr_exp % 100), True, YELLOW)
			lv_text = self.SMALL_FONT.render(_("LV: %d") % unit.level, True, BLUE)

			self.screen.blit(bg, (0, 0))
			self.screen.blit(unit.image, img_pos)
			self.screen.blit(exp, exp_pos)
			self.screen.blit(exp_text, (exp_pos[0], exp_pos[1] + 25))
			self.screen.blit(lv_text, (exp_pos[0] + exp_text.get_width() + 10, exp_pos[1] + 25))

			curr_exp += 1
			pygame.display.flip()
			self.clock.tick(60)
			events.pump()

		sounds.stop('exp')
		events.wait(timeout=2000)

	def battle(self, attacking, defending):
		events.new_context("Battle")
		attacking_team = self.units_manager.get_team(attacking.color)
		defending_team = self.units_manager.get_team(defending.color)

		att_weapon = attacking.get_active_weapon()
		def_weapon = defending.get_active_weapon()

		attacking.prepare_battle()
		defending.prepare_battle()

		dist = utils.distance(attacking.coord, defending.coord)
		at, dt = attacking.number_of_attacks(defending, dist)

		print("\r\n" + "#" * 12 + " " + _("Fight!!!") + " " + "#" * 12)
		att_str = _("%s is going to attack %d %s")
		print(att_str % (attacking.name, at, _("time") if at == 1 else _("times")))
		print(att_str % (defending.name, dt, _("time") if dt == 1 else _("times")))

		attacking_team.play_music('battle')

		self.blit_map()
		self.fadeout(1000, 10)  # Darker atmosphere

		battle_background = self.screen.copy()

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
			if (at > 0 or dt > 0) and (def_swap.health > 0 and att_swap.health > 0):  # Se ci sono turni e se sono vivi
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
						sounds.play('miss')
					elif outcome == 2:  # Null attack
						def_text = null_text
						sounds.play('null')
					elif outcome == 3:  # Triple hit
						att_text = crit_text
						sounds.play('critical')
					elif outcome == 4:  # Hit
						sounds.play('hit')

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
				for i in range(attacking.health_max):
					x = att_life_pos[0] + (i % 30 * 5)
					y = att_life_pos[1] + i // 30 * 11
					if i < attacking.health:
						self.screen.blit(life_block, (x , y))
					else:
						self.screen.blit(life_block_used, (x , y))
				for i in range(defending.health_max):
					x = def_life_pos[0] + (i % 30 * 5)
					y = def_life_pos[1] + i // 30 * 11
					if i < defending.health:
						self.screen.blit(life_block, (x , y))
					else:
						self.screen.blit(life_block_used, (x , y))
				self.screen.blit(att_info, att_info_pos)
				self.screen.blit(def_info, def_info_pos)
				self.blit_fps()
				events.pump("Battle")
				pygame.display.flip()
				latest_tick = self.clock.tick(60)

			if dt > 0:
				att_swap, def_swap = def_swap, att_swap
				at, dt = dt, at
				att_rect, def_rect = def_rect, att_rect
				att_rect_origin, def_rect_origin = def_rect_origin, att_rect_origin
				att_text_pos, def_text_pos = def_text_pos, att_text_pos
		if attacking.health > 0:
			attacking.gain_exp(defending)
			self.experience_animation(attacking, battle_background)
		else:
			self.kill(attacking)

		if defending.health > 0:
			defending.gain_exp(attacking)
			self.experience_animation(defending, battle_background)
		else:
			self.kill(defending)

		if att_weapon and att_weapon.uses == 0:
			sounds.play('broke')
			broken_text = self.SMALL_FONT.render("%s is broken" % att_weapon.name, True, RED)
			self.screen.blit(broken_text, utils.center(screen_rect, broken_text.get_rect()))
			pygame.display.flip()
			events.wait(timeout=3000, context="Battle")
		if def_weapon and def_weapon.uses == 0:
			sounds.play('broke')
			broken_text = self.SMALL_FONT.render("%s is broken" % def_weapon.name, True, RED)
			self.screen.blit(broken_text, utils.center(screen_rect, broken_text.get_rect()))
			pygame.display.flip()
			events.wait(timeout=3000, context="Battle")

		pygame.mixer.music.fadeout(500)
		pygame.time.wait(500)
		attacking_team.play_music('map', True)

		self.screen.blit(battle_background, (0, 0))
		attacking.played = True

		if defending_team.is_defeated():
			self.winner = attacking_team
		elif attacking_team.is_defeated():
			self.winner = defending_team

		print("#" * 12 + " " + _("Battle ends") + " " + "#" * 12 + "\r\n")

	def kill(self, unit):
		self.map.kill_unit(unit=unit)
		self.units_manager.kill_unit(unit)

	def disable_controls(self):
		events.unregister(MOUSEBUTTONDOWN, self.handle_click)
		events.unregister(MOUSEMOTION, self.handle_mouse_motion)
		events.unregister(KEYDOWN, self.handle_keyboard)
		self.sidebar.endturn_btn.unregister()

	def enable_controls(self):
		events.register(MOUSEBUTTONDOWN, self.handle_click)
		events.register(MOUSEMOTION, self.handle_mouse_motion)
		events.register(KEYDOWN, self.handle_keyboard)
		self.sidebar.endturn_btn.register()

	def switch_turn(self):
		active_team = self.units_manager.switch_turn()
		if not active_team.ai:
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
		pygame.mixer.music.fadeout(1000)
		active_team.play_music('map')
		events.wait(timeout=5000)

	def victory_screen(self):
		print(_("%s wins") % self.winner.name)
		pygame.mixer.stop()
		resources.load_music('Victory Track.ogg')
		pygame.mixer.music.play()
		self.fadeout(1000)

		victory = self.MAIN_MENU_FONT.render(self.winner.name + ' wins!', 1, self.winner.color)
		thank_you = self.MAIN_MENU_FONT.render(_('Thank you for playing Ice Emblem!'), 1, ICE)

		self.screen.fill(BLACK)
		self.screen.blit(victory, utils.center(self.screen.get_rect(), victory.get_rect(), yoffset=-50))
		self.screen.blit(thank_you, utils.center(self.screen.get_rect(), thank_you.get_rect(), yoffset=50))

		pygame.display.flip()

		pygame.event.clear()
		events.wait()
		pygame.mixer.music.fadeout(2000)
		self.fadeout(2000)
		pygame.mixer.music.stop()

	def get_mouse_coord(self, pos=None):
		if pos is None:
			pos = pygame.mouse.get_pos()
		try:
			return self.map.mouse2cell(pos)
		except ValueError:
			return None

	def action_menu(self, actions, rollback, pos):
		events.new_context("ActionMenu")

		menu = gui.Menu(actions, self.SMALL_FONT, rollback, (5, 10), pos)
		menu.register("ActionMenu")

		self.map.still_attack_area(self.map.curr_sel)
		self.map.update_highlight()

		self.blit_map()
		self.blit_info()

		action = None
		while action is None:
			menu.draw(self.screen)
			pygame.display.flip()
			events.wait(gui.Menu.EVENT_TYPES, context="ActionMenu")
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
			events.new_context()
			self.enable_controls()
			self.battle_wrapper(self.get_mouse_coord())
		elif event.button == 3:
			self.__attack_abort()

	def __attack_keydown(self, event):
		# user must choose an enemy unit
		if event.key == pygame.K_SPACE and self.map.is_enemy_cursor():
			events.new_context()
			self.enable_controls()
			self.battle_wrapper(self.map.cursor.coord)
		elif event.key == pygame.K_ESCAPE:
			self.__attack_abort()
		self.map.cursor.update(event)

	def __attack_abort(self):
		events.new_context()
		self.enable_controls()
		self.map.move(self.map.get_unit(self.map.curr_sel), self.map.prev_sel)
		self.map.reset_selection()

	def reset(self):
		pygame.mixer.fadeout(1000)
		self.fadeout(1000)
		self.done = True

	def pause_menu(self):
		events.new_context("PauseMenu")
		menu_entries = [
			('Return to Game', None),
			('Return to Main Menu', self.reset),
			('Return to O.S.', utils.return_to_os)
		]
		menu = gui.Menu(menu_entries, self.MAIN_FONT)
		menu.rect.center = self.screen.get_rect().center

		menu.register("PauseMenu")

		while menu.choice is None:
			menu.draw(self.screen)
			pygame.display.flip()
			events.wait(gui.Menu.EVENT_TYPES, context="PauseMenu")

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
				self.disable_controls()
				events.register(MOUSEBUTTONDOWN, self.__attack_mousebuttondown)
				events.register(KEYDOWN, self.__attack_keydown)
				events.register(MOUSEMOTION, self.map.cursor.update)

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

