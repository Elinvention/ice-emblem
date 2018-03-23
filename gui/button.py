"""

"""


import pygame

import gui
import colors as c
import display


class Button(gui.GUI):
    def __init__(self, text, font, **kwargs):
        super().__init__(**kwargs)
        self.font = font
        self.clicked = False
        self._focus = False
        self.callback = kwargs.get('callback', None)
        self.txt_color = kwargs.get('txt_color', c.ICE)
        self.sel_color = kwargs.get('sel_color', c.MENU_SEL)
        self.bg_color = kwargs.get('bg_color', c.MENU_BG)
        self.set_text(text)

    def set_text(self, text):
        self.text = text
        self.rendered_text = self.font.render(text, True, self.txt_color, self.sel_color if self._focus else self.bg_color)
        self.compute_content_size()

    def compute_content_size(self):
        self.content_size = self.rendered_text.get_size()
        self.rect.apply()

    def loop(self, _events, dt):
        return self.clicked

    def handle_mousemotion(self, event):
        if self.global_rect().collidepoint(event.pos):
            self.focus()
        else:
            self.unfocus()

    def focus(self):
        if not self._focus:
            self.rendered_text = self.font.render(self.text, True, self.txt_color, self.sel_color)
            self._focus = True

    def unfocus(self):
        if self._focus:
            self.rendered_text = self.font.render(self.text, True, self.txt_color, self.bg_color)
            self._focus = False

    def is_focused(self):
        return self._focus

    def handle_mousebuttondown(self, event):
        if event.button == 1:
            if self.global_rect().collidepoint(event.pos):
                if self.callback is not None:
                    self.callback(self)
                self.clicked = True

    def draw(self, surface=display.window):
        btn = pygame.Surface(self.rect.size)
        btn.fill(self.bg_color)
        btn.blit(self.rendered_text, (self.padding[3], self.padding[0]))
        surface.blit(btn, self.rect.topleft)


class CheckBox(Button):
    def __init__(self, text, font, checked=False, **kwargs):
        super().__init__(text, font, **kwargs)
        self.checked = checked
        self.compute_content_size()

    def compute_content_size(self):
        super().compute_content_size()
        self.content_size = (self.content_size[0] + self.content_size[1], self.content_size[1])
        self.rect.apply()

    def handle_mousebuttondown(self, event):
        if event.button == 1:
            if self.global_rect().collidepoint(event.pos):
                self.checked = not self.checked
                if self.callback is not None:
                    self.callback(self, self.checked)
                self.clicked = True
                self.handle_mousemotion(event)

    def draw(self, surface=display.window):
        btn = pygame.Surface(self.rect.size)
        btn.fill(self.bg_color)
        btn_pos = (self.padding[3] + self.content_size[1], self.padding[0])
        btn.blit(self.rendered_text, btn_pos)
        checkbox = pygame.Surface((self.content_size[1],) * 2)
        if self.checked:
            checkbox.fill(c.GREEN)
        else:
            checkbox.fill(c.RED)
        btn.blit(checkbox, (self.padding[3], self.padding[0]))
        surface.blit(btn, self.rect.topleft)
