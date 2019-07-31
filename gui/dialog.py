"""

"""


import pygame.locals as p

from .container import LinearLayout
from .label import Label
from .button import Button
from .menu import HorizontalMenu


class Dialog(LinearLayout):
    def __init__(self, text, font, **kwargs):
        super().__init__(**kwargs)
        self.label = Label(text, font)
        self.ok_btn = Button("OK", font, callback=self.dismiss, die_when_done=False)
        self.callback = kwargs.get('callback', None)
        self.add_children(self.label, self.ok_btn)

    def dismiss(self, *_):
        self.done = True
        self.call_callback()

    def call_callback(self):
        if callable(self.callback):
            self.callback(self)

    def set_text(self, text):
        self.label.set_text(text)


class Modal(LinearLayout):
    def __init__(self, text, font, **kwargs):
        super().__init__(**kwargs)
        self.callback = kwargs.get('callback', None)
        self.answer = None
        self.label = Label(text, font)
        self.yesno = HorizontalMenu([("Yes", self.yes), ("No", self.no)], font, die_when_done=False)
        self.add_children(self.label, self.yesno)

    def yes(self, *_):
        self.answer = True
        self.done = True
        self.call_callback()

    def no(self, *_):
        self.answer = False
        self.done = True
        self.call_callback()

    def call_callback(self):
        if callable(self.callback):
            self.callback(self, self.answer)

    def handle_keydown(self, event):
        if event.key == p.K_SPACE:
            self.answer = self.yesno.choice == 0
            self.done = True
