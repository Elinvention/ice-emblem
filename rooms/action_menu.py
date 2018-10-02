import pygame

import room
import gui
from fonts import SMALL


class AttackSelect(room.Room):
    def begin(self):
        super().begin()
        self.parent.prepare_attack()

    def handle_mousebuttondown(self, event):
        # user must click on an enemy unit
        if event.button == 1 and self.parent.is_attack_click(event.pos):
            self.parent.prev_sel = self.parent.curr_sel
            self.parent.curr_sel = self.parent.tilemap.index_at(*event.pos)
            self.parent.attack()
            self.done = True
        elif event.button == 3:
            self.parent.move_undo()
            self.done = True
        return True  # prevent event propagation to parent

    def handle_keydown(self, event):
        # user must choose an enemy unit
        self.parent.cursor.update(event)
        if event.key == pygame.K_SPACE and self.parent.is_enemy_cursor():
            self.parent.prev_sel = self.parent.curr_sel
            self.parent.curr_sel = self.parent.cursor.coord
            self.parent.attack()
            self.done = True
        elif event.key == pygame.K_ESCAPE:
            self.parent.move_undo()
            self.done = True
        self.parent.invalidate()
        return True  # prevent event propagation to parent


class ActionMenu(gui.Menu):
    """
    Shows the action menu and handles input until it is dismissed.
    """

    def __init__(self, **kwargs):
        super().__init__([], SMALL, dismiss_callback=self.undo, **kwargs)

    def menu_attack(self):
        self.parent.add_child(AttackSelect())

    def menu_items(self):
        unit = self.parent.curr_unit
        def setitem(item):
            def set(*args):
                unit.items.active = item
                unit.played = True
                self.parent.reset_selection()
            return set
        self.menu_entries = [(i.name, setitem(i)) for i in unit.items]
        self.done = False

    def menu_wait(self):
        self.parent.curr_unit.wait()
        self.parent.reset_selection()

    def undo(self, *args):
        self.visible = False
        self.parent.move_undo()

    def handle_mousemotion(self, event):
        super().handle_mousemotion(event)
        return True  # prevent event propagation to parent

    def handle_mousebuttondown(self, event):
        super().handle_mousebuttondown(event)
        return True  # prevent event propagation to parent

    def handle_keydown(self, event):
        super().handle_keydown(event)
        return True  # prevent event propagation to parent

    def begin(self):
        super().begin()
        self.menu_entries = [
            (_("Attack"), lambda *_: self.menu_attack()),
            (_("Items"), lambda *_: self.menu_items()),
            (_("Wait"), lambda *_: self.menu_wait()),
        ] if len(self.parent.nearby_enemies()) > 0 else [
            (_("Items"), lambda *_: self.menu_items()),
            (_("Wait"), lambda *_: self.menu_wait()),
        ]

