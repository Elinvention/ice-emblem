import logging
import traceback
import pygame

import room
import rooms
import gui
import resources
import colors as c
import fonts as f
import state as s

from room import Gravity, Layout, LayoutParams


class MapMenu(gui.LinearLayout):
    def __init__(self, background):
        super().__init__(layout=Layout(width=LayoutParams.FILL_PARENT, height=LayoutParams.FILL_PARENT),
                         default_child_gravity=Gravity.CENTER, background=background)

        def map_file_closure(file):
            return lambda m, _: self.chosen(m, file)

        self.files = [(map_name, map_file_closure(file)) for file, map_name in resources.list_maps()]
        self.choose_label = gui.Label(_("Choose a map!"), f.MAIN_MENU, txt_color=c.ICE)
        self.menu = gui.Menu(self.files, f.MAIN, padding=(25, 25), die_when_done=False)
        self.back_btn = gui.Button(_("Go Back"), f.MAIN, callback=self.back, layout=Layout(gravity=Gravity.BOTTOMRIGHT))
        self.add_children(self.choose_label, self.menu, self.back_btn)

    def back(self, *_):
        self.done = True
        self.next = rooms.MainMenu()

    def chosen(self, menu, choice):
        map_path = resources.map_path(choice)
        try:
            s.load_map(map_path)
        except:
            msg = _("Error while loading map \"%s\"! Please report this issue.\n\n%s") % (
            map_path, traceback.format_exc())
            logging.error(msg)
            dialog = gui.Dialog(msg, f.MONOSPACE, layout=Layout(gravity=Gravity.FILL), padding=25)
            room.run_room(dialog)
        else:
            self.done = True

    def handle_mousebuttondown(self, event: pygame.event.Event):
        if event.button == pygame.BUTTON_RIGHT:
            self.back()
