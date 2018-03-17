import pygame
import room
import gui
import display
import events
import pygame.locals as pl
import colors as c
import fonts as f


class SettingsMenu(room.Room):

    def __init__(self):
        super().__init__()
        self.back_btn = gui.Button(_("Go Back"), f.MAIN_FONT, callback=lambda *_: setattr(self, 'done', True))
        self.fullscreen_btn = gui.CheckBox(_("Toggle Fullscreen"), f.MAIN_FONT, callback=lambda _, _a: display.toggle_fullscreen())
        def res_setter(res):
            return lambda *_: display.set_resolution(res)
        resolutions = [("{0[0]}x{0[1]}".format(res), res_setter(res)) for res in pygame.display.list_modes()]
        self.resolutions_menu = gui.Menu(resolutions, f.MAIN_FONT)
        self.add_children(self.back_btn, self.fullscreen_btn, self.resolutions_menu)

    def begin(self):
        super().begin()
        self.bind_keys((pl.K_ESCAPE,), lambda *_: setattr(self, 'done', True))

    def draw(self):
        window = display.window
        window.fill(c.BLACK)
        self.back_btn.rect.bottomright = window.get_size()
        self.fullscreen_btn.rect.midtop = window.get_rect(top=50).midtop
        self.resolutions_menu.rect.midtop = window.get_rect(top=100).midtop
        super().draw()
