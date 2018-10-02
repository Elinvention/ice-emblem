from pygame.locals import MOUSEBUTTONDOWN, KEYDOWN

import gui
import resources

from fonts import MAIN_MENU
from colors import BLACK
from .main_menu import MainMenu

class SplashScreen(gui.Label):
    def __init__(self):
        super().__init__("Elinvention\n" + _("PRESENTS"), MAIN_MENU, align='center', bg_color=BLACK, layout_gravity=gui.Gravity.FILL, allowed_events=[MOUSEBUTTONDOWN, KEYDOWN])
        self.done = True

    def begin(self):
        super().begin()
        resources.play_music('Beyond The Clouds (Dungeon Plunder).ogg')

    def end(self):
        super().end()
        self.wait_event(timeout=6000)
        self.next = MainMenu()
