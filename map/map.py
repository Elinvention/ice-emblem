"""

"""

import pygame
import logging
from typing import List, Tuple, Optional
from typing import Union

import action
import ai
import display
import game
import item
import resources
import room
import rooms
import tmx
import unit
import utils
from basictypes import Point
from map.arrow import Arrow
from map.cellhighlight import CellHighlightLayer
from map.cursor import Cursor
from map.pathfinder import Pathfinder, Terrain, manhattan_path
from map.unit import UnitSprite
from room import Layout, LayoutParams, Background, BackgroundSize

Coord = Tuple[int, int]


class TileMap(room.Room):
    """
    TileMap rendering.
    """

    def __init__(self, map_path, **kwargs):
        """
        
        """
        super().__init__(wait=False,
                         background=Background(image=resources.load_image("old-paper.jpg"), size=BackgroundSize.COVER),
                         layout=Layout(width=LayoutParams.FILL_PARENT, height=LayoutParams.FILL_PARENT), **kwargs)

        self.tilemap = tmx.load(map_path, self.rect.size, self.rect.topleft)

        self.zoom = self.tilemap.zoom = 2
        self.tw, self.th = (self.tilemap.tile_width, self.tilemap.tile_height)
        self.w, self.h = self.tilemap.width, self.tilemap.height

        self.terrains = {}
        self.sprites_layer = tmx.SpriteLayer()

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
                    UnitSprite(self.tilemap, u, team, self.sprites_layer)

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

        self.highlight_layer = CellHighlightLayer(self.tilemap)

        self.tilemap.layers.append(self.highlight_layer)
        self.tilemap.layers.append(self.sprites_layer)
        self.tilemap.layers.append(arrow_layer)
        self.tilemap.layers.append(cursor_layer)

        self.tilemap.set_focus(self.tilemap.view_w // 2, self.tilemap.view_h // 2)

        self.prev_sel: Union[None, Coord] = None
        self.curr_sel: Union[None, Coord] = None
        self.move_area: List[Coord] = []
        self.attack_area: List[Coord] = []

        # Scroll speed
        self.vx, self.vy = 0, 0

        self.path = Pathfinder(self)
        self.return_path = None  # stores the path to undo a move

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

    def is_obstacle(self, coord, for_unit=None):
        terrain = self.terrains[coord]
        try:
            return self.units_manager.are_enemies(for_unit, terrain.unit)
        except AttributeError:
            if for_unit is None:
                return False
            for allowed in terrain.allowed:
                if allowed == 'any':
                    return False
                if allowed == 'none':
                    return True
                if allowed in for_unit.ALLOWED_TERRAINS:
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

    def make_move_unit_animation(self, who: unit.Unit, where: Coord, path=None) -> Union[None, 'MoveUnitAnimation']:
        """
        Factory method for MoveUnitAnimation.

        :param who: the unit to move
        :param where: the destination
        :param path: optional, the path to follow to reach the destination
        :return: the animation of the move
        """
        if who.coord == where:
            return None
        if not path:
            path = self.path.shortest_path(who.coord, where, who.movement)
        px_path = list(map(lambda x: self.tilemap.pixel_at(*x, False), path))
        sprite: UnitSprite = self.find_sprite(unit=who)
        animation = MoveUnitAnimation(who, where, sprite, px_path)
        # build the return path (used to undo the move)
        path.pop()
        path.reverse()
        path.append(who.coord)
        self.return_path = path
        return animation

    def add_move_unit_animation(self, animation: 'MoveUnitAnimation') -> None:
        """
        Ensures there is only one MoveUnitAnimation children before adding the new animation.

        Pending animations are removed.
        :param animation: the new animation to add as child
        """
        if animation is None:
            return
        for child in self.children:
            if isinstance(child, MoveUnitAnimation):
                child.end()
        self.add_child(animation)

    def move_unit(self, who: unit.Unit, where: Coord) -> None:
        """
        Moves a unit to a another place. If the unit is already at the destination, no action is performed.

        This method does the actual movement of the unit, but does not perform any animation visible on the map.
        For that see :method:`make_move_unit_animation` and :method:`add_move_unit_animation`.
        :param who: the unit to move
        :param where: the destination
        """
        if who.coord != where:
            if self.get_unit(where) is not None:
                raise ValueError("Destination %s is already occupied by another unit" % str(where))
            self.terrains[who.coord].unit = None
            self.terrains[where].unit = who
            print(_('Unit %s moved from %s to %s') % (who.name, who.coord, where))
            who.move(where)

    def move_unit_undo(self):
        if self.curr_sel != self.prev_sel:
            _unit = self.curr_unit
            if self.return_path:
                animation = self.make_move_unit_animation(_unit, self.prev_sel, self.return_path)
                self.add_move_unit_animation(animation)
                self.return_path = None
            self.terrains[self.prev_sel].unit = _unit
            self.terrains[self.curr_sel].unit = None
            _unit.move(self.prev_sel)
        self.reset_selection()

    def kill_unit(self, _unit):
        self.units_manager.kill_unit(_unit)
        self.terrains[_unit.coord].unit = None
        sprite = self.find_sprite(unit=_unit)
        self.sprites_layer.remove(sprite)

    def get_unit(self, coord):
        return self.terrains[coord].unit

    def find_sprite(self, **kwargs) -> UnitSprite:
        unit_sprite: UnitSprite
        for unit_sprite in self.sprites_layer:
            for attr in kwargs:
                if getattr(unit_sprite, attr) == kwargs[attr]:
                    return unit_sprite

    def path_cost(self, path):
        cost = 0
        for coord in path:
            cost += self.terrains[coord].moves
        return cost

    def update_arrow(self, target=None):
        if self.curr_unit and not self.curr_unit.played \
                and self.units_manager.active_team.is_mine(self.curr_unit) and target:
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
        self.highlight_layer.update(self.curr_sel, self.move_area, self.attack_area, played)
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

    def handle_mousebuttondown(self, event):
        if isinstance(self.parent, game.AITurn):
            return
        if event.button == 1:
            if self.rect.collidepoint(event.pos):
                coord = self.tilemap.index_at(*event.pos)
                if coord:
                    self.select(coord)
        elif event.button == 3:
            self.reset_selection()
        elif event.button == 4:  # Mouse wheel up
            if self.zoom < 5:
                self.zoom += 1
        elif event.button == 5:
            if self.zoom > 1:
                self.zoom -= 1

    def handle_mousemotion(self, event):
        if isinstance(self.parent, game.AITurn):
            return
        x, y = event.pos
        border, speed = 200, 100
        if self.rect.collidepoint(event.pos):
            coord = self.tilemap.index_at(x, y)
            if coord and coord != self.cursor.coord:
                self.cursor.point(*coord)
                self.invalidate()
                if self.children_done():
                    self.update_arrow(coord)

            if x - self.rect.left < border:
                self.vx = int(-speed * (1 - ((x - self.rect.left) / border)))
            elif self.rect.right - x < border:
                self.vx = int(speed * (1 - ((self.rect.right - x) / border)))
            else:
                self.vx = 0

            if y - self.rect.top < border:
                self.vy = int(-speed * (1 - ((y - self.rect.top) / border)))
            elif self.rect.bottom - y < border:
                self.vy = int(speed * (1 - ((self.rect.bottom - y) / border)))
            else:
                self.vy = 0
        else:
            self.vx = self.vy = 0

        self.wait_set(not self.tilemap.can_scroll(self.vx, self.vy))

    def handle_keydown(self, event):
        if isinstance(self.parent, game.AITurn):
            return
        self.cursor.update(event)
        self.update_arrow(self.cursor.coord)
        self.tilemap.set_focus(*self.cursor.rect.topleft)

        if event.key == pygame.K_SPACE:
            self.select(self.cursor.coord)
        self.invalidate()

    def layout_children(self, rect):
        if self.tilemap.viewport.size != rect.size:
            self.tilemap.viewport.size = rect.size
            self.tilemap.view_w, self.tilemap.view_h = rect.size
            self.tilemap.set_focus(self.tilemap.restricted_fx, self.tilemap.restricted_fy)
        super().layout_children(rect)

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
            self.sprites_layer.update()
            self.cursor.update()
            self.arrow.update()
            self.update_highlight()
            self.fill()

    def draw(self):
        self.tilemap.draw(self.surface)
        self.draw_children()
        self.valid = True
        self.surface = self.surface.convert()

    def __set_attack_area(self, coord: Tuple[int, int], min_range: int, max_range: int):
        # Auxiliary method for update_move_attack_area and update_still_attack_area
        x, y = coord
        for i in range(x - max_range, x + max_range + 1):
            for j in range(y - max_range, y + max_range + 1):
                if self.check_coord((i, j)) and (i, j) not in self.move_area and (i, j) not in self.attack_area:
                    if min_range <= utils.distance((x, y), (i, j)) <= max_range:
                        self.attack_area.append((i, j))

    def update_move_attack_area(self, _unit: Optional[unit.Unit]):
        """
        Updates the area which will be highlighted on the map to show how far unit can move and attack.
        """
        if _unit is not None and not _unit.played:
            self.move_area = self.path.area(_unit.coord, _unit.movement)
            min_range, max_range = _unit.get_weapon_range()
            self.attack_area = []
            for coord in self.move_area:
                self.__set_attack_area(coord, min_range, max_range)
        else:
            self.move_area = []
            self.attack_area = []

    def update_still_attack_area(self, _unit: Optional[unit.Unit]):
        """
        Update the area which will be highlighted on the map to show
        how far the selected unit can attack with her weapon
        """
        if _unit is not None and not _unit.played:
            min_range, max_range = self.curr_unit.get_weapon_range()
            self.attack_area = []
            self.move_area = []
            self.__set_attack_area(self.curr_sel, min_range, max_range)
        else:
            self.attack_area = []
            self.move_area = []

    def can_selection_move(self):
        return (self.prev_unit is not None and not self.prev_unit.played and
                self.units_manager.active_team.is_mine(self.prev_unit) and
                self.curr_sel in self.move_area)

    def move_then_action_menu(self, target: Optional[Tuple[int, int]] = None):
        if target is None:
            target = self.curr_sel
        target_unit = self.curr_unit
        animation = self.make_move_unit_animation(self.prev_unit, target, self.arrow.path)
        self.add_move_unit_animation(animation)
        self.move_unit(self.prev_unit, target)
        self.curr_sel = target  # otherwise move_undo will move back the defending unit!
        self.update_still_attack_area(self.curr_unit)
        self.update_highlight()
        self.action_menu(attacking=self.curr_unit, defending=target_unit)

    def select(self, coord: Coord) -> None:
        """
        Handles selection on the map.
        :param coord: the selected coordinate on the map.
        """
        active_team = self.units_manager.active_team
        self.prev_sel = self.curr_sel
        self.curr_sel = coord

        if self.prev_sel is None:
            # Nothing has been previously selected
            self.update_move_attack_area(self.curr_unit)
            self.update_highlight()
        elif self.prev_unit is not None and self.curr_unit is not None:
            # Selected a unit and then another unit
            if self.prev_unit.played or not active_team.is_mine(self.prev_unit):
                # The previous unit can't be controlled. Just show what it can do
                self.update_move_attack_area(self.curr_unit)
                self.update_highlight()
            elif self.prev_sel == self.curr_sel:
                # Two times on the same playable unit. Show the action menu.
                self.action_menu()
            elif self.curr_sel in self.attack_area:
                # Two different units: prev_unit can attack curr_unit
                # This results in a combined action: move the unit next to the enemy and propose the user to attack
                nearest = self.arrow.path[-1] if self.arrow.path else self.prev_sel
                if self.nearby_enemies(self.prev_unit, nearest):
                    # prev_unit can actually move near the enemy and attack
                    self.move_then_action_menu(nearest)
                else:
                    # prev_unit can't reach the enemy
                    self.reset_selection()
        elif self.can_selection_move():
            # Move the previously selected unit to the currently selected coordinate.
            self.move_then_action_menu()
        else:
            # Previously something irrelevant was chosen
            self.reset_selection()
            self.curr_sel = coord

            # show move and attack area of unit if present
            self.update_move_attack_area(self.curr_unit)
            self.update_highlight()

        self.arrow.set_path([])

    def action_menu(self, attacking=None, defending=None, pos=None):
        self.vx, self.vy = 0, 0
        if pos is None:
            pos = self.tilemap.pixel_at(*self.curr_sel, False) - self.tilemap.viewport.topleft + \
                  self.tilemap.zoom_tile_size / 2
        menu = rooms.ActionMenu(attacking, defending, layout=Layout(position=pos), padding=10, leading=5)
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

    def do_action(self, _action: action.Action) -> None:
        """
        Makes an action actually happen on screen.
        :param _action: the action to perform
        :raise: NotImplementedError in case the type of action is not defined.
        """
        if isinstance(_action, action.Attack):
            self.do_attack_action(_action)
        elif isinstance(_action, action.Move):
            self.do_move_action(_action)
        else:
            raise NotImplementedError(f"Action {type(_action)} not implemented!")

    def do_attack_action(self, attack_action: action.Attack) -> None:
        """
        Makes the cursor move to the attacking unit, then to the defending one and finally makes the battle happen.
        :param attack_action: the :class:`action.Attack` that describes who should attack who.
        """
        self.logger.debug("Executing action.Attack: %s", attack_action)
        self.reset_selection()
        # First move the cursor on the attacking unit
        first = MoveCursorAnimation(self.cursor.coord, attack_action.attacking.coord)
        # Then select the attacking unit
        first.next = SelectAndWait(attack_action.attacking.coord)
        # Then move the cursor on the defending unit
        first.next.next = MoveCursorAnimation(attack_action.attacking.coord, attack_action.defending.coord)
        # Finally do the attack
        first.next.next.next = room.RunRoomAsRoot(rooms.BattleAnimation(attack_action.attacking, attack_action.defending))
        self.add_child(first)

    def do_move_action(self, move_action: action.Move) -> None:
        """
        Makes the cursor move to the unit to move, then to the destination and finally starts the move animation.
        :param move_action: the :class:`action.Move` that describes who should move where.
        """
        self.logger.debug("Executing action.Move: %s", move_action)
        self.reset_selection()
        # First move the cursor on the unit to move
        first = MoveCursorAnimation(self.cursor.coord, move_action.who.coord)
        # Then select the unit to move
        first.next = SelectAndWait(move_action.who.coord)
        # Then move the cursor on the destination
        first.next.next = MoveCursorAnimation(move_action.who.coord, move_action.where)
        # Finally play the unit move animation
        first.next.next.next = self.make_move_unit_animation(move_action.who, move_action.where)
        self.add_child(first)


class MoveUnitAnimation(room.Room):
    """
    Animate the movement of a sprite.

    Objects instantiated from this class should be added as child of :class:`TileMap` using the method
    :method:`TileMap.add_move_unit_animation`, to ensure that only one movement animation is taking place.
    """
    def __init__(self, who: unit.Unit, where: Coord, sprite: UnitSprite, path: List[Coord]):
        super().__init__(wait=False, visible=False)
        self.who: unit.Unit = who
        self.where: Coord = where
        self.sprite: UnitSprite = sprite
        self.path: List[Coord] = path
        self.next_path: Coord = path.pop(0)

    def loop(self, _events: List[pygame.event.Event], dt: int) -> None:
        super().loop(_events, dt)
        if self.next_path is None:
            return
        reached = self.sprite.move_animation(dt, self.next_path)
        self.invalidate()
        if reached:
            try:
                self.next_path = self.path.pop(0)
            except IndexError:
                self.set_timeout(100, lambda *_: self.mark_done())
                self.next_path = None

    def end(self) -> None:
        self.parent: TileMap
        self.parent.move_unit(self.who, self.where)
        self.sprite.reposition()
        super().end()


class MoveCursorAnimation(room.Room):
    """
    Make the cursor move along a path. Should be a child of :class:`TileMap`.
    """
    def __init__(self, source: Coord, target: Coord):
        super().__init__()
        self.path = manhattan_path(source, target)
        self.set_interval(100, self.step)

    def step(self, *_) -> None:
        self.parent: TileMap
        try:
            self.parent.cursor.point(*next(self.path))
            self.parent.invalidate()
        except StopIteration:
            self.done = True


class SelectAndWait(room.Room):
    """
    Select a coordinate and wait 100ms. Should be a child of :class:`TileMap`.
    """
    def __init__(self, coord: Coord):
        super().__init__()
        self.coord = coord

    def begin(self) -> None:
        self.parent: TileMap
        super().begin()
        self.parent.select(self.coord)
        self.set_timeout(100, self.mark_done)


if __name__ == '__main__':
    import gettext
    gettext.install('ice-emblem', resources.LOCALE_PATH)
    logging.basicConfig(level=0)
    room.run_room(TileMap('resources/maps/default.tmx', w=200, h=200, center=display.get_rect().center))
    pygame.quit()
