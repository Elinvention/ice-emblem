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
import gc

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
        bg = display.window.copy().convert()
        bg.set_alpha(100)
        super().__init__(_('%s phase') % team.name, f.MAIN_MENU, txt_color=team.color, bg_color=c.BLACK, bg_image=bg, allowed_events=[p.MOUSEBUTTONDOWN, p.KEYDOWN], wait=True, layout_gravity=gui.Gravity.FILL)
        self.next_team = team

    def begin(self):
        super().begin()
        pygame.mixer.music.fadeout(1000)
        if isinstance(self.next_team, ai.AI):
            self.next = AITurn()
        else:
            self.next = PlayerTurn()
        self.done = True

    def end(self):
        super().end()
        self.wait_event(timeout=2000)
        sidebar.turn_changed(self.next_team)


class Turn(gui.Container):
    def __init__(self, **kwargs):
        super().__init__(layout_gravity=gui.Gravity.FILL, gravity=gui.Gravity.NO_GRAVITY, wait=False, **kwargs)
        self.add_children(sidebar, s.loaded_map)

    def begin(self):
        self.team = s.units_manager.active_team
        self.team.play_music('map')
        self.bind_keys((p.K_SPACE, ), lambda *_: s.units_manager.active_team.end_turn())


    def handle_keydown(self, event):
        if event.key == pygame.K_ESCAPE:
            self.pause_menu()

    def loop(self, _events, dt):
        """
        Main loop.
        """
        super().loop(_events, dt)
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
        display.darken(200)
        menu = gui.Menu(menu_entries, f.MAIN, layout_gravity=gui.Gravity.CENTER, dismiss_callback=True, clear_screen=None)
        room.run_room(menu)

    def reset(self, *_):
        room.run_room(rooms.Fadeout(1000))
        room.stop()

    def switch_turn(self, *args):
        next_team = s.units_manager.switch_turn()
        self.next = NextTurnTransition(next_team)
        self.done = True

    def end(self):
        s.loaded_map.reset_selection()


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
            room.run(rooms.SplashScreen())
            room.run(rooms.Fadeout(2000))
        else:
            s.load_map(map_file)
        sidebar = gui.Sidebar(die_when_done=False)
        room.run(NextTurnTransition(s.units_manager.active_team))
        gc.collect()
        s.loaded_map = None
        s.units_manager = None
        s.winner = None
