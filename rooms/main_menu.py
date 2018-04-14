import pygame
import pygame.locals as pl

import room
import rooms
import gui
import events
import resources
import display
from display import window
import state as s
import fonts as f
import colors as c

from rooms.settings_menu import SettingsMenu
from rooms.map_menu import MapMenu




class MainMenu(room.Room):
    def __init__(self):
        super().__init__(size=display.get_size(), allowed_events=[pl.MOUSEMOTION, pl.MOUSEBUTTONDOWN, pl.KEYDOWN])
        self.image = resources.load_image('Ice Emblem.png')
        self.click_to_start = gui.Label(_("Click to Start"), f.MAIN_MENU, bg_color=c.TRANSPARENT, txt_color=c.ICE)
        self.hmenu = gui.HorizontalMenu([(_("License"), self.show_license), (_("Settings"), self.settings_menu)], f.SMALL)
        self.add_children(self.click_to_start, self.hmenu)

    def begin(self):
        super().begin()
        self.bind_keys((pl.K_RETURN, pl.K_SPACE), lambda *_: setattr(self, 'done', True))
        self.bind_click((1,), lambda *_: setattr(self, 'done', True), self.hmenu.rect, False)

    def draw(self):
        self.surface = pygame.Surface(self.rect.size)
        self.rect.center = window.get_rect().center
        self.surface.blit(self.image, self.image.get_rect(center=display.get_rect().center))
        self.click_to_start.rect.centery = self.surface.get_rect().centery + 200
        self.click_to_start.rect.centerx = self.surface.get_rect().centerx
        self.hmenu.rect.bottomright = self.surface.get_size()
        super().draw()

    def end(self):
        super().end()
        window.fill(c.BLACK)
        window.blit(self.image, self.rect)

        while not s.loaded_map:
            room.run_room(MapMenu(self.image))

        room.run_room(rooms.Fadeout(2000))

    def show_license(self, obj, choice):
        gpl_image = resources.load_image('GNU GPL.jpg')
        gpl_image = pygame.transform.smoothscale(gpl_image, window.get_size())
        window.blit(gpl_image, (0, 0))
        display.flip()
        events.set_allowed([pl.MOUSEBUTTONDOWN, pl.KEYDOWN])
        events.wait()
        events.set_allowed(self.allowed_events)

    def settings_menu(self, obj, choice):
        room.run_room(SettingsMenu())

