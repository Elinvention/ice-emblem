import pygame
import pygame.locals as p

import room
import gui
import rooms
import state as s
import fonts as f
import colors as c
import resources
import display


class VictoryScreen(gui.LinearLayout):
    def __init__(self, **kwargs):
        super().__init__(size=display.get_size(), allowed_events=[p.MOUSEBUTTONDOWN, p.KEYDOWN], **kwargs)

    def begin(self):
        super().begin()
        print(_("%s wins") % s.winner.name)
        pygame.event.clear()
        self.victory = gui.Label(_("%s wins!") % s.winner.name, f.MAIN_MENU, txt_color=s.winner.color)
        self.thank_you = gui.Label(_("Thank you for playing Ice Emblem!"), f.MAIN_MENU, txt_color=c.ICE)
        pygame.mixer.stop()
        resources.play_music('Victory Track.ogg', pos=1)
        self.add_children(self.victory, self.thank_you)

    def handle_keydown(self, event: pygame.event.Event):
        if event.key in [p.K_SPACE, p.K_RETURN]:
            self.done = True

    def handle_mousebuttondown(self, event: pygame.event.Event):
        if event.button == 1:
            self.done = True


if __name__ == '__main__':
    import logging
    import unit
    from gettext import gettext as _
    logging.basicConfig(level=0)
    display.initialize()
    u = unit.RandomUnitFactory.make_unit()
    s.winner = unit.Team("Red mordace", (255, 0, 0), 0, [u], u, {})
    pygame.display.set_caption("Ice Emblem VictoryScreen Test")
    room.run(rooms.Fadeout(duration=1000, next=VictoryScreen(next=rooms.Fadeout(duration=2000))))
