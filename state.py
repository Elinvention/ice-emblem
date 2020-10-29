"""

"""

from typing import Union

import display
import map
import unit


loaded_map: Union[None, map.Map] = None
units_manager: Union[None, unit.UnitsManager] = None
winner: Union[None, unit.Team] = None


def load_map(map_path):
    global loaded_map, units_manager, winner

    size = display.get_size()
    winner = None
    loaded_map = map.Map(map_path, w=size[0]-250, h=size[1])
    units_manager = loaded_map.units_manager
