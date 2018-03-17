import pygame

import room
import rooms
import pygame.locals as p
import state as s
import fonts as f
import colors as c
import resources
import display


class VictoryScreen(room.Room):
    def __init__(self):
        super().__init__(allowed_events=[p.MOUSEBUTTONDOWN, p.KEYDOWN])

    def begin(self):
        super().begin()
        print(_("%s wins") % s.winner.name)
        pygame.event.clear()
        self.victory = f.MAIN_MENU_FONT.render(s.winner.name + ' wins!', 1, s.winner.color)
        self.thank_you = f.MAIN_MENU_FONT.render(_('Thank you for playing Ice Emblem!'), 1, c.ICE)
        pygame.mixer.stop()
        resources.play_music('Victory Track.ogg')
        room.run_room(rooms.Fadeout(duration=1000, stop_mixer=False))

    def draw(self):
        window = display.window
        window.fill(c.BLACK)
        wr = window.get_rect()
        window.blit(self.victory, self.victory.get_rect(centery=wr.centery-50, centerx=wr.centerx))
        window.blit(self.thank_you, self.thank_you.get_rect(centery=wr.centery+50, centerx=wr.centerx))
        super().draw()

    def loop(self, _events):
        return True

    def end(self):
        super().end()
        self.wait_event()
        room.run_room(rooms.Fadeout(2000))

