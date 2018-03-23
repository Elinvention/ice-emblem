"""

"""


import pygame.locals as p

from .container import Container
from .label import Label
from .button import Button
from .menu import HorizontalMenu


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
