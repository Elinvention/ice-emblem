# -*- coding: utf-8 -*-
#
#  menu.py, Ice Emblem's menu class.
#
#  Copyright 2015 Elia Argentieri <elia.argentieri@openmailbox.org>
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.


import pygame
import pygame.locals as p

import colors as c
import room
import display
import utils


class Rect(pygame.Rect):
    def __init__(self, **kwargs):
        if 'rect' in kwargs:
            super().__init__(kwargs['rect'])
        else:
            super().__init__(0, 0, 0, 0)
        self.settings = {k: v for k, v in kwargs.items() if not k.startswith('_') and k in dir(self)}
        self.apply()

    def apply(self):
        for attr in self.settings:
            setattr(self, attr, self.settings[attr])


class TupleOp(tuple):
    def __new__(cls, *args):
        return tuple.__new__(cls, *args)
    def __add__(self, other):
        return TupleOp(x + y for x, y in zip(self, other))
    def __sub__(self, other):
        return self.__add__(-i for i in other)
    def __neg__(self):
        return TupleOp(-x for x in self)
    def __mul__(self, other):
        return TupleOp(x * other for x in self)
    def __truediv__(self, other):
        return TupleOp(x / other for x in self)
    def __floordiv__(self, other):
        return TupleOp(x // other for x in self)


class GUI(room.Room):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.kwargs = kwargs
        self.user_interacted = False
        self.rect = Rect(**kwargs)
        self._content_size = self.rect.size
        self.padding = kwargs.get('padding', (0, 0, 0, 0))

    @property
    def content_size(self):
        return self._content_size

    @content_size.setter
    def content_size(self, size):
        self._content_size = size
        self.update_size()
        if isinstance(self.parent, GUI):
            self.parent.compute_content_size()

    def compute_content_size(self):
        self.rect.apply()

    @property
    def padding(self):
        return self._padding

    @padding.setter
    def padding(self, padding):
        self._padding = padding
        if isinstance(padding, int):

            self._padding = (padding,) * 4
        elif len(padding) == 2:
            self._padding = padding * 2
        elif len(padding) == 4:
            self._padding = padding
        else:
            raise ValueError("padding shold be either an int or a couple or a quadruple")
        self.update_size()

    def update_size(self):
        self.rect.size = (self.padding[1] + self.padding[3] + self.content_size[0],
                        self.padding[0] + self.padding[2] + self.content_size[1])

    def loop(self, _events, dt):
        super().loop(_events, dt)
        return self.user_interacted

    def global_coord(self, coord):
        coord = TupleOp(coord)
        node = self.parent
        while node is not None:
            if isinstance(node, GUI):
                coord += TupleOp(node.rect.topleft)
            node = node.parent
        return coord

    def global_pos(self):
        return self.global_coord(self.rect.topleft)

    def global_rect(self):
        return pygame.Rect(self.global_pos(), self.rect.size)

    def get_pos(self):
        return self.rect.topleft

    def get_size(self):
        return self.rect.size

    def get_width(self):
        return self.rect.w

    def get_height(self):
        return self.rect.h


class Container(GUI):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bg_color = kwargs.get('bg_color', c.MENU_BG)
        self.spacing = kwargs.get('spacing', 10)
        self.align = kwargs.get('align', 'center')
        self.compute_content_size()

    def compute_content_size(self):
        size = (0, 0)
        for i, child in enumerate(self.children):
            size = (max(size[0], child.get_width()), size[1] + child.get_height() + (self.spacing if i > 0 else 0))
        self.content_size = size
        top = self.padding[1]
        for child in self.children:
            if self.align == 'center':
                child.rect.centerx = self.padding[3] + size[0] // 2
            elif self.align == 'left':
                child.rect.left = self.padding[3]
            elif self.align == 'right':
                child.rect.right = self.padding[3] + size[0]
            child.rect.top = top
            top += child.get_height() + self.spacing
        self.rect.apply()

    def add_child(self, child):
        super().add_child(child)
        self.compute_content_size()

    def add_children(self, *children):
        super().add_children(*children)
        self.compute_content_size()

    def draw(self, surface=display.window):
        container = pygame.Surface(self.rect.size).convert_alpha()
        container.fill(self.bg_color)
        super().draw(container)
        surface.blit(container, self.rect.topleft)


class Tween(Container):
    def __init__(self, change, duration, **kwargs):
        super().__init__(wait=False, **kwargs)
        self.change = TupleOp(change)
        self.duration = duration
        self.clock = 0
        self.easing = getattr(self, kwargs.get('easing', 'linear'))
        self.callback = kwargs.get('callback', None)
        self.backward = kwargs.get('backward', False)

    def begin(self):
        self.initial = TupleOp(self.rect.topleft)
        self.target = self.initial + TupleOp(self.change)

    @staticmethod
    def linear(t, initial, change, duration):
        return initial + change * t / duration

    @staticmethod
    def inQuad(t, initial, change, duration):
        return initial + change * (t / duration) ** 2

    @staticmethod
    def inCubic(t, initial, change, duration):
        return initial + change * (t / duration) ** 3

    def reset(self, *_):
        self.clock = 0
        self.done = False

    def go_backward(self):
        self.backward = not self.backward
        self.done = False

    def loop(self, _events, dt):
        super().loop(_events, dt)
        if self.clock <= 0:
            self.done = self.backward
            self.rect.topleft = self.initial
            if self.done and callable(self.callback):
                self.callback(self)
        elif self.clock < self.duration:
            self.rect.topleft = self.easing(self.clock, self.initial, self.change, self.duration)
        else:
            self.done = not self.backward
            self.rect.topleft = self.target
            if self.done and callable(self.callback):
                self.callback(self)
        self.clock = self.clock - dt if self.backward else self.clock + dt
        return self.done

class Image(GUI):
    def __init__(self, image, **kwargs):
        self.image = image
        super().__init__(size=image.get_size(), **kwargs)

    def compute_content_size(self):
        self.content_size = self.image.get_size()
        self.rect.apply()

    def draw(self, surface=display.window):
        surface.blit(self.image, self.rect)


class Menu(GUI):
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
        self.rect.apply()

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
                self.user_interacted = True
                self.callback(self)
        elif (event.key == p.K_RETURN or event.key == p.K_SPACE) and self.index is not None:
            self.choice = self.index
            self.user_interacted = True
            self.call_callback(self.index)

    def set_index(self, index):
        if index is None:
            if self.index is not None:
                txt = self.menu_entries[self.index][0]
                r = self.font.render(txt, True, self.txt_color, self.bg_color).convert_alpha()
                self.rendered_entries[self.index] = r
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

    def move_index(self, amount):
        if self.index is None:
            self.set_index(0)
        else:
            self.set_index(self.index + amount)

    def get_entry_pos(self, i):
        return self.global_coord((self.padding[3] + self.rect.x,
                self.padding[0] + self.rect.y + i * (self.font.get_linesize() + self.leading)))

    def handle_mousebuttondown(self, event):
        if event.button == 1:
            self.clicked = False
            for i, entry in enumerate(self.rendered_entries):
                rect = pygame.Rect(self.get_entry_pos(i), entry.get_size())
                if rect.collidepoint(event.pos):
                    self.clicked = True
                    self.choice = i
                    self.user_interacted = True
                    self.call_callback(i)
        elif event.button == 3:
            if self.callback is not None:
                self.choice = -1
                self.callback(self)
                self.user_interacted = True

    def handle_mousemotion(self, event):
        hover = False
        for i, entry in enumerate(self.rendered_entries):
            rect = pygame.Rect(self.get_entry_pos(i), entry.get_size())
            if rect.collidepoint(event.pos):
                self.set_index(i)
                hover = True
        if not hover:
            self.set_index(None)

    def draw(self, surface=display.window):
        tmp = pygame.Surface(self.rect.size).convert_alpha()
        tmp.fill(self.bg_color)
        linesize = self.font.get_linesize()

        for i, entry in enumerate(self.rendered_entries):
            tmp.blit(entry, (self.padding[3], i * (linesize + self.leading) + self.padding[0]))
        super().draw(tmp)
        surface.blit(tmp, self.rect)


class HorizontalMenu(Menu):
    K_INDEX_INCREASE = p.K_LEFT
    K_INDEX_DECREASE = p.K_RIGHT
    def __init__(self, menu_entries, font, **kwargs):
        super().__init__(menu_entries, font, **kwargs)

    def compute_content_size(self):
        w = 0
        for entry in self.rendered_entries:
            w += entry.get_width()
        w += self.leading * (len(self.menu_entries) - 1)
        h = self.font.get_linesize()
        self.content_size = w, h
        self.rect.apply()

    def get_entry_pos(self, index):
        x = self.padding[3] + self.rect.x
        i = 0
        while i < index:
            x += self.rendered_entries[i].get_width() + self.leading
            i += 1
        return self.global_coord((x, self.padding[0] + self.rect.y))

    def draw(self, surface=display.window):
        tmp = pygame.Surface(self.rect.size)
        tmp.fill(self.bg_color)

        x = self.padding[3]
        for i, entry in enumerate(self.rendered_entries):
            tmp.blit(entry, (x, self.padding[0]))
            x += entry.get_width() + 10

        surface.blit(tmp, self.rect)


class Button(GUI):
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


class LifeBar(GUI):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.max = kwargs.get('max', 100)
        self.value = kwargs.get('value', self.max)
        self.block_size = kwargs.get('block_size', (4, 10))
        self.blocks_per_row = kwargs.get('blocks_per_row', 30)
        self._life = pygame.Surface(self.block_size)
        self._damage = self._life.copy()
        self._life.fill(kwargs.get('life_color', c.GREEN))
        self._damage.fill(kwargs.get('damage_color', c.RED))
        self.compute_content_size()

    def compute_content_size(self):
        w = self.blocks_per_row * (self.block_size[0] + 1)
        h = (self.max // self.blocks_per_row + 1) * (self.block_size[1] + 1)
        self.content_size = w, h

    def draw(self, surface=display.window):
        for i in range(self.max):
            x = self.rect.x + (i % self.blocks_per_row) * (self.block_size[0] + 1)
            y = self.rect.y + (i // self.blocks_per_row) * (self.block_size[1] + 1)
            if i < self.value % (self.max + 1):
                surface.blit(self._life, (x, y))
            else:
                surface.blit(self._damage, (x, y))
        super().draw(surface)


class Label(GUI):
    def __init__(self, format_string, font, **kwargs):
        super().__init__(**kwargs)
        self.font = font
        self.leading = kwargs.get('leading', 10)
        self.tabs = kwargs.get('tabs', 100)
        self.txt_color = kwargs.get('txt_color', c.WHITE)
        self.bg_color = kwargs.get('bg_color', c.MENU_BG)
        self.format_string = format_string
        self.set_text(format_string)

    def draw(self, surface=display.window):
        tmp = pygame.Surface(self.rect.size).convert_alpha()
        tmp.fill(self.bg_color)
        for i, line in enumerate(self.rendered_text):
            y = self.padding[0] + i * (self.font.get_linesize() + self.leading)
            x = self.padding[1]
            for tab in line:
                tmp.blit(tab, (x, y))
                x += self.tab_space(tab.get_width())
        self.draw_children(tmp)
        surface.blit(tmp, self.rect)

    def set_text(self, text):
        lines = map(lambda x: x.split('\t'), text.split('\n'))
        self.rendered_text = [ [self.font.render(t, True, self.txt_color) for t in r] for r in lines ]
        self.compute_content_size()

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


class Dialog(Container):
    def __init__(self, text, font, **kwargs):
        super().__init__(**kwargs)
        self.ok = False
        self.label = Label(text, font)
        self.ok_btn = Button("OK", font, callback=self.dismiss)
        self.callback = kwargs.get('callback', None)
        self.add_children(self.label, self.ok_btn)

    def dismiss(self, *_):
        self.ok = True
        if callable(self.callback):
            self.callback(self)

    def loop(self, _events, dt):
        return self.ok

    def set_text(self, text):
        self.label.set_text(text)
        self.ok_btn.rect.midbottom = self.rect.midbottom
        self.compute_content_size()


class Modal(Container):
    def __init__(self, text, font, **kwargs):
        super().__init__(**kwargs)
        self.callback = kwargs.get('callback', None)
        self.answer = None
        self.label = Label(text, font)
        self.yesno = HorizontalMenu([("Yes", self.yes), ("No", self.no)], font)
        self.add_children(self.label, self.yesno)

    def yes(self, *_):
        self.answer = True
        if callable(self.callback):
            self.callback(self, self.answer)

    def no(self, *_):
        self.answer = False
        if callable(self.callback):
            self.callback(self, self.answer)

    def handle_keydown(self, event):
        if event.key == p.K_SPACE:
            self.answer = self.yesno.choice == 0

    def loop(self, _events, dt):
        return self.answer is not None


if __name__ == '__main__':
    import logging
    logging.basicConfig(level=0)
    pygame.init()
    screen = pygame.display.set_mode((1280, 720), pygame.RESIZABLE)
    pygame.display.set_caption("Ice Emblem GUI Test")

    f = pygame.font.SysFont("Liberation Sans", 24)
    d = Dialog("Dialog\nLorem ipsum dolor sit amet.\n\nTROLOL", f, callback=lambda self: self.set_text("Hai premuto OK"), x=50, y=100)
    l = Label("TEST LABEL\nTEST\tTAB\nTAB\tTAB\tTAB\n\n\n\tTROLOL", f, x=50, y=400)
    a = Label("NO ANSWER", f)
    m = Modal("Modal\nRispondi SI o NO?\n\nFORSE?", f, callback=lambda _,ans: a.set_text("SI" if ans else "NO"), x=800, y=100)
    a.rect.topleft = m.rect.bottomleft
    a.rect.top += 10
    q = Button("Quit", f, callback=utils.return_to_os)
    cb = CheckBox("Click here to toggle", f, False, callback=lambda obj, chk: obj.set_text(str(chk)), x=800, y=50)

    lh = Label("SELEZIONA DAL MENU", f)
    h = HorizontalMenu([(c, lambda _,choice: lh.set_text(choice)) for c in "Horizontal"], f)
    lv = Label("SELEZIONA DAL MENU", f, bg_color=c.RED)
    v = Menu([(c, lambda _,choice: lv.set_text(choice)) for c in "VERTICAL"], f, padding=(10, 60), leading=0, bg_color=c.BLUE)
    container = Container(children=(h, lh, v, lv), x=400, y=300)

    size, ti = (1000, 0), 10000
    tween_test = [Tween(size, ti, easing=e, children=[Label(e, f, bg_color=c.RED)], callback=lambda s: s.go_backward()) for e in Tween.__dict__ if isinstance(Tween.__dict__[e], staticmethod)]

    class GUITest(room.Room):
        def __init__(self, **kwargs):
            super().__init__(wait=False, **kwargs)
            #self.add_children(d, l, m, a, q, cb, container)
            self.add_child(Container(w=size[0], center=display.get_rect().center, align='left', children=tween_test))
        def draw(self):
            screen.fill(c.BLACK)
            super().draw()

    room.run_room(GUITest())

    if m.answer is not None:
        print("Answer: %s" % m.answer)

    pygame.quit()

