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
        super().__init__(_("%s phase") % team.name, f.MAIN_MENU, txt_color=team.color,
                         layout=room.Layout(gravity=room.Gravity.FILL),
                         background=room.Background(color=c.BLACK), allowed_events=[p.MOUSEBUTTONDOWN, p.KEYDOWN])
        self.next_team = team

    def begin(self):
        super().begin()
        bg = display.window.copy().convert()
        bg.set_alpha(100)
        self.background.image = bg
        pygame.mixer.music.fadeout(1000)
        if isinstance(self.next_team, ai.AI):
            self.next = AITurn()
        else:
            self.next = PlayerTurn()
        self.set_timeout(2000, self.handle_timeout)

    def handle_timeout(self, _event):
        self.done = True

    def handle_mousebuttondown(self, event):
        if event.button == 1:
            self.done = True

    def handle_keydown(self, event):
        if event.key in [p.K_SPACE, p.K_RETURN]:
            self.done = True


class Turn(gui.LinearLayout):
    def __init__(self, **kwargs):
        super().__init__(wait=True, orientation=gui.Orientation.HORIZONTAL, **kwargs)
        self.add_children(s.loaded_map, gui.Sidebar(self, die_when_done=False))

    def begin(self):
        self.team = s.units_manager.active_team
        self.team.play_music('map')
        self.bind_keys((p.K_BACKSPACE, ), self.end_turn)

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
            self.next = rooms.Fadeout(duration=1000, next=rooms.VictoryScreen(next=rooms.Fadeout(duration=2000)))
        elif self.team.is_turn_over() and not self.next:
            self.end_turn()

    def pause_menu(self):
        menu_entries = [
            (_('Return to Game'), None),
            (_('Return to Main Menu'), self.reset),
            (_('Return to O.S.'), utils.return_to_os)
        ]
        display.darken(200)
        menu = gui.Menu(menu_entries, f.MAIN, layout=room.Layout(gravity=room.Gravity.CENTER), dismiss_callback=True,
                        clear_screen=None)
        room.run_room(menu)

    def reset(self, *_):
        room.run_room(rooms.Fadeout(1000))
        room.stop()

    def end_turn(self, *args):
        s.loaded_map.reset_selection()
        next_team = s.units_manager.switch_turn()
        self.next = NextTurnTransition(next_team)
        self.set_timeout(1000, self.mark_done)

    def end(self):
        s.loaded_map.reset_selection()


class PlayerTurn(Turn):

    def __init__(self):
        super().__init__(allowed_events=[p.MOUSEBUTTONDOWN, p.KEYDOWN, p.MOUSEMOTION])

    def end_turn(self, *args):
        if self.team.is_turn_over():
            super().end_turn()
            self.set_timeout(100, self.mark_done)
        else:
            modal = gui.Modal(_("Are you sure you want to end your turn? There are still units that can move."),
                              f.SMALL, layout=room.Layout(gravity=gui.Gravity.CENTER), dismiss_callback=True,
                              clear_screen=None)
            room.run_room(modal)
            if modal.answer:
                super().end_turn()
                self.set_timeout(100, self.mark_done)


class AITurn(Turn):

    def begin(self):
        super().begin()
        self.actions = iter(self.team)

    def loop(self, _events, dt):
        super().loop(_events, dt)
        if len(s.loaded_map.children) == 0 and not self.next:
            try:
                action = next(self.actions)
                s.loaded_map.do_action(action)
            except StopIteration:
                self.team.end_turn()


def main_menu():
    room.run(rooms.SplashScreen())
    room.run(rooms.Fadeout(2000))


def actual_game():
    room.run(NextTurnTransition(s.units_manager.active_team))

    s.loaded_map = None
    s.units_manager = None
    s.winner = None
    gc.collect()


def play(map_file):
    if map_file is None:
        main_menu()
    else:
        s.load_map(map_file)

    while True:
        actual_game()
        main_menu()
