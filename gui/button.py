"""

"""


import pygame

import room
import colors as c


class Button(room.Room):
    def __init__(self, text, font, **kwargs):
        super().__init__(**kwargs)
        self.font = font
        self.clicked = False
        self._focus = False
        self.callback = kwargs.get('callback', None)
        self.txt_color = kwargs.get('txt_color', c.ICE)
        self.sel_color = kwargs.get('sel_color', c.MENU_SEL)
        self.set_text(text)

    def set_text(self, text):
        self.text = text
        self.rendered_text = self.font.render(text, True, self.txt_color,
                                              self.sel_color if self._focus else self.background.color)
        self.layout_request()

    def measure(self, spec_width, spec_height):
        self.resolve_measure(spec_width, spec_height, *self.rendered_text.get_size())

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
            self.invalidate()

    def unfocus(self):
        if self._focus:
            self.rendered_text = self.font.render(self.text, True, self.txt_color, self.background.color)
            self._focus = False
            self.invalidate()

    def is_focused(self):
        return self._focus

    def handle_mousebuttondown(self, event):
        if event.button == 1:
            if self.global_rect().collidepoint(event.pos):
                if self.callback is not None:
                    self.callback(self)
                self.clicked = True

    def draw(self):
        self.fill()
        self.surface.blit(self.rendered_text, (self.padding[3], self.padding[0]))
        self.draw_children()
        self.valid = True


class CheckBox(Button):
    def __init__(self, text, font, checked=False, **kwargs):
        super().__init__(text, font, **kwargs)
        self.checked = checked

    def measure(self, spec_width, spec_height):
        w = self.rendered_text.get_width() + self.rendered_text.get_height()
        self.resolve_measure(spec_width, spec_height, w + self.padding.we,
                             self.rendered_text.get_height() + self.padding.ns)

    def handle_mousebuttondown(self, event):
        if event.button == 1:
            if self.global_rect().collidepoint(event.pos):
                self.checked = not self.checked
                if self.callback is not None:
                    self.callback(self, self.checked)
                self.clicked = True
                self.handle_mousemotion(event)

    def draw(self):
        self.fill()
        btn_pos = (self.padding[3] + self.rendered_text.get_height(), self.padding[0])
        self.surface.blit(self.rendered_text, btn_pos)
        checkbox = pygame.Surface((self.rendered_text.get_height(),) * 2)
        if self.checked:
            checkbox.fill(c.GREEN)
        else:
            checkbox.fill(c.RED)
        self.surface.blit(checkbox, (self.padding[3], self.padding[0]))
        self.draw_children()
        self.valid = True
