"""

"""


import pygame
import pygame.locals as p

import gui
import colors as c


class Menu(gui.GUI):
    K_INDEX_INCREASE = p.K_DOWN
    K_INDEX_DECREASE = p.K_UP

    def __init__(self, menu_entries, font, **kwargs):
        super().__init__(**kwargs)
        self.font = font
        self.callback = kwargs.get('callback', None)
        self.txt_color = kwargs.get('txt_color', c.ICE)
        self.sel_color = kwargs.get('sel_color', c.MENU_SEL)
        self.bg_color = kwargs.get('bg_color', c.MENU_BG)
        self.leading = kwargs.get('leading', 10)

        self.menu_entries = menu_entries

        self.prev_index = self.index = None
        self.choice = None
        self.clicked = False  # tells wether latest click was on menu

    def __getitem__(self, key):
        return self.menu_entries[key]

    def compute_content_size(self):
        w = 0
        for entry in self.rendered_entries:
            w = max(w, entry.get_width())
        h = self.font.get_linesize() * len(self.menu_entries) + self.leading * (len(self.menu_entries) - 1)
        self.content_size = w, h
        self.invalidate()

    @property
    def menu_entries(self):
        return self._menu_entries

    @menu_entries.setter
    def menu_entries(self, entries):
        self._menu_entries = entries
        self.rendered_entries = [self.font.render(entry[0], True, self.txt_color).convert_alpha() for entry in entries]
        self.compute_content_size()
        self.prev_index = self.index = None

    def call_callback(self, i):
        callback = self.menu_entries[i][1]
        if callable(callback):
            callback(self, self.menu_entries[i][0])

    def handle_keydown(self, event):
        if event.key == self.K_INDEX_DECREASE:
            self.move_index(-1)
        elif event.key == self.K_INDEX_INCREASE:
            self.move_index(1)
        elif event.key == p.K_ESCAPE:
            if self.callback is not None:
                self.choice = -1
                self.done = True
                self.callback(self, None)
        elif (event.key == p.K_RETURN or event.key == p.K_SPACE) and self.index is not None:
            self.choice = self.index
            self.done = True
            self.call_callback(self.index)

    def set_index(self, index):
        if index is None:
            if self.index is not None:
                txt = self.menu_entries[self.index][0]
                r = self.font.render(txt, True, self.txt_color, self.bg_color).convert_alpha()
                self.rendered_entries[self.index] = r
                self.invalidate()
            self.prev_index = self.index
            self.index = None
            return

        self.prev_index = self.index
        self.index = index % len(self.menu_entries)

        if self.index != self.prev_index:
            for i, entry in enumerate(self.menu_entries):
                entry_text, entry_callback = entry
                if i == self.index:
                    render = self.font.render(entry_text, True, self.txt_color, self.sel_color).convert_alpha()
                    self.rendered_entries[i] = render
                elif i == self.prev_index:
                    render = self.font.render(entry_text, True, self.txt_color, self.bg_color).convert_alpha()
                    self.rendered_entries[i] = render
            self.invalidate()

    def move_index(self, amount):
        if self.index is None:
            self.set_index(0)
        else:
            self.set_index(self.index + amount)

    def get_entry_pos(self, i):
        return self.global_coord((self.padding[3],
                self.padding[0] + i * (self.font.get_linesize() + self.leading)))

    def handle_mousebuttondown(self, event):
        if event.button == 1:
            self.clicked = False
            for i, entry in enumerate(self.rendered_entries):
                rect = pygame.Rect(self.get_entry_pos(i), entry.get_size())
                if rect.collidepoint(event.pos):
                    self.clicked = True
                    self.choice = i
                    self.done = True
                    self.call_callback(i)
        elif event.button == 3:
            if self.callback is not None:
                self.choice = -1
                self.callback(self, None)
                self.done = True

    def handle_mousemotion(self, event):
        hover = False
        for i, entry in enumerate(self.rendered_entries):
            rect = pygame.Rect(self.get_entry_pos(i), entry.get_size())
            if rect.collidepoint(event.pos):
                self.set_index(i)
                hover = True
                break
        if not hover:
            self.set_index(None)

    def draw(self):
        self.surface.fill(self.bg_color)
        linesize = self.font.get_linesize()
        for i, entry in enumerate(self.rendered_entries):
            self.surface.blit(entry, (self.padding[3], i * (linesize + self.leading) + self.padding[0]))
        super().draw()


class HorizontalMenu(Menu):
    K_INDEX_INCREASE = p.K_RIGHT
    K_INDEX_DECREASE = p.K_LEFT
    def __init__(self, menu_entries, font, **kwargs):
        super().__init__(menu_entries, font, **kwargs)

    def compute_content_size(self):
        w = 0
        for entry in self.rendered_entries:
            w += entry.get_width()
        w += self.leading * (len(self.menu_entries) - 1)
        h = self.font.get_linesize()
        self.content_size = w, h

    def get_entry_pos(self, index):
        x = self.padding[3]
        for i in range(index):
            x += self.rendered_entries[i].get_width() + self.leading
        return self.global_coord((x, self.padding[0]))

    def draw(self):
        self.surface.fill(self.bg_color)
        x = self.padding[3]
        for i, entry in enumerate(self.rendered_entries):
            self.surface.blit(entry, (x, self.padding[0]))
            x += entry.get_width() + self.leading
        super(gui.GUI, self).draw()
