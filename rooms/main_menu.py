import pygame
import pygame.locals as pl

import display
import gui
import resources
import fonts as f
import colors as c

from rooms.map_menu import MapMenu


FILL = gui.LayoutParams.FILL_PARENT


class MainMenu(gui.LinearLayout):
    def __init__(self):
        super().__init__(allowed_events=[pl.MOUSEMOTION, pl.MOUSEBUTTONDOWN, pl.KEYDOWN],
                         bg_color=c.BLACK, bg_image=resources.load_image('Ice Emblem.png'),
                         layout_width=FILL, layout_height=FILL,
                         spacing=50)
        self.click_to_start = gui.Label(_("Click to Start"), f.MAIN_MENU, padding=10,
                                        txt_color=c.ICE, layout_gravity=gui.Gravity.BOTTOM, die_when_done=False)
        self.hmenu = gui.HorizontalMenu([(_("License"), self.show_license), (_("Settings"), self.settings_menu)],
                                        f.SMALL, die_when_done=False, layout_gravity=gui.Gravity.BOTTOMRIGHT)
        self.add_children(self.click_to_start, self.hmenu)
        self.bind_keys((pl.K_RETURN, pl.K_SPACE), self.show_map_menu)
        self.bind_click((1,), self.show_map_menu, self.hmenu.rect, False)

    def show_map_menu(self, *_):
        self.next = MapMenu(self.bg_image)
        self.done = True

    def show_license(self, *_):
        self.next = License()
        self.done = True
        self.next.next = self

    def settings_menu(self, *_):
        self.next = SettingsMenu()
        self.done = True
        self.next.next = self


class License(gui.Image):
    def __init__(self):
        super().__init__(resources.load_image('GNU GPL.jpg'), layout_gravity=gui.Gravity.FILL, 
                         allowed_events=[pl.MOUSEBUTTONDOWN, pl.KEYDOWN], die_when_done=True)


class SettingsMenu(gui.LinearLayout):

    def __init__(self):
        super().__init__()
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

