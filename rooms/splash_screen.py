"""

"""


import pygame
from pygame.locals import MOUSEBUTTONDOWN, KEYDOWN

import gui
import resources

from fonts import MAIN_MENU
from colors import BLACK
from room import Background
from .main_menu import MainMenu


class SplashScreen(gui.Label):
    def __init__(self):
        super().__init__("Elinvention\n" + _("PRESENTS"), MAIN_MENU, background=Background(color=BLACK),
                         allowed_events=[MOUSEBUTTONDOWN, KEYDOWN])

    def begin(self):
        super().begin()
        resources.play_music('Beyond The Clouds (Dungeon Plunder).ogg')
        self.set_timeout(6000, self.handle_timeout)
        self.next = MainMenu()

    def handle_timeout(self, event):
        self.done = True

    def handle_mousebuttondown(self, event):
        if event.button == 1:
            self.done = True

    def handle_keydown(self, event):
        if event.key in (pygame.K_SPACE, pygame.K_RETURN):
            self.done = True
