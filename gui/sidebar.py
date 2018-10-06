"""

"""


import gui
import fonts as f
import state as s
import resources

from room import Gravity


class Sidebar(gui.NinePatch):
    def __init__(self, **kwargs):
        super().__init__(resources.load_image('WindowBorder.png'), (70, 70),
                         layout_height=gui.LayoutParams.FILL_PARENT,
                         layout_width=250,
                         layout_gravity=gui.Gravity.RIGHT, gravity=Gravity.TOPLEFT, padding=30, **kwargs)
        self.endturn_btn = gui.Button(_("End Turn"), f.SMALL, layout_gravity=Gravity.BOTTOMRIGHT, callback=lambda *_: s.units_manager.active_team.end_turn())
        self.turn_label = gui.Label(_("{team} turn"), f.SMALL)
        self.terrain_label = gui.Label(f'{{0}}\n{_("Def")}: {{1}}\n{_("Avoid")}: {{2}}\n{_("Allowed")}: {{3}}', f.SMALL)
        self.unit_label = gui.Label('{0}\n{1}', f.SMALL)
        self.coord_label = gui.Label('X: {0} Y: {1}', f.SMALL, layout_gravity=Gravity.BOTTOM)
        self.clock = gui.Clock(f.SMALL, layout_gravity=Gravity.BOTTOM)
        self.add_children(self.turn_label, self.terrain_label, self.unit_label, self.coord_label, self.clock, self.endturn_btn)

    def begin(self):
        super().begin()
        s.loaded_map.cursor.register_cursor_moved(self.coord_changed)

    def turn_changed(self, team):
        self.turn_label.txt_color = team.color
        self.turn_label.format(team=team.name)

    def coord_changed(self, coord):
        unit = s.loaded_map.get_unit(coord)
        terrain = s.loaded_map[coord]

        if terrain:
            self.terrain_label.format(terrain.name, terrain.defense, terrain.avoid, ", ".join(terrain.allowed))

        if unit:
            weapon = unit.items.active
            self.unit_label.format(unit.name, weapon.name if weapon else _("No Weapon"))
        else:
            self.unit_label.set_text("No unit")

        self.coord_label.format(*coord)

