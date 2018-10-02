import pygame

import gui
import display
import pygame.locals as pl
import fonts as f


class SettingsMenu(gui.Container):

    def __init__(self):
        super().__init__(layout_gravity=gui.Gravity.FILL)
        self.back_btn = gui.Button(_("Go Back"), f.MAIN, callback=lambda *_: setattr(self, 'done', True), layout_gravity=gui.Gravity.BOTTOMRIGHT)
        self.fullscreen_btn = gui.CheckBox(_("Toggle Fullscreen"), f.MAIN, callback=lambda *_: display.toggle_fullscreen(), padding=25)
        def res_setter(res):
            return lambda *_: display.set_resolution(res)
        resolutions = [("{0[0]}x{0[1]}".format(res), res_setter(res)) for res in pygame.display.list_modes()]
        self.resolutions_menu = gui.Menu(resolutions, f.MAIN, die_when_done=False)
        self.add_children(self.back_btn, self.fullscreen_btn, self.resolutions_menu)

    def handle_keydown(self, event):
        if event.key == pl.K_ESCAPE:
            self.done = True
