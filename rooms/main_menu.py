import pygame.locals as pl

import room
import gui
import resources
import fonts as f
import colors as c

from rooms.settings_menu import SettingsMenu
from rooms.map_menu import MapMenu


class MainMenu(gui.Container):
    def __init__(self):
        super().__init__(layout_gravity=gui.Gravity.FILL, allowed_events=[pl.MOUSEMOTION, pl.MOUSEBUTTONDOWN, pl.KEYDOWN], bg_color=c.BLACK, bg_image=resources.load_image('Ice Emblem.png'), spacing=50)
        self.click_to_start = gui.Label(_("Click to Start"), f.MAIN_MENU, bg_color=c.TRANSPARENT, txt_color=c.ICE, layout_gravity=gui.Gravity.BOTTOM)
        self.hmenu = gui.HorizontalMenu([(_("License"), self.show_license), (_("Settings"), self.settings_menu)], f.SMALL, die_when_done=False, layout_gravity=gui.Gravity.BOTTOMRIGHT)
        self.add_children(self.click_to_start, self.hmenu)
        self.bind_keys((pl.K_RETURN, pl.K_SPACE), lambda *_: setattr(self, 'done', True))
        self.bind_click((1,), lambda *_: setattr(self, 'done', True), self.hmenu.rect, False)

    def end(self):
        super().end()
        self.next = MapMenu(self.bg_image)

    def show_license(self, *_):
        room.run_room(License())

    def settings_menu(self, *_):
        room.run_room(SettingsMenu())


class License(gui.Container):
    def __init__(self):
        super().__init__(layout_gravity=gui.Gravity.FILL, allowed_events=[pl.MOUSEBUTTONDOWN, pl.KEYDOWN], bg_image=resources.load_image('GNU GPL.jpg'))

    def handle_keydown(self, _event):
        self.done = True

    def handle_mousebuttondown(self, _event):
        self.done = True
