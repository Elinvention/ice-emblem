"""

"""
from typing import Union

import pygame
import logging

import room
import rooms
import tmx
import display
import utils
import resources
import unit, item
import ai
from basictypes import Point

from map.pathfinder import Pathfinder, Terrain, manhattan_path
from map.unit import UnitSprite
from map.arrow import Arrow
from map.cellhighlight import CellHighlight
from map.cursor import Cursor


class TileMap(room.Room):
    """
    TileMap rendering.
    """

    def __init__(self, map_path, **kwargs):
        """
        
        """
        super().__init__(wait=False, bg_image=resources.load_image("old-paper.jpg").convert(),
                         bg_size='cover', layout_width=room.LayoutParams.FILL_PARENT,
                         layout_height=room.LayoutParams.FILL_PARENT, **kwargs)

        self.tilemap = tmx.load(map_path, self.rect.size, self.rect.topleft)

        self.zoom = self.tilemap.zoom = 2
        self.tw, self.th = (self.tilemap.tile_width, self.tilemap.tile_height)
        self.w, self.h = self.tilemap.width, self.tilemap.height

        self.terrains = {}
        self.sprites = tmx.SpriteLayer()

        yaml_units = utils.parse_yaml(resources.DATA_PATH / 'units.yml', unit)
        yaml_weapons = utils.parse_yaml(resources.DATA_PATH / 'weapons.yml', item)

        teams = {}

        for layer in self.tilemap.layers:
            if isinstance(layer, tmx.ObjectLayer):  # layer can be an ObjectLayer or a Layer
                c = layer.color
                layer.visible = False  # don't draw squares
                color = (int(c[1:3], base=16), int(c[3:5], base=16),
                        int(c[5:7], base=16))  # from '#RGB' to (R,G,B)
                units = {}
                for obj in layer.objects:
                    if obj.type == 'unit':
                        units[obj.name] = yaml_units[obj.name]
                        units[obj.name].coord = obj.px // self.tw, obj.py // self.th
                        weapon = obj.properties.get('weapon', None)
                        if weapon:
                            try:
                                units[obj.name].give_weapon(yaml_weapons[weapon])
                            except KeyError:
                                logging.warning("Weapon %s not found", weapon)
                relation = layer.properties['relation']
                boss = yaml_units[layer.properties['boss']]
                def get(key):
                    v = layer.properties.get(key, None)
                    return str(resources.MUSIC_PATH / v) if v else None
                music = {'map': get('map_music'), 'battle': get('battle_music')}
                if layer.properties.get('AI', None) is None:
                    teams[color] = unit.Team(layer.name, color, relation, list(units.values()), boss, music)
                else:
                    teams[color] = ai.AI(layer.name, color, relation, list(units.values()), boss, music)

        for layer in self.tilemap.layers:
            if isinstance(layer, tmx.ObjectLayer):
                for obj in layer.objects:
                    u = yaml_units[obj.name]
                    team = teams[u.team.color]
                    UnitSprite(self.tilemap, u, team, self.sprites)

        self.units_manager = unit.UnitsManager(list(teams.values()))

        for layer in reversed(self.tilemap.layers):
            if isinstance(layer, tmx.Layer):
                for cell in layer:
                    coord = cell.x, cell.y
                    units = self.units_manager.get_units(coord=coord)
                    _unit = units[0] if units else None
                    if coord not in self.terrains and cell.tile is not None:
                        self.terrains[coord] = Terrain(cell.tile, _unit)

        cursor_layer = tmx.SpriteLayer()
        self.cursor = Cursor(self.tilemap, resources.load_image('cursor.png'), cursor_layer)

        arrow_layer = tmx.SpriteLayer()
        self.arrow = Arrow(self.tilemap, resources.load_image('arrow.png'), arrow_layer)

        highlight_layer = tmx.SpriteLayer()
        self.highlight = CellHighlight(self.tilemap, highlight_layer)

        self.tilemap.layers.append(highlight_layer)
        self.tilemap.layers.append(self.sprites)
        self.tilemap.layers.append(arrow_layer)
        self.tilemap.layers.append(cursor_layer)

        self.tilemap.set_focus(self.tilemap.view_w // 2, self.tilemap.view_h // 2)

        self.prev_sel = None
        self.curr_sel = None
        self.move_area = []
        self.attack_area = []

        # Scroll speed
        self.vx, self.vy = 0, 0

        self.path = Pathfinder(self)
        self.return_path = None  # stores the path to undo a move
        self.moving = None

    @property
    def curr_unit(self) -> Union[unit.Unit, None]:
        try:
            return self.terrains[self.curr_sel].unit
        except KeyError:
            return None

    @curr_unit.setter
    def curr_unit(self, _unit: Union[unit.Unit, None]) -> None:
        self.curr_sel = _unit.coord

    @property
    def prev_unit(self) -> Union[unit.Unit, None]:
        try:
            return self.terrains[self.prev_sel].unit
        except KeyError:
            return None

    @prev_unit.setter
    def prev_unit(self, _unit: Union[unit.Unit, None]) -> None:
        self.prev_sel = _unit.coord

    def __getitem__(self, coord):
        return self.terrains[coord]

    def simulate_move(self, target):
        path = manhattan_path(self.cursor.coord, target)
        for next in path:
            self.cursor.point(*next)
            self.invalidate()
            yield 10

    def is_obstacle(self, coord, unit=None):
        terrain = self.terrains[coord]
        try:
            return self.units_manager.are_enemies(unit, terrain.unit)
        except AttributeError:
            if unit is None:
                return False
            for allowed in terrain.allowed:
                if allowed == 'any':
                    return False
                if allowed == 'none':
                    return True
                if allowed in unit.ALLOWED_TERRAINS:
                    return False
            return True

    def check_coord(self, coord):
        x, y = coord
        return 0 <= x < self.w and 0 <= y < self.h

    def neighbors(self, coord):
        """
        Returns a list containing all existing neighbors of a node.
        coord must be a valid coordinate i.e. self.check_coord(coord).
        """
        if not self.check_coord(coord):
            raise ValueError("Invalid coordinates")
        x, y = coord
        n = [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
        ret = [c for c in n if self.check_coord(c)]

        return ret

    def move_animation(self, _unit, target, path=None):
        if not path:
            path = self.path.shortest_path(_unit.coord, target, _unit.movement)
        px_path = list(map(lambda x: self.tilemap.pixel_at(*x, False), path))
        sprite = self.find_sprite(unit=_unit)
        if self.moving is not None and self.moving in self.children:
            self.remove_child(self.moving)
        self.moving = MoveAnimation(sprite, target, px_path)
        self.add_child(self.moving)
        return path

    def move(self, unit, new_coord, path=None):
        """
        This method moves a unit from a node to another one. If the two
        coordinates are the same no action is performed.
        """
        if unit.coord != new_coord:
            if self.get_unit(new_coord) is not None:
                raise ValueError("Destination %s is already occupied by another unit" % str(new_coord))
            self.return_path = self.move_animation(unit, new_coord, path)
            self.return_path.pop()
            self.return_path.reverse()
            self.return_path.append(unit.coord)
            self.terrains[unit.coord].unit = None
            self.terrains[new_coord].unit = unit
            print(_('Unit %s moved from %s to %s') % (unit.name, unit.coord, new_coord))
            unit.move(new_coord)

    def move_undo(self):
        if self.curr_sel != self.prev_sel:
            unit = self.curr_unit
            if self.return_path:
                self.move_animation(unit, self.prev_sel, self.return_path)
                self.return_path = None
            self.terrains[self.prev_sel].unit = unit
            self.terrains[self.curr_sel].unit = None
            unit.move(self.prev_sel)
        self.reset_selection()

    def kill_unit(self, _unit):
        self.units_manager.kill_unit(_unit)
        self.terrains[_unit.coord].unit = None
        sprite = self.find_sprite(unit=_unit)
        self.sprites.remove(sprite)

    def update_move_area(self):
        """
        Updates the area which will be highlighted on the map to show
        which nodes can be reached by the selected unit.
        """
        self.move_area = self.path.area(self.curr_sel, self.curr_unit.movement)

    def get_unit(self, coord):
        return self.terrains[coord].unit

    def find_sprite(self, **kwargs):
        for sprite in self.sprites:
            for attr in kwargs:
                if getattr(sprite, attr) == kwargs[attr]:
                    return sprite

    def __set_attack_area(self, coord, min_range, max_range):
        x, y = coord
        for i in range(x - max_range, x + max_range + 1):
            for j in range(y - max_range, y + max_range + 1):
                if (i, j) not in self.move_area and (i, j) not in self.attack_area:
                    if min_range <= utils.distance((x, y), (i, j)) <= max_range:
                        self.attack_area.append((i, j))

    def move_attack_area(self):
        """
        Updates the area which will be highlighted on the map to show
        how far the selected unit can move and attack.
        """
        min_range, max_range = self.curr_unit.get_weapon_range()
        self.attack_area = []
        for (x, y) in self.move_area:
            self.__set_attack_area((x, y), min_range, max_range)

    def still_attack_area(self):
        """
        Update the area which will be highlighted on the map to show
        how far the selected unit can attack with her weapon
        """
        min_range, max_range = self.curr_unit.get_weapon_range()
        self.attack_area = []
        self.move_area = []
        self.__set_attack_area(self.curr_sel, min_range, max_range)

    def path_cost(self, path):
        cost = 0
        for coord in path:
            cost += self.terrains[coord].moves
        return cost

    def update_arrow(self, target=None):
        if self.curr_unit and not self.curr_unit.played and self.units_manager.active_team.is_mine(self.curr_unit) and target:
            target_unit = self.get_unit(target)
            if target in self.move_area:
                self.arrow.source = self.curr_sel
                self.arrow.add_or_remove_coord(target)
                if self.path_cost(self.arrow.path) > self.curr_unit.movement or target not in self.arrow.path:
                    path = self.path.shortest_path(self.curr_sel, target, self.curr_unit.movement)
                    self.arrow.set_path(path, self.curr_sel)
            elif target in self.attack_area and target_unit:
                if not self.arrow.path or target_unit not in self.nearby_enemies(self.curr_unit, self.arrow.path[-1]):
                    path = self.path.shortest_path(self.curr_sel, target, self.curr_unit.movement)
                else:
                    path = self.arrow.path
                min_range = self.curr_unit.get_weapon_range()[0]
                while path and (Point(path[-1]) - Point(target)).norm() < min_range:
                    print(path.pop())
                self.arrow.set_path(path, self.curr_sel)
        else:
            self.arrow.set_path([])

    def update_highlight(self):
        played = [u.coord for u in self.units_manager.active_team.list_played()]
        self.highlight.update(self.curr_sel, self.move_area, self.attack_area, played)
        self.invalidate()

    def area(self, center, radius, hole=0):
        x, y = center
        _area = [(i, j) for i in range(x - radius, x + radius + 1)
                    for j in range(y - radius, y + radius + 1)
                    if self.check_coord((i, j))
                    and hole <= utils.distance((x, y), (i, j)) <= radius]
        return _area

    def nearby_enemies(self, _unit=None, coord=None):
        """
        Returns a list of near enemies that can be attacked without having to move.
        """
        if not _unit:
            _unit = self.curr_unit
        if not coord:
            coord = _unit.coord
        min_range, max_range = _unit.get_weapon_range()
        area = self.area(coord, max_range, min_range)
        nearby_list = []
        for u in area:
            c_unit = self.get_unit(u)
            if c_unit and self.units_manager.are_enemies(c_unit, _unit):
                nearby_list.append(c_unit)
        return nearby_list

    def reset_selection(self):
        logging.debug('Selection reset')
        self.curr_sel = None
        self.prev_sel = None
        self.move_area = []
        self.attack_area = []
        self.arrow.set_path([])
        self.update_highlight()

    def can_selection_move(self):
        return (self.prev_unit is not None and not self.prev_unit.played and
                self.units_manager.active_team.is_mine(self.prev_unit) and
                self.curr_sel in self.move_area)

    def handle_mousebuttondown(self, event):
        if event.button == 1:
            if self.rect.collidepoint(event.pos):
                coord = self.tilemap.index_at(*event.pos)
                if coord:
                    self.select(coord)
                    self.update_highlight()
        elif event.button == 3:
            self.reset_selection()
        elif event.button == 4:  # Mouse wheel up
            if self.zoom < 5:
                self.zoom += 1
        elif event.button == 5:
            if self.zoom > 1:
                self.zoom -= 1

    def handle_mousemotion(self, event):
        x, y = event.pos
        border, speed = 200, 100
        if self.rect.collidepoint(event.pos):
            coord = self.tilemap.index_at(x, y)
            if coord and coord != self.cursor.coord:
                self.cursor.point(*coord)
                self.invalidate()
                self.update_arrow(coord)

            if x - self.rect.left < border:
                self.vx = int(-speed * (1 - ((x - self.rect.left) / border)))
            elif self.rect.right - x < border:
                self.vx = int(speed * (1 - ((self.rect.right - x) / border)))
            else:
                self.vx = 0

            if y - self.rect.top < border:
                self.vy = int(-speed * (1 - ((y - self.rect.top) / border)))
            elif self.rect.bottom -y < border:
                self.vy = int(speed * (1 - ((self.rect.bottom - y) / border)))
            else:
                self.vy = 0
        else:
            self.vx = self.vy = 0

        self.wait_set(not self.tilemap.can_scroll(self.vx, self.vy))

    def handle_keydown(self, event):
        self.cursor.update(event)
        self.update_arrow(self.cursor.coord)
        self.tilemap.set_focus(*self.cursor.rect.topleft)

        if event.key == pygame.K_SPACE:
            self.select(self.cursor.coord)
            self.update_highlight()
        self.invalidate()

    def layout(self, rect):
        if self.tilemap.viewport.size != rect.size:
            self.tilemap.viewport.size = rect.size
            self.tilemap.view_w, self.tilemap.view_h = rect.size
            self.tilemap.set_focus(self.tilemap.restricted_fx, self.tilemap.restricted_fy)
        super().layout(rect)

    def loop(self, _events, dt):
        super().loop(_events, dt)
        if self.vx != 0 or self.vy != 0:
            prev = (self.tilemap.restricted_fx, self.tilemap.restricted_fy)
            self.tilemap.scroll(self.vx, self.vy)
            if prev != (self.tilemap.restricted_fx, self.tilemap.restricted_fy):
                self.cursor.update()
                self.invalidate()
            self.wait_set(not self.tilemap.can_scroll(self.vx, self.vy))
        if self.zoom != self.tilemap.zoom:
            self.tilemap.set_zoom(self.zoom, *self.cursor.rect.topleft)
            self.sprites.update()
            self.cursor.update()
            self.arrow.update()
            self.update_highlight()
            self.fill()

    def draw(self):
        self.tilemap.draw(self.surface)
        self.draw_children()
        self.valid = True
        self.surface = self.surface.convert()

    def select(self, coord):
        """
        Handles selection on the map.
        """
        active_team = self.units_manager.active_team
        self.prev_sel = self.curr_sel
        self.curr_sel = coord

        if self.prev_sel is None:
            # Nothing has been previously selected
            unit = self.get_unit(coord)
            if unit is None or unit.played:
                self.move_area = []
                self.attack_area = []
            else:
                # Show the currently selected unit's move and attack area
                self.update_move_area()
                self.move_attack_area()
        else:
            # Something has been previously selected
            if self.prev_unit is not None and self.curr_unit is not None:
                # Selected a unit two times
                if self.prev_sel == self.curr_sel and not self.prev_unit.played and active_team.is_mine(self.prev_unit):
                    # Two times on the same playable unit. Show the action menu.
                    self.action_menu()
                elif self.curr_sel in self.attack_area:
                    # Two different units: prev_unit can attack curr_unit
                    # This results in a combined action: move the unit next to the enemy and propose the user to attack
                    nearest = self.arrow.path[-1] if self.arrow.path else self.prev_sel
                    if self.nearby_enemies(self.prev_unit, nearest):
                        self.move(self.prev_unit, nearest, self.arrow.path)
                        self.curr_sel = nearest
                        self.still_attack_area()
                        self.action_menu()
                    else:
                        self.reset_selection()
                else:
                    # Two different units: prev_unit can't attack curr_unit
                    # show the current unit's move and attack area
                    self.update_move_area()
                    self.move_attack_area()
            elif self.can_selection_move():
                # Move the previously selected unit to the currently selected coordinate.
                self.move(self.prev_unit, self.curr_sel, self.arrow.path)
                self.still_attack_area()
                self.action_menu()
            else:
                # Previously something irrelevant was chosen
                self.reset_selection()
                self.curr_sel = coord

                if self.curr_unit is not None and not self.curr_unit.played:
                    # Selected a unit: show its move and attack area
                    self.update_move_area()
                    self.move_attack_area()

        self.arrow.set_path([])

    def action_menu(self, pos=None):
        self.vx, self.vy = 0, 0
        if pos is None:
            pos = self.tilemap.pixel_at(*self.curr_sel, False) - self.tilemap.viewport.topleft + self.tilemap.zoom_tile_size / 2
        menu = rooms.ActionMenu(layout_position=pos, padding=10, leading=5)
        self.add_child(menu)

    def prepare_attack(self, _unit=None):
        if not _unit:
            _unit = self.curr_unit
        self.move_area = []
        self.attack_area = [u.coord for u in self.nearby_enemies(_unit, _unit.coord)]
        self.update_highlight()

    def attack(self, attacking=None, defending=None):
        if not defending:
            defending = self.curr_unit
        if not attacking:
            attacking = self.prev_unit

        assert(defending != attacking)

        # let the battle begin!
        room.run_room(rooms.BattleAnimation(attacking, defending))

        self.reset_selection()

    def is_attack_click(self, mouse_pos):
        coord = self.tilemap.index_at(*mouse_pos)
        return self.rect.collidepoint(mouse_pos) and coord in self.attack_area

    def is_enemy_cursor(self):
        return self.cursor.coord in self.attack_area


class MoveAnimation(room.Room):
    def __init__(self, sprite, target, path):
        super().__init__(wait=False, visible=False)
        self.sprite = sprite
        self.target = target
        self.path = path

    def loop(self, _events, dt):
        reached = self.sprite.move_animation(dt, self.path[0])
        self.invalidate()
        if reached and len(self.path) > 0:
            self.path.pop(0)
        self.done = len(self.path) == 0

    def end(self):
        self.parent.moving = None
        self.sprite.reposition()
        super().end()


if __name__ == '__main__':
    import gettext
    gettext.install('ice-emblem', resources.LOCALE_PATH)
    logging.basicConfig(level=0)
    room.run_room(TileMap('resources/maps/default.tmx', w=200, h=200, center=display.get_rect().center))
    pygame.quit()
