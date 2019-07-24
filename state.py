"""

"""


import display
import map


loaded_map: map.Map = None
units_manager = None
winner = None


def load_map(map_path):
    global loaded_map, units_manager, winner

    size = display.get_size()
    winner = None
    loaded_map = map.Map(map_path, w=size[0]-250, h=size[1])
    units_manager = loaded_map.units_manager
