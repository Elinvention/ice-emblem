import pygame
import room
import gui
import events
import resources
import display
from display import window
import state as s
from rooms.settings_menu import SettingsMenu
from rooms.map_menu import MapMenu
import pygame.locals as pl
import fonts as f
import colors as c


class MainMenu(room.Room):
    def __init__(self):
        super().__init__(allowed_events=[pl.MOUSEMOTION, pl.MOUSEBUTTONDOWN, pl.KEYDOWN, events.INTERRUPT])
        self.image = resources.load_image('Ice Emblem.png')
        self.rect = self.image.get_rect()
        self.click_to_start = f.MAIN_MENU_FONT.render(_("Click to Start"), 1, c.ICE)
        self.hmenu = gui.HorizontalMenu([(_("License"), self.show_license), (_("Settings"), self.settings_menu)], f.SMALL_FONT)
        self.hmenu.rect.bottomright = window.get_size()
        self.add_child(self.hmenu)

    def begin(self):
        super().begin()
        self.bind_keys((pl.K_RETURN, pl.K_SPACE), events.post_interrupt)
        self.bind_click((1,), events.post_interrupt, self.hmenu.rect, False)

    def loop(self, _events):
        super().loop(_events)
        for event in _events:
            if event.type == events.INTERRUPT:
                return True
        return False

    def draw(self):
        window.fill(c.BLACK)
        self.rect.center = window.get_rect().center
        window.blit(self.image, self.rect)
        rect = self.click_to_start.get_rect(centery=window.get_rect().centery+200, centerx=window.get_rect().centerx)
        window.blit(self.click_to_start, rect)
        self.hmenu.rect.bottomright = window.get_size()
        super().draw()

    def end(self):
        super().end()
        window.fill(c.BLACK)
        window.blit(self.image, self.rect)

        while not s.loaded_map:
            room.run_room(MapMenu(self.image))

        pygame.mixer.music.fadeout(2000)
        display.fadeout(2000)
        pygame.mixer.music.stop() # Make sure mixer is not busy

    def show_license(self, obj, choice):
        events.new_context("License")
        gpl_image = resources.load_image('GNU GPL.jpg')
        gpl_image = pygame.transform.smoothscale(gpl_image, window.get_size())
        window.blit(gpl_image, (0, 0))
        display.flip()
        events.set_allowed([pl.MOUSEBUTTONDOWN, pl.KEYDOWN])
        events.wait(context="License")
        events.allow_all()

    def settings_menu(self, obj, choice):
        room.run_room(SettingsMenu())

