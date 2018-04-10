"""

"""


import display
import map


loaded_map = None
units_manager = None
winner = None


def load_map(map_path):
    global loaded_map, units_manager

    size = display.get_size()
    loaded_map = map.Map(map_path, w=size[0]-250, h=size[1])
    units_manager = loaded_map.units_manager

def kill(unit):
    global winner
    loaded_map.kill_unit(unit=unit)
    units_manager.kill_unit(unit)

