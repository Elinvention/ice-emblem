"""

"""


import colors as c
import gui


class Container(gui.GUI):
    def __init__(self, **kwargs):
        self.bg_color = kwargs.get('bg_color', c.MENU_BG)
        self.spacing = kwargs.get('spacing', 10)
        self.align = kwargs.get('align', 'center')
        super().__init__(**kwargs)
        self.compute_content_size()

    def compute_content_size(self):
        size = (0, 0)
        for i, child in enumerate(self.children):
            size = (max(size[0], child.rect.w), size[1] + child.rect.h + (self.spacing if i > 0 else 0))
        self.content_size = size
        self.reflow()

    def reflow(self):
        size = self.content_size
        top = self.padding[1]
        for child in self.children:
            child.rect.top = top
            top += child.rect.h + self.spacing
            if isinstance(child, gui.Tween) and child.playing:
                continue
            if self.align == 'center':
                child.rect.centerx = self.padding[3] + size[0] // 2
            elif self.align == 'left':
                child.rect.left = self.padding[3]
            elif self.align == 'right':
                child.rect.right = self.padding[3] + size[0]
        self.invalidate()

    def add_child(self, child):
        super().add_child(child)
        self.compute_content_size()

    def add_children(self, *children):
        super().add_children(*children)
        self.compute_content_size()

    def remove_child(self, child):
        super().remove_child(child)
        self.compute_content_size()

    def draw(self):
        self.surface.fill(self.bg_color)
        super().draw()
