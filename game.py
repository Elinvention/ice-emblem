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


def attack(attacking, defending):
    room.run_room(rooms.BattleAnimation(attacking, defending))

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
    phase = f.MAIN_MENU.render(phase_str, 1, active_team.color)
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

    def draw(self):
        display.window.fill(c.BLACK)
        s.loaded_map.draw(display.window)
        sidebar.update()

    def loop(self, _events, dt):
        return self.team != s.units_manager.active_team or self.team.is_turn_over()

    def handle_mousemotion(self, event):
        s.loaded_map.handle_mousemotion(event)

    def handle_mousebuttondown(self, event):
        if s.loaded_map.handle_mousebuttondown(event):
            self.action_menu(event.pos)

    def handle_keydown(self, event):
        if event.key == pygame.K_ESCAPE:
            self.pause_menu()
        else:
            if s.loaded_map.handle_keydown(event):
                pos = s.loaded_map.tilemap.pixel_at(*s.loaded_map.cursor.coord)
                pos = (pos[0] + s.loaded_map.tilemap.tile_width, pos[1] + s.loaded_map.tilemap.tile_height)
                self.action_menu(pos)

    def action_menu(self, pos):
        menu = rooms.ActionMenu(topleft=pos, padding=10, leading=5)
        self.run_room(menu)
        return menu.choice

    def pause_menu(self):
        menu_entries = [
            ('Return to Game', None),
            ('Return to Main Menu', self.reset),
            ('Return to O.S.', utils.return_to_os)
        ]
        menu = gui.Menu(menu_entries, f.MAIN, center=display.get_rect().center)
        self.run_room(menu)

    def reset(self, *_):
        room.run_room(rooms.Fadeout(1000))
        room.stop()


class AITurn(room.Room):
    def __init__(self, actions):
        super().__init__(allowed_events=[p.KEYDOWN, p.MOUSEBUTTONDOWN], wait=False, fps=0.5)
        self.actions = actions

    def draw(self):
        display.window.fill(c.BLACK)
        s.loaded_map.draw(display.window)

    def loop(self, _events, dt):
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

    def loop(self, _events, dt):
        """
        Main loop.
        """
        active_team = s.units_manager.active_team
        if isinstance(active_team.ai, ai.AI):
            actions = iter(active_team.ai)
            self.run_room(AITurn(actions))
        else:
            self.run_room(PlayerTurn(active_team))
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
