from pygame.locals import MOUSEBUTTONDOWN, KEYDOWN

import gui
import resources
import display
from fonts import MAIN_MENU
from colors import BLACK


class SplashScreen(gui.Label):
    def __init__(self):
        super().__init__("Elinvention\n" + _("PRESENTS"), MAIN_MENU, align='center', bg_color=BLACK, size=display.get_size(), allowed_events=[MOUSEBUTTONDOWN, KEYDOWN])
        self.done = True

    def begin(self):
        super().begin()
        resources.play_music('Beyond The Clouds (Dungeon Plunder).ogg')

    def end(self):
        super().end()
        self.wait_event(timeout=6000)
