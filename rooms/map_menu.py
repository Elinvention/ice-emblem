import pygame
import logging
import traceback

import room
import gui
import resources
import display
import colors as c
import fonts as f
import state as s


class MapMenu(room.Room):
    def __init__(self, image):
        super().__init__(size=display.get_size())
        self.image = image
        self.files = [(f, None) for f in resources.list_maps()]
        self.choose_label = gui.Label(_("Choose a map!"), f.MAIN_MENU, txt_color=c.ICE, bg_color=c.MENU_BG)
        self.menu = gui.Menu(self.files, f.MAIN, padding=(25, 25), center=display.window.get_rect().center)
        self.add_children(self.choose_label, self.menu)

    def draw(self):
        self.surface = pygame.Surface(self.rect.size)
        self.rect.center = display.get_rect().center
        self.surface.blit(self.image, self.image.get_rect(center=display.get_rect().center))
        self.choose_label.rect.top = 50
        self.choose_label.rect.centerx = self.rect.w // 2
        self.menu.rect.centerx = self.rect.w // 2
        self.menu.rect.centery = self.rect.h // 2
        super().draw()

    def loop(self, _events, dt):
        self.done = self.menu.choice is not None

    def end(self):
        super().end()
        map_path = resources.map_path(self.files[self.menu.choice][0])
        try:
            s.load_map(map_path)
        except:
            msg = _("Error while loading map \"%s\"! Please report this issue.\n%s") % (map_path, traceback.format_exc())
            logging.error(msg)
            room.run_room(gui.Dialog(msg, f.SMALL, center=display.get_rect().center))
