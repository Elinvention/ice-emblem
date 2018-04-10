"""

"""


import gui
import colors as c

from basictypes import Point


class Label(gui.GUI):
    def __init__(self, format_string, font, **kwargs):
        super().__init__(**kwargs)
        self.font = font
        self.leading = kwargs.get('leading', 10)
        self.tabs = kwargs.get('tabs', 100)
        self.txt_color = kwargs.get('txt_color', c.WHITE)
        self.bg_color = kwargs.get('bg_color', c.MENU_BG)
        self.align = kwargs.get('align', 'center')
        self.text = self.format_string = format_string
        self._render_text()

    def draw(self):
        self.surface.fill(self.bg_color)
        offset = Point((0, 0))
        if self.align == 'center':
            offset = (Point(self.rect.size) - Point(self.content_size)) / 2
        y = self.padding[0] + offset.y
        for i, line in enumerate(self.rendered_text):
            x = self.padding[1] + offset.x
            for tab in line:
                self.surface.blit(tab, (x, y))
                x += self.tab_space(tab.get_width())
            y += self.font.get_linesize() + self.leading
        super().draw()

    def _render_text(self):
        lines = map(lambda x: x.split('\t'), self.text.split('\n'))
        self.rendered_text = [ [self.font.render(t, True, self.txt_color) for t in r] for r in lines ]
        self.compute_content_size()

    def set_text(self, text):
        if text != self.text:
            self.text = text
            self._render_text()

    def format(self, *args, **kwargs):
        text = self.format_string.format(*args, **kwargs)
        self.set_text(text)

    def tab_space(self, tab):
        return (tab // self.tabs + 1) * self.tabs

    def compute_content_size(self):
        w = max((sum((self.tab_space(t.get_width()) for t in l)) if len(l) > 1 else l[0].get_width() for l in self.rendered_text))
        h = self.font.get_linesize() * len(self.rendered_text) + self.leading * (len(self.rendered_text) - 1)
        self.content_size = w, h
        self.rect.apply()
