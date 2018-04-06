"""

"""


import pygame

import room
import display
import gui
import fonts as f
import state as s
import colors as c
import game


class Sidebar(room.Room):
    def __init__(self, **kwargs):
        super().__init__(w=250, h=display.window.get_height(), right=display.window.get_width(), **kwargs)
        self.endturn_btn = gui.Button(_("End Turn"), f.SMALL, right=self.rect.w, bottom=self.rect.h, callback=game.switch_turn)
        self.add_child(self.endturn_btn)
        self.start_time = 0

    def begin(self):
        if self.start_time == 0:
            self.start_time = pygame.time.get_ticks()

    def handle_videoresize(self, event):
        self.resize((250, event.h))
        self.rect.right = event.w
        self.endturn_btn.rect.bottomright = self.rect.bottomright

    def draw(self):
        coord = s.loaded_map.cursor.coord
        unit = s.loaded_map.get_unit(coord)
        terrain = s.loaded_map[coord]
        team = s.units_manager.active_team
        render = lambda x, y: f.SMALL.render(x, True, y)

        self.surface.fill((100, 100, 100))

        turn_s = render(_('%s phase') % team.name, team.color)
        pos = turn_s.get_rect(top=40, left=10)
        self.surface.blit(turn_s, pos)

        t_info = [
            render(terrain.name, c.WHITE),
            render(_("Def: %d") % terrain.defense, c.WHITE),
            render(_("Avoid: %d") % terrain.avoid, c.WHITE),
            render(_("Allowed: %s") % (", ".join(terrain.allowed)), c.WHITE),
        ] if terrain else []

        weapon = unit.items.active if unit else None
        weapon_name = weapon.name if weapon else _("No Weapon")
        u_info = [
            render(unit.name, unit.team.color),
            render(weapon_name, c.WHITE),
        ] if unit else [render(_("No unit"), c.WHITE)]

        delta = (pygame.time.get_ticks() - self.start_time) // 1000
        hours, remainder = divmod(delta, 3600)
        minutes, seconds = divmod(remainder, 60)

        global_info = [
            render('X: %d Y: %d' % coord, c.WHITE),
            render('%02d:%02d:%02d' % (hours, minutes, seconds), c.WHITE),
        ]

        out = t_info + u_info + global_info

        for i in out:
            pos.move_ip(0, 40)
            self.surface.blit(i, pos)

        super().draw()
