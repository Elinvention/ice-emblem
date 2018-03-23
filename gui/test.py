"""

"""


import pygame
import logging

import colors as c
import utils
import display
import room


if __name__ == '__main__':
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

