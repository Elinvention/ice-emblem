import pygame
from pygame.locals import MOUSEBUTTONDOWN, KEYDOWN
import events
import room
import resources
from display import window
from colors import WHITE, BLACK
from fonts import MAIN_MENU_FONT


class SplashScreen(room.Room):
    def __init__(self):
        super().__init__()
        self.elinvention = MAIN_MENU_FONT.render("Elinvention", 1, WHITE)
        self.presents = MAIN_MENU_FONT.render(_("PRESENTS"), 1, WHITE)
        self.ticks = pygame.time.get_ticks()
        self.done = False

    def begin(self):
        resources.play_music('Beyond The Clouds (Dungeon Plunder).ogg')

    def loop(self, _events):
        return self.done

    def draw(self):
        window.fill(BLACK)
        window.blit(self.elinvention, self.elinvention.get_rect(center=window.get_rect().center))
        window.blit(self.presents, self.presents.get_rect(centery=window.get_rect().centery+MAIN_MENU_FONT.get_linesize(), centerx=window.get_rect().centerx))
        pygame.display.flip()
        events.set_allowed([MOUSEBUTTONDOWN, KEYDOWN])
        events.wait(6000)
        events.allow_all()
        self.done = True
