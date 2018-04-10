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
import gui
import utils
import ai
import room
import rooms
import colors as c
import fonts as f
import state as s


class NextTurnTransition(gui.Label):
    def __init__(self, team):
        super().__init__(_('%s phase') % team.name, f.MAIN_MENU, txt_color=team.color, bg_color=(0, 0, 0, 0), alpha=True, clear_screen=None, allowed_events=[p.MOUSEBUTTONDOWN, p.KEYDOWN], size=display.get_size(), wait=True)
        self.team = team

    def begin(self):
        super().begin()
        pygame.mixer.music.fadeout(1000)
        self.done = True

    def end(self):
        super().end()
        self.wait_event(timeout=2000)


class Turn(room.Room):
    def __init__(self, **kwargs):
        super().__init__(size=display.get_size(), wait=False, children=[sidebar], **kwargs)

    def begin(self):
        self.team = s.units_manager.active_team
        self.team.play_music('map')
        self.sidebar = gui.Sidebar()
        self.add_children(s.loaded_map, self.sidebar)

    def handle_keydown(self, event):
        if event.key == pygame.K_ESCAPE:
            self.pause_menu()

    def loop(self, _events, dt):
        """
        Main loop.
        """
        super().loop(_events, dt)
        if not s.loaded_map.valid:
            self.sidebar.invalidate()
        if s.winner is not None:
            self.done = True
        elif self.team.is_turn_over():
            self.switch_turn()

    def draw(self):
        self.surface.fill(c.BLACK)
        super().draw()

    def pause_menu(self):
        menu_entries = [
            (_('Return to Game'), None),
            (_('Return to Main Menu'), self.reset),
            (_('Return to O.S.'), utils.return_to_os)
        ]
        menu = gui.Menu(menu_entries, f.MAIN, center=display.get_rect().center)
        self.run_room(menu)

    def switch_turn(self, *args):
        next_team = s.units_manager.switch_turn()
        if isinstance(next_team, ai.AI):
            room.next_room(AITurn())
        else:
            room.next_room(PlayerTurn())
        room.next_room(NextTurnTransition(next_team))
        self.done = True


class PlayerTurn(Turn):

    def __init__(self):
        super().__init__(allowed_events=[p.MOUSEBUTTONDOWN, p.KEYDOWN, p.MOUSEMOTION])


class AITurn(Turn):

    def begin(self):
        super().begin()
        self.actions = iter(self.team)

    def loop(self, _events, dt):
        super().loop(_events, dt)
        try:
            action = next(self.actions)
            for fps in action:
                self.fps = fps
                room.draw_room(self)
            s.loaded_map.invalidate()
        except StopIteration:
            self.team.end_turn()


def play(map_file):
    global sidebar
    while True:
        if map_file is None:
            room.queue_room(rooms.SplashScreen())
            room.queue_room(rooms.MainMenu())
        else:
            s.load_map(map_file)
        room.run()
        sidebar = gui.Sidebar()
        if isinstance(s.units_manager.active_team, ai.AI):
            room.queue_room(AITurn())
        else:
            room.queue_room(PlayerTurn())
        room.queue_room(rooms.VictoryScreen())
        room.run()
        s.loaded_map = None
        s.units_manager = None
        s.winner = None
