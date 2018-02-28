import logging
import pygame
import events
import ai
import room
import traceback
import gui
import fonts as f
import map


loaded_map = None
units_manager = None
winner = None


def load_map(map_path):
    global loaded_map, units_manager
    try:
        loaded_map = map.Map(map_path)
        units_manager = loaded_map.units_manager
        for team in units_manager.teams:
            if team.ai:
                team.ai = ai.AI(loaded_map, units_manager, team)
        events.register(pygame.locals.VIDEORESIZE, loaded_map.handle_videoresize)
    except:
            msg = _("Can't load map %s! Probably the format is not ok.\n%s") % (map_path, traceback.format_exc())
            logging.error(msg)
            room.run_room(gui.Dialog(msg, f.SMALL_FONT, pos=(100, 100)))

def kill(unit):
    loaded_map.kill_unit(unit=unit)
    units_manager.kill_unit(unit)

