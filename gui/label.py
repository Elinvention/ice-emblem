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
        y = self.padding.n
        for i, line in enumerate(self.rendered_text):
            x = self.padding.w
            for tab in line:
                self.surface.blit(tab, (x, y))
                x += self.tab_space(tab.get_width())
            y += self.font.get_linesize() + self.leading
        self.draw_children()
        self.valid = True

    def set_text(self, text):
        if text != self.text:
            self.text = text
            self._render_text()
            self.invalidate()
            self.layout_request()

    def format(self, *args, **kwargs):
        text = self.format_string.format(*args, **kwargs)
        self.set_text(text)

    def tab_space(self, tab):
        return (tab // self.tabs + 1) * self.tabs

    def measure(self, spec_width, spec_height):
        w = max((sum((self.tab_space(t.get_width()) for t in l)) if len(l) > 1 else l[0].get_width() for l in self.rendered_text))
        h = self.font.get_linesize() * len(self.rendered_text) + self.leading * (len(self.rendered_text) - 1)
        self.resolve_measure(spec_width, spec_height, w + self.padding.we, h + self.padding.ns)
