"""

"""


import pygame

import room

import colors as c


class Label(room.Room):
    def __init__(self, format_string, font, **kwargs):
        super().__init__(**kwargs)
        self.font = font
        self.leading = kwargs.get('leading', 10)
        self.tabs = kwargs.get('tabs', 100)
        self.txt_color = kwargs.get('txt_color', c.WHITE)
        #self.align = kwargs.get('align', 'center')
        self.text = self.format_string = format_string
        self._render_text()

    def _render_text(self):
        lines = map(lambda x: x.split('\t'), self.text.split('\n'))
        self.rendered_text = [ [self.font.render(t, True, self.txt_color) for t in r] for r in lines ]

    def draw(self):
        self.fill()
        text_surf = pygame.Surface(self.text_area(), flags=pygame.SRCALPHA)
        y = 0
        for i, line in enumerate(self.rendered_text):
            x = 0
            for tab in line:
                text_surf.blit(tab, (x, y))
                x += self.tab_space(tab.get_width())
            y += self.font.get_linesize() + self.leading
        pos_rect = text_surf.get_rect(centerx=self.rect.w//2, centery=self.rect.h//2)
        self.surface.blit(text_surf, pos_rect)
        self.draw_children()
        self.valid = True

    def set_text(self, text):
        if text != self.text:
            self.text = text
            self._render_text()
            self.invalidate()
            required_w, required_h = self.full_area()
            if self.rect.w != required_w or self.rect.h != required_h:
                self.layout_request()

    def format(self, *args, **kwargs):
        text = self.format_string.format(*args, **kwargs)
        self.set_text(text)

    def tab_space(self, tab):
        return (tab // self.tabs + 1) * self.tabs

    def line_width(self, line):
        if len(line) == 1:
            return line[0].get_width()
        line_w = 0
        for tab in line:
            line_w += self.tab_space(tab.get_width())
        return line_w

    def text_area(self):
        w = 0
        for line in self.rendered_text:
            w = max(w, self.line_width(line))
        h = self.font.get_linesize() * len(self.rendered_text) + self.leading * (len(self.rendered_text) - 1)
        return w, h

    def full_area(self):
        w, h = self.text_area()
        return w + self.padding.we, h + self.padding.ns

    def measure(self, spec_width, spec_height):
        w, h = self.full_area()
        self.resolve_measure(spec_width, spec_height, w, h)
