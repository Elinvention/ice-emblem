"""

"""


import pygame
from pygame.locals import MOUSEBUTTONDOWN, KEYDOWN

import gui
import resources
from events import TIMEOUT

from fonts import MAIN_MENU
from colors import BLACK
from .main_menu import MainMenu


class SplashScreen(gui.Label):
    def __init__(self):
        super().__init__("Elinvention\n" + _("PRESENTS"), MAIN_MENU, bg_color=BLACK,
                         allowed_events=[MOUSEBUTTONDOWN, KEYDOWN])

    def begin(self):
        super().begin()
        resources.play_music('Beyond The Clouds (Dungeon Plunder).ogg')
        pygame.time.set_timer(TIMEOUT, 6000)
        self.next = MainMenu()

    def handle_userevent(self, event):
        if event.type == TIMEOUT:
            self.done = True

    def handle_mousebuttondown(self, event):
        if event.button == 1:
            self.done = True

    def handle_keydown(self, event):
        if event.key in (pygame.K_SPACE, pygame.K_RETURN):
            self.done = True

    def end(self):
        super().end()
        pygame.time.set_timer(TIMEOUT, 0)
