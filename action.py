import state as s
import room
import rooms


class Action(object):
    pass

class Attack(Action):
    def __init__(self, attacking, defending):
        super().__init__()
        self.attacking = attacking
        self.defending = defending

    def __iter__(self):
        yield from s.loaded_map.simulate_move(self.attacking.coord)
        s.loaded_map.prepare_attack(self.attacking)
        yield 5
        yield from s.loaded_map.simulate_move(self.defending.coord)
        yield 5
        room.run_room(rooms.BattleAnimation(self.attacking, self.defending))
        s.loaded_map.reset_selection()

    def __str__(self):
        return f"{self.attacking.name} vs {self.defending.name}"


class Move(Action):
    def __init__(self, who, where):
        super().__init__()
        self.who = who
        self.where = where

    def __iter__(self):
        yield from s.loaded_map.simulate_move(self.who.coord)
        yield 5
        s.loaded_map.curr_unit = self.who
        s.loaded_map.update_move_area()
        s.loaded_map.move_attack_area()
        s.loaded_map.update_highlight()
        yield 5
        yield from s.loaded_map.simulate_move(self.where)
        yield 5
        s.loaded_map.move(self.who, self.where)
        s.loaded_map.reset_selection()

    def __str__(self):
        return f"Move {self.who.name} to {self.where}"
