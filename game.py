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
import os.path

from item import Item, Weapon
from map import Map
from unit import Unit, Player
from menu import Menu
from colors import *

def center(rect1, rect2, xoffset=0, yoffset=0):
	"""Center rect2 in rect1 with offset."""
	return (rect1.centerx - rect2.centerx + xoffset, rect1.centery - rect2.centery + yoffset)

def distance(p0, p1):
    return abs(p0[0] - p1[0]) + abs(p0[1] - p1[1])

class Game(object):
	TIME_BETWEEN_ATTACKS = 2000
	MAP_STATE = 0
	CHOOSE_ENEMY_STATE = 1
	INPUT_EVENTS = [MOUSEBUTTONDOWN, QUIT, KEYDOWN]

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
		self.map = Map(map_path, (800, 600), colors, units)

		#pygame.mixer.set_reserved(2)
		self.overworld_music_ch = pygame.mixer.Channel(0)
		self.battle_music_ch = pygame.mixer.Channel(1)

		self.main_menu_music = pygame.mixer.Sound(os.path.abspath(music['menu']))
		self.overworld_music = pygame.mixer.Sound(os.path.abspath(music['overworld']))
		self.battle_music = pygame.mixer.Sound(os.path.abspath(music['battle']))

		self.winner = None
		self.state = 0
		self.prev_coord = None

	def blit_map(self):
		"""
		This method renders and blits the map on the screen.
		"""
		self.map.tilemap.draw(self.screen)

	def blit_info(self):
		screen_w, screen_h = self.screen.get_size()
		try:
			cell_x, cell_y = self.map.mouse2cell(pygame.mouse.get_pos())
		except ValueError:
			pass
		else:
			cell_label = self.SMALL_FONT.render('X: %d Y: %d' % (cell_x, cell_y), True, WHITE)
			rec = cell_label.get_rect(bottom=screen_h - 5, right=screen_w - 5)
			self.screen.blit(cell_label, rec)

		turn = self.whose_turn()
		turn_label = self.SMALL_FONT.render('phase', True, WHITE)
		turn_square = pygame.Surface((16, 16))
		turn_square.fill(turn.color)
		turn_surface = pygame.Surface((turn_label.get_width() + 20, self.SMALL_FONT.get_linesize()))
		turn_surface.blit(turn_square, (0, (turn_label.get_height() // 2) - 8))
		turn_surface.blit(turn_label, (20, 0))
		pos = turn_surface.get_rect(bottom=screen_h - 40, right=screen_w - 5)
		self.screen.blit(turn_surface, pos)

	def screen_resize(self, screen_size):
		"""
		This method takes care to resize and scale everithing to match
		the new window's size. The minum window size is 800x600.
		On Debian testing there is an issue that makes the window kind of
		"rebel" while trying to resize it.
		"""
		if screen_size[0] < 800:
			screen_size = (800, screen_size[1])
		if screen_size[1] < 600:
			screen_size = (screen_size[0], 600)
		self.screen = pygame.display.set_mode(screen_size, pygame.RESIZABLE)
		self.map.screen_resize(screen_size)

	def play_overworld_music(self):
		"""Start playing overworld music in a loop."""
		self.overworld_music_ch.play(self.overworld_music, -1)

	def wait_for_user_input(self, timeout=-1, event_types=None, fps=10):
		"""
		This function waits for the user to left-click somewhere and,
		if the timeout argument is positive, exits after the specified
		number of milliseconds.
		"""
		if event_types is None:
			event_types = self.INPUT_EVENTS

		now = start = pygame.time.get_ticks()
		event = pygame.event.poll()

		while event.type not in event_types and (now - start < timeout or timeout < 0):
			event = pygame.event.poll()
			if event.type == pygame.NOEVENT:
				self.clock.tick(fps)
				now = pygame.time.get_ticks()
			elif event.type == pygame.QUIT:  # If user clicked close
				pygame.quit()
				sys.exit(0)

		return event

	def main_menu(self):
		self.main_menu_music.play()
		screen_rect = self.screen.get_rect()
		screen_w, screen_h = self.screen.get_size()

		self.screen.fill(BLACK)

		elinvention = self.MAIN_MENU_FONT.render("Elinvention", 1, WHITE)
		presents = self.MAIN_MENU_FONT.render("PRESENTS", 1, WHITE)

		self.screen.blit(elinvention, center(screen_rect, elinvention.get_rect()))

		self.screen.blit(presents, center(screen_rect, presents.get_rect(), yoffset=self.MAIN_MENU_FONT.get_linesize()))

		pygame.display.flip()

		self.wait_for_user_input(6000)


		path = os.path.abspath('images/Ice Emblem.png')
		main_menu_image = pygame.image.load(path).convert_alpha()
		main_menu_image = pygame.transform.smoothscale(main_menu_image, (screen_w, screen_h))

		click_to_start = self.MAIN_MENU_FONT.render("Click to Start", 1, ICE)
		click_license = self.SMALL_FONT.render("License", 1, WHITE)

		self.screen.blit(main_menu_image, (0, 0))
		self.screen.blit(click_to_start, center(screen_rect, click_to_start.get_rect(), yoffset=200))
		license_w, license_h = click_license.get_size()
		self.screen.blit(click_license, (screen_w - license_w, screen_h - license_h))

		pygame.display.flip()

		click_x, click_y = self.wait_for_user_input().pos

		if click_x > screen_w - license_w and click_y > screen_h - license_h:
			path = os.path.abspath('images/GNU GPL.jpg')
			gpl_image = pygame.image.load(path).convert()
			gpl_image = pygame.transform.smoothscale(gpl_image, (screen_rect.w, screen_rect.h))
			self.screen.blit(gpl_image, (0, 0))
			pygame.display.flip()
			self.wait_for_user_input()

		pygame.mixer.fadeout(2000)
		self.fade_out(2000)
		pygame.mixer.stop() # Make sure mixer is not busy

	def blit_fps(self):
		screen_w, screen_h = self.screen.get_size()
		fps = self.clock.get_fps()
		fpslabel = self.FPS_FONT.render(str(int(fps)) + ' FPS', True, WHITE)
		rec = fpslabel.get_rect(top=5, right=screen_w - 5)
		self.screen.blit(fpslabel, rec)

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

	def fade_out(self, fade_out_time, percent=0):
		start = pygame.time.get_ticks()
		fade = self.screen.copy()
		state_time = 0
		percent = (100 - percent) / 100.0

		while state_time < fade_out_time:
			alpha = int(255.0 - 255.0 * state_time / fade_out_time * percent)
			fade.set_alpha(alpha)
			self.screen.fill(BLACK)
			self.screen.blit(fade, (0, 0))
			pygame.display.flip()
			self.clock.tick(60)
			state_time = pygame.time.get_ticks() - start

	def check_quit_event(self):
		for event in pygame.event.get(pygame.QUIT):
			if event.type == pygame.QUIT:  # If user clicked close
				pygame.quit()
				sys.exit()

	def experience_animation(self, unit, bg):
		img_pos = center(self.screen.get_rect(), unit.image.get_rect())
		exp_pos = (img_pos[0], img_pos[1] + unit.image.get_height() + 50)

		curr_exp = unit.prev_exp
		target_exp = unit.exp if unit.prev_exp <= unit.exp else 100 + unit.exp

		while curr_exp <= unit.exp:
			exp = pygame.Surface((curr_exp % 100, 20))
			exp.fill(YELLOW)

			exp_text = self.SMALL_FONT.render("EXP: %d" % (curr_exp % 100), True, YELLOW)
			lv_text = self.SMALL_FONT.render("LV: %d" % unit.lv, True, BLUE)

			self.screen.blit(bg, (0, 0))
			self.screen.blit(unit.image, img_pos)
			self.screen.blit(exp, exp_pos)
			self.screen.blit(exp_text, (exp_pos[0], exp_pos[1] + 25))
			self.screen.blit(lv_text, (exp_pos[0] + exp_text.get_width() + 10, exp_pos[1] + 25))

			curr_exp += 1
			pygame.display.flip()
			self.clock.tick(60)
			self.check_quit_event()

		self.wait_for_user_input(2000)

	def battle(self, attacking, defending, dist):
		attacking_player = self.whose_unit(attacking)
		defending_player = self.whose_unit(defending)

		attacking.prepare_battle()
		defending.prepare_battle()

		at, dt = attacking.number_of_attacks(defending, dist)

		print("\r\n" + "#" * 12 + " Fight!!! " + "#" * 12)
		print("%s is going to attack %d %s" %
				(attacking.name, at, "time" if at == 1 else "times"))
		print("%s is going to attack %d %s" %
				(defending.name, dt, "time" if dt == 1 else "times"))

		self.overworld_music_ch.pause()  # Stop music and loop fight music
		self.battle_music_ch.play(self.battle_music, -1)

		latest_attack = start = pygame.time.get_ticks()

		self.fade_out(1000, 10)  # Darker atmosphere

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

		missed_text = self.SMALL_FONT.render("MISSED", 1, YELLOW).convert_alpha()
		void_text = self.SMALL_FONT.render("VOID ATTACK", 1, BLUE).convert_alpha()
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
								att_image_pos = ATT_IMAGE_POS
								animate_attack = False
						else:
							def_image_pos = (def_image_pos[0] - speed, 100)
							#print(defending.name + str(def_image_pos))
							if def_image_pos[0] <= 300:
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
		self.blit_map()
		self.blit_info()
		phase_str = self.active_player.name + ' phase'
		phase = self.MAIN_MENU_FONT.render(phase_str, 1, self.active_player.color)
		self.screen.blit(phase, center(self.screen.get_rect(), phase.get_rect()))
		pygame.display.flip()
		self.wait_for_user_input(5000)

	def victory_screen(self):
		print(self.winner.name + " wins")
		pygame.mixer.stop()
		pygame.mixer.music.load(os.path.abspath('music/Victory Track.ogg'))
		pygame.mixer.music.play()
		self.fade_out(1000)

		victory = self.MAIN_MENU_FONT.render(self.winner.name + ' wins!', 1, self.winner.color)
		thank_you = self.MAIN_MENU_FONT.render('Thank you for playing Ice Emblem!', 1, ICE)

		self.screen.fill(BLACK)
		self.screen.blit(victory, center(self.screen.get_rect(), victory.get_rect(), yoffset=-50))
		self.screen.blit(thank_you, center(self.screen.get_rect(), thank_you.get_rect(), yoffset=50))

		pygame.display.flip()

		pygame.event.clear()
		self.wait_for_user_input()

	def get_mouse_coord(self, pos=None):
		if pos is None:
			pos = pygame.mouse.get_pos()
		try:
			return self.map.mouse2cell(pos)
		except ValueError:
			return None

	def handle_mouse_motion(self, event):
		coord = self.get_mouse_coord(event.pos)
		if coord is not None and coord != self.prev_coord:
			self.prev_coord = coord
			self.map.cursor.update(event)
			self.map.update_arrow(coord)

	def action_menu(self, actions, rollback, pos):
		self.blit_map()

		menu = Menu(actions, self.SMALL_FONT, (5, 10), pos)

		action = None
		while action is None:
			self.screen.blit(menu.render(), menu.pos)
			pygame.display.flip()
			event = self.wait_for_user_input()
			print(event)
			if event.type == pygame.MOUSEBUTTONDOWN:
				if event.button == 3:
					action = -1
					rollback()
				elif event.button == 1:
					action = menu.handle_click(event)
			elif event.type == pygame.KEYDOWN:
				action = menu.handle_keydown(event)

		return action

	def battle_wrapper(self):
		coord = self.get_mouse_coord()

		defending = self.map.get_unit(coord)
		attacking = self.map.get_unit(self.map.curr_sel)

		# enemy chosen by the user... let the battle begin!
		self.battle(attacking, defending, distance(coord, self.map.curr_sel))

		self.state = self.MAP_STATE  # return to map state
		self.map.reset_selection()

	def action_menu_wrapper(self, menu_entries):
		if menu_entries is not None and len(menu_entries) > 0:  # Have to display action menu
			# rollback will be called if the user aborts the
			# action menu by right clicking
			rollback = self.map.rollback_callback
			pos = pygame.mouse.get_pos()
			action = self.action_menu(menu_entries, rollback, pos)

			if action == 0 and menu_entries[0][0] is "Attack":
				# user choose to attack.
				# Now he has to choose the enemy to attack
				# so the next click must be an enemy unit
				self.state = self.CHOOSE_ENEMY_STATE

	def abort_action(self):
		self.state = self.MAP_STATE
		self.map.move(self.map.curr_sel, self.map.prev_sel)
		self.map.reset_selection()

	def handle_click(self, event):
		"""
		Handles clicks.
		"""

		if self.state == self.MAP_STATE:  # normal state
			menu_entries = self.map.handle_click(event, self.active_player)
			self.action_menu_wrapper(menu_entries)

		elif self.state == self.CHOOSE_ENEMY_STATE:
			# user must click on an enemy unit
			if event.button == 1 and self.map.is_attack_click(event.pos):
				self.battle_wrapper()
			elif event.button == 3:
				self.abort_action()

		if self.winner is None:
			self.check_turn()

	def check_turn(self):
		if self.active_player.is_turn_over():
			self.switch_turn()

	def handle_keyboard(self, event):
		if self.state == self.MAP_STATE:  # normal state
			menu_entries = self.map.handle_keyboard(event, self.active_player)
			self.action_menu_wrapper(menu_entries)
		elif self.state == self.CHOOSE_ENEMY_STATE:
			# user must choose an enemy unit
			if event.key == pygame.K_SPACE and self.map.is_enemy_cursor():
				self.battle_wrapper()
			elif event.key == pygame.K_ESCAPE:
				self.abort_action()

		if self.winner is None:
			self.check_turn()

	def handle_event(self, event):
		if event.type == pygame.MOUSEBUTTONDOWN: # user click on map
			self.handle_click(event)
		elif event.type == pygame.MOUSEMOTION:
			self.handle_mouse_motion(event)
		elif event.type == pygame.KEYDOWN:
			self.handle_keyboard(event)
		elif event.type == pygame.VIDEORESIZE: # user resized window
			self.screen_resize(event.size) # update window's size

