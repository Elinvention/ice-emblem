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
import pygame.locals as p

import display
import sounds
import events
import gui
import utils
import ai
import room
import rooms
import colors as c
import fonts as f
import state as s


TIME_BETWEEN_ATTACKS = 2000  # Time to wait between each attack animation


def experience_animation(unit, bg):
    window = display.window
    img_pos = utils.center(window.get_rect(), unit.image.get_rect())
    exp_pos = (img_pos[0], img_pos[1] + unit.image.get_height() + 50)

    sounds.play('exp', -1)

    gained_exp = unit.gained_exp()
    curr_exp = unit.prev_exp
    while curr_exp <= gained_exp + unit.prev_exp:
        if unit.levelled_up() and curr_exp == 100:
            sounds.play('levelup')
        exp = pygame.Surface((curr_exp % 100, 20))
        exp.fill(c.YELLOW)

        exp_text = f.SMALL_FONT.render(_("EXP: %d") % (curr_exp % 100), True, c.YELLOW)
        lv_text = f.SMALL_FONT.render(_("LV: %d") % unit.level, True, c.BLUE)

        window.blit(bg, (0, 0))
        window.blit(unit.image, img_pos)
        window.blit(exp, exp_pos)
        window.blit(exp_text, (exp_pos[0], exp_pos[1] + 25))
        window.blit(lv_text, (exp_pos[0] + exp_text.get_width() + 10, exp_pos[1] + 25))

        curr_exp += 1
        pygame.display.flip()
        display.clock.tick(60)
        events.pump()

    sounds.stop('exp')
    events.set_allowed([p.MOUSEBUTTONDOWN, p.KEYDOWN])
    events.wait(timeout=2000)


def attack(attacking, defending):
    events.new_context("Battle")
    attacking_team = s.units_manager.get_team(attacking.color)
    defending_team = s.units_manager.get_team(defending.color)

    att_weapon = attacking.items.active
    def_weapon = defending.items.active

    attacking.prepare_battle()
    defending.prepare_battle()

    dist = utils.distance(attacking.coord, defending.coord)
    at, dt = attacking.number_of_attacks(defending, dist)

    print(f"\r\n{'#' * 12} {attacking.name} vs {defending.name} {'#' * 12}")
    att_str = _("%s is going to attack %d %s")
    print(att_str % (attacking.name, at, _("time") if at == 1 else _("times")))
    print(att_str % (defending.name, dt, _("time") if dt == 1 else _("times")))

    attacking_team.play_music('battle')

    s.loaded_map.draw(window)
    display.fadeout(1000, 10)  # Darker atmosphere

    battle_background = window.copy()

    att_swap = attacking
    def_swap = defending

    att_name = f.MAIN_FONT.render(attacking.name, 1, attacking_team.color)
    def_name = f.MAIN_FONT.render(defending.name, 1, defending_team.color)

    miss_text = f.SMALL_FONT.render(_("MISS"), 1, c.YELLOW).convert_alpha()
    null_text = f.SMALL_FONT.render(_("NULL"), 1, c.RED).convert_alpha()
    crit_text = f.SMALL_FONT.render(_("TRIPLE"), 1, c.RED).convert_alpha()
    screen_rect = window.get_rect()

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
    life_block.fill(c.GREEN)
    life_block_used.fill(c.RED)

    collide = screen_rect.centerx, att_rect.bottom - 1
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
        while animation_time < TIME_BETWEEN_ATTACKS:
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
                #miss_target = def_rect_origin.y - 50

            if animate_miss:
                t = (animation_time - animate_miss) / 1000
                def_rect.bottom = int(att_rect.bottom - 400 * t + 800 * t * t)
                if def_rect.bottom > att_rect.bottom:
                    animate_miss = False
                    def_rect.bottom = att_rect.bottom

            animation_time = pygame.time.get_ticks() - start_animation

            att_info = attacking.render_info(f.SMALL_FONT)
            def_info = defending.render_info(f.SMALL_FONT)

            window.blit(battle_background, (0, 0))
            window.blit(att_swap.image, att_rect.topleft)
            window.blit(def_swap.image, def_rect.topleft)
            if att_text is not None:
                window.blit(att_text, att_text_pos)
            if def_text is not None:
                window.blit(def_text, def_text_pos)
            window.blit(att_name, att_name_pos)
            window.blit(def_name, def_name_pos)
            for i in range(attacking.health_max):
                x = att_life_pos[0] + (i % 30 * 5)
                y = att_life_pos[1] + i // 30 * 11
                if i < attacking.health:
                    window.blit(life_block, (x , y))
                else:
                    window.blit(life_block_used, (x , y))
            for i in range(defending.health_max):
                x = def_life_pos[0] + (i % 30 * 5)
                y = def_life_pos[1] + i // 30 * 11
                if i < defending.health:
                    window.blit(life_block, (x , y))
                else:
                    window.blit(life_block_used, (x , y))
            window.blit(att_info, att_info_pos)
            window.blit(def_info, def_info_pos)
            display.draw_fps()
            events.pump("Battle")
            display.flip()
            latest_tick = display.tick(60)

        if dt > 0:
            att_swap, def_swap = def_swap, att_swap
            at, dt = dt, at
            att_rect, def_rect = def_rect, att_rect
            att_rect_origin, def_rect_origin = def_rect_origin, att_rect_origin
            att_text_pos, def_text_pos = def_text_pos, att_text_pos
    if attacking.health > 0:
        attacking.gain_exp(defending)
        experience_animation(attacking, battle_background)
    else:
        s.kill(attacking)

    if defending.health > 0:
        defending.gain_exp(attacking)
        experience_animation(defending, battle_background)
    else:
        s.kill(defending)

    if att_weapon and att_weapon.uses == 0:
        sounds.play('broke')
        broken_text = f.SMALL_FONT.render("%s is broken" % att_weapon.name, True, c.RED)
        window.blit(broken_text, utils.center(screen_rect, broken_text.get_rect()))
        display.flip()
        events.wait(timeout=3000, context="Battle")
    if def_weapon and def_weapon.uses == 0:
        sounds.play('broke')
        broken_text = f.SMALL_FONT.render("%s is broken" % def_weapon.name, True, c.RED)
        window.blit(broken_text, utils.center(screen_rect, broken_text.get_rect()))
        display.flip()
        events.wait(timeout=3000, context="Battle")

    pygame.mixer.music.fadeout(500)
    events.block_all()
    events.wait(500, "Battle")
    events.allow_all()
    attacking_team.play_music('map', True)

    window.blit(battle_background, (0, 0))
    attacking.played = True

    if defending_team.is_defeated():
        s.winner = attacking_team
    elif attacking_team.is_defeated():
        s.winner = defending_team

    print("#" * 12 + " " + _("Battle ends") + " " + "#" * 12 + "\r\n")


def battle_wrapper(coord):
    defending = s.loaded_map.get_unit(coord)
    attacking = s.loaded_map.curr_unit

    # enemy chosen by the user... let the battle begin!
    attack(attacking, defending)

    s.loaded_map.reset_selection()

def switch_turn(*args):
    active_team = s.units_manager.switch_turn()
    s.loaded_map.reset_selection()
    display.window.fill(c.BLACK)
    s.loaded_map.draw(display.window)
    sidebar.update()
    phase_str = _('%s phase') % active_team.name
    phase = f.MAIN_MENU_FONT.render(phase_str, 1, active_team.color)
    display.window.blit(phase, utils.center(display.window.get_rect(), phase.get_rect()))
    pygame.display.flip()
    pygame.mixer.music.fadeout(1000)
    active_team.play_music('map')
    events.set_allowed([p.MOUSEBUTTONDOWN, p.KEYDOWN])
    events.wait(timeout=5000)


class Sidebar(object):
    def __init__(self, font):
        self.rect = gui.Rect(w=250, h=display.window.get_height(), right=display.window.get_width())
        self.start_time = pygame.time.get_ticks()
        self.font = font
        self.endturn_btn = gui.Button(_("End Turn"), self.font, callback=switch_turn)

    def update(self):
        coord = s.loaded_map.cursor.coord
        unit = s.loaded_map.get_unit(coord)
        terrain = s.loaded_map[coord]
        team = s.units_manager.active_team
        render = lambda x, y: self.font.render(x, True, y)
        self.rect.h = display.window.get_height()
        self.rect.x = display.window.get_width() - self.rect.w
        self.endturn_btn.rect.bottomright = self.rect.bottomright

        sidebar = pygame.Surface(self.rect.size)
        sidebar.fill((100, 100, 100))

        turn_s = render(_('%s phase') % team.name, team.color)
        pos = turn_s.get_rect(top=40, left=10)
        sidebar.blit(turn_s, pos)

        t_info = [
            render(terrain.name, c.WHITE),
            render(_("Def: %d") % terrain.defense, c.WHITE),
            render(_("Avoid: %d") % terrain.avoid, c.WHITE),
            render(_("Allowed: %s") % (", ".join(terrain.allowed)), c.WHITE),
        ] if terrain else []

        weapon = unit.items.active if unit else None
        weapon_name = weapon.name if weapon else _("No Weapon")
        u_info = [
            render(unit.name, unit.team.color),
            render(weapon_name, c.WHITE),
        ] if unit else [render(_("No unit"), c.WHITE)]

        delta = (pygame.time.get_ticks() - self.start_time) // 1000
        hours, remainder = divmod(delta, 3600)
        minutes, seconds = divmod(remainder, 60)

        global_info = [
            render('X: %d Y: %d' % coord, c.WHITE),
            render('%02d:%02d:%02d' % (hours, minutes, seconds), c.WHITE),
        ]

        out = t_info + u_info + global_info

        for i in out:
            pos.move_ip(0, 40)
            sidebar.blit(i, pos)

        display.window.blit(sidebar, self.rect)
        self.endturn_btn.draw()

sidebar = None


class PlayerTurn(room.Room):
    def __init__(self, team):
        super().__init__(allowed_events=[p.KEYDOWN, p.MOUSEBUTTONDOWN, p.MOUSEMOTION, events.CLOCK])
        self.add_child(sidebar.endturn_btn)
        self.team = team

    def begin(self):
        super().begin()
        self.register(p.MOUSEBUTTONDOWN, self.handle_click)
        self.register(p.MOUSEMOTION, self.handle_mouse_motion)
        self.register(p.KEYDOWN, self.handle_keyboard)

    def draw(self):
        display.window.fill(c.BLACK)
        s.loaded_map.draw(display.window)
        sidebar.update()

    def loop(self, _events):
        return self.team != s.units_manager.active_team or self.team.is_turn_over()

    def handle_mouse_motion(self, event):
        s.loaded_map.handle_mouse_motion(event)

    def handle_click(self, event):
        if s.loaded_map.handle_click(event):
            self.action_menu(event.pos)

    def handle_keyboard(self, event):
        if event.key == pygame.K_ESCAPE:
            self.pause_menu()
        else:
            if s.loaded_map.handle_keyboard(event):
                pos = s.loaded_map.tilemap.pixel_at(*s.loaded_map.cursor.coord)
                pos = (pos[0] + s.loaded_map.tilemap.tile_width, pos[1] + s.loaded_map.tilemap.tile_height)
                self.action_menu(pos)

    def action_menu(self, pos):
        menu = rooms.ActionMenu(topleft=pos, padding=10, leading=5)
        room.run_room(menu)
        return menu.choice

    def pause_menu(self):
        events.new_context("PauseMenu")
        menu_entries = [
            ('Return to Game', None),
            ('Return to Main Menu', self.reset),
            ('Return to O.S.', utils.return_to_os)
        ]
        menu = gui.Menu(menu_entries, f.MAIN_FONT, context="PauseMenu")
        menu.rect.center = display.window.get_rect().center
        room.run_room(menu)

    def reset(self):
        pygame.mixer.fadeout(1000)
        display.fadeout(1000)
        room.stop()


class AITurn(room.Room):
    def __init__(self, actions):
        super().__init__(allowed_events=[p.KEYDOWN, p.MOUSEBUTTONDOWN], wait=False, fps=0.5)
        self.actions = actions

    def draw(self):
        display.window.fill(c.BLACK)
        s.loaded_map.draw(display.window)

    def loop(self, _events):
        try:
            for fps in next(self.actions):
                self.draw()
                display.flip()
                display.tick(fps)
        except StopIteration:
            return True
        return False


class Game(room.Room):
    def __init__(self):
        super().__init__(wait=False)

    def begin(self):
        global sidebar
        s.units_manager.active_team.play_music('map')
        sidebar = Sidebar(f.SMALL_FONT)

    def draw(self):
        display.window.fill(c.BLACK)
        s.loaded_map.draw(display.window)
        sidebar.update()

    def loop(self, _events):
        """
        Main loop.
        """
        active_team = s.units_manager.active_team
        if isinstance(active_team.ai, ai.AI):
            actions = iter(active_team.ai)
            room.run_room(AITurn(actions))
        else:
            room.run_room(PlayerTurn(active_team))
        if s.winner is None and active_team == s.units_manager.active_team:
            switch_turn()
        return s.winner is not None

    def end(self):
        super().end()
        pygame.time.set_timer(events.CLOCK, 0);


def play(map_file):
    while True:
        if map_file is None:
            room.queue_room(rooms.SplashScreen())
            room.queue_room(rooms.MainMenu())
        else:
            s.load_map(map_file)
        room.queue_room(Game())
        room.queue_room(rooms.VictoryScreen())
        room.run()
        s.loaded_map = None
        s.units_manager = None
        s.winner = None
