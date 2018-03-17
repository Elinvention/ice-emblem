# -*- coding: utf-8 -*-
#
#  Item.py, Ice Emblem's item class.
#
#  Copyright 2015 Elia Argentieri <elia.argentieri@openmailbox.org>
#  Copyright 2015 Luca Argentieri <luca99.argentieri@gmail.com>
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.


class Item(object):
    """Generic item class"""
    def __init__(self, name, worth, uses, description=""):
        self.name     =    name
        self.descr    =    description
        self.worth    =    int(worth)  # Price
        self.muses    =    int(uses)   # max number of uses
        self.uses     =    int(uses)   # number of remaining uses

    def use(self):
        self.uses -= 1
        if self.uses <= 0:
            self.uses = 0
            print("%s is broken" % self.name)
        return self.uses

    def __str__(self):
        return f'{self.name} ({self.uses}/{self.muses})'

    def __repr__(self):
        return (
            f'Item:\n\tName: "{self.name}"\n\tDescription: "{self.descr}"\n'
            f'\tWorth: "{self.worth}₤"\n\tUses: {self.uses}/{self.muses}'
        )


class Weapon(Item):
    bonus_weapons = []
    bonus_units = []
    """Swords, Lances, Axes, Bows, Tomes, Staffs"""
    def __init__(self, name, rank, might, weight, hit, critical, range,
                uses, worth, experience, effective, description=""):
        super().__init__(name, worth, uses, description)
        self.rank      = rank               # rank necessary to use it
        self.might     = int(might)         # damage
        self.weight    = int(weight)        # weight affects on speed
        self.hit       = int(hit)           # probability to hit the enemy
        self.crit      = int(critical)          # probability of triple damage
        self.min_range = int(range['min'])  # min attack distance
        self.max_range = int(range['max'])  # max attack distancez
        self.exp       = int(experience)    # exp increases unit's weapon rank
        self.effective = effective

    def __repr__(self):
        return (
            'Weapon:\n\tName: "{name}"\n'
            'Description: "{descr}"\n'
            'Rank: {rank}\n'
            'Might: {might}\n'
            'Weight: {weight}\n'
            'Hit: {hit}\n'
            'Crit: {crit}\n'
            'Range: {min_range}-{max_range}\n'
            'Uses: {uses}/{muses}\n'
            'Worth: {worth}\n'
            'Exp: {experience}\n'
            .format_map(self.__dict__)
        )

    def get_might(self, enemy):
        if isinstance(enemy, self.bonus_class):
            might = self.might + (self.might / 10)
            print("%s is advantaged over %s" % (self.bonus_class.__name__, enemy.__class__.__name__))
        else:
            might = self.might

        for effect in self.effective:
            if isinstance(effect, enemy):
                might += might / 10

        return might


class Sword(Weapon):
    pass


class Lance(Weapon):
    pass


class Axe(Weapon):
    pass


Sword.bonus_weapons.append(Axe)
Lance.bonus_weapons.append(Sword)
Axe.bonus_weapons.append(Lance)


class Bow(Weapon):
    pass


class LightTome(Weapon):
    pass


class DarkTome(Weapon):
    pass


class AnimaTome(Weapon):
    pass


class Staff(Weapon):
    pass


class Armour(Item):
    """
    Not used yet.
    """
    def __init__(self, name, rank, defence, weight, uses, worth, exp, effective, descr=""):
        super().__init__(name, worth, descr)
        self.rank       =    rank        # rank necessary to use it
        self.defence    =    int(defence)# damage
        self.weight     =    int(weight)    # weight affects on speed
        self.exp        =    int(exp)    # exp increases unit's weapon rank
        self.effective    =    effective

    def __str__(self):
        return """
Armour "%s":
    Description: "%s"
    Rank: %c
    Defence: %d
    Weight: %d
    Uses: %d/%d
    Worth: %d
    Exp: %d
""" % (self.name, self.descr, self.rank, self.defence, self.weight,
        self.uses, self.muses, self.worth, self.exp)

