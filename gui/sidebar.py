"""

"""


import gui
import fonts as f
import state as s
import resources
import game

from room import Layout, LayoutParams, Gravity, MeasureParams, MeasureSpec


class Sidebar(gui.LinearLayout):
    def __init__(self, turn, **kwargs):
        super().__init__(background=gui.NinePatch(resources.load_image('WindowBorder.png'), (70, 70)),
                         layout=Layout(height=LayoutParams.FILL_PARENT, width=270, gravity=Gravity.RIGHT),
                         default_child_gravity=Gravity.TOPLEFT, padding=30, **kwargs)

        font = f.SMALLER
        self.endturn_btn = gui.Button(_("End Turn"), font, layout=Layout(gravity=Gravity.BOTTOMRIGHT),
                                      callback=lambda *_: turn.end_turn())
        self.turn_label = gui.Label(_("{team} turn"), font)
        self.terrain_label = gui.Label(f'Terrain: {{0}}\n{_("Def")}: {{1}}\n{_("Avoid")}: {{2}}\n{_("Allowed")}: {{3}}', font)
        self.unit_label = gui.Label('Unit: {0}\nHealth: {1}\nCan move on: {2}\nWeapon: {3}', font)
        self.coord_label = gui.Label('X: {0} Y: {1}', font, layout=Layout(gravity=Gravity.BOTTOM))
        self.clock = gui.Clock(font, layout=Layout(gravity=Gravity.BOTTOM))

        self.add_children(self.turn_label, self.terrain_label, self.unit_label, self.coord_label, self.clock)

        if isinstance(turn, game.PlayerTurn):
            self.add_child(self.endturn_btn)

    def begin(self):
        super().begin()
        s.loaded_map.cursor.register_cursor_moved(self.coord_changed)
        self.turn_label.txt_color = s.units_manager.active_team.color
        self.turn_label.format(team=s.units_manager.active_team.name)

    def coord_changed(self, coord):
        unit = s.loaded_map.get_unit(coord)
        terrain = s.loaded_map[coord]

        if terrain:
            self.terrain_label.format(_(terrain.name), terrain.defense, terrain.avoid, ', '.join(map(_, terrain.allowed)))

        if unit:
            weapon = unit.items.active
            self.unit_label.format(unit.name, unit.condition, ', '.join(map(_, unit.ALLOWED_TERRAINS)), str(weapon) if weapon else _("No Weapon"))
        else:
            self.unit_label.set_text("No unit")

        self.coord_label.format(*coord)

