import pygame
from pygame.locals import MOUSEBUTTONDOWN, KEYDOWN

import room
import resources
from display import window
from colors import WHITE, BLACK
from fonts import MAIN_MENU_FONT


class SplashScreen(room.Room):
    def __init__(self):
        super().__init__(allowed_events=[MOUSEBUTTONDOWN, KEYDOWN])
        self.elinvention = MAIN_MENU_FONT.render("Elinvention", 1, WHITE)
        self.presents = MAIN_MENU_FONT.render(_("PRESENTS"), 1, WHITE)

    def begin(self):
        resources.play_music('Beyond The Clouds (Dungeon Plunder).ogg')

    def draw(self):
        window.fill(BLACK)
        window.blit(self.elinvention, self.elinvention.get_rect(center=window.get_rect().center))
        window.blit(self.presents, self.presents.get_rect(centery=window.get_rect().centery+MAIN_MENU_FONT.get_linesize(), centerx=window.get_rect().centerx))
        pygame.display.flip()
        self.wait_event(timeout=6000)
        self.done = True
