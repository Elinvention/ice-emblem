"""
This module deals with "low level" handling of pygame.display.
"""

import pygame

import resources
import utils
import colors as c

import math

from typing import Tuple


resolution = (1280, 720)
min_resolution = (800, 600)
fps = 60
mode = pygame.RESIZABLE
spinner_angle = 0
spinner_size = (15, 15)


def initialize() -> None:
    """
    Must be called first to initialize pygame and this module.
    """
    global window, clock, FPS_FONT
    if pygame.get_init():
        return
    pygame.mixer.pre_init(frequency=44100, size=-16, channels=2)
    pygame.init()
    pygame.display.set_icon(resources.load_image('icon.png'))
    version = utils.get_version()

    window = pygame.display.set_mode(resolution, mode)
    pygame.display.set_caption("Ice Emblem " + version)
    pygame.key.set_repeat(200, 50)
    clock = pygame.time.Clock()

    FPS_FONT = pygame.font.SysFont("Liberation Sans", 12)


def modeset() -> None:
    """
    Create a window.
    """
    global window
    window = pygame.display.set_mode(resolution, mode)


def set_fullscreen(enable) -> None:
    """
    Makes the window fullscreen or resizable.
    :param enable: True -> make fullscreen window, False -> make resizable window
    :return: None
    """
    global mode
    mode = pygame.FULLSCREEN if enable else pygame.RESIZABLE
    modeset()


def toggle_fullscreen() -> None:
    """
    Makes the windows fullscreen if it is resizable and viceversa.
    """
    global mode
    mode = pygame.FULLSCREEN if mode != pygame.FULLSCREEN else pygame.RESIZABLE
    modeset()


def set_resolution(res: Tuple[int, int]):
    """
    Changes window resolution.
    :param res: resolution as a Tuple[int, int]
    """
    global resolution
    resolution = res
    modeset()
    pygame.event.post(pygame.event.Event(pygame.VIDEORESIZE, size=res, w=res[0], h=res[1]))


def handle_videoresize(event: pygame.event.EventType) -> None:
    """
    Handles pygame.VIDEORESIZE events.
    :param event: a pygame.VIDEORESIZE event
    """
    global window
    screen_size = event.size
    if screen_size[0] < min_resolution[0]:
        screen_size = (min_resolution[0], screen_size[1])
    if screen_size[1] < min_resolution[1]:
        screen_size = (screen_size[0], min_resolution[1])
    window = pygame.display.set_mode(screen_size, mode)


def draw_fps(font=None) -> None:
    """
    Draws an FPS counter and a spinner.
    :param font: the font to use to render the counter. There is a default font if not specified.
    """
    global spinner_angle
    if not font:
        font = FPS_FONT
    screen_w, screen_h = window.get_size()
    fps = clock.get_fps()
    fpslabel = font.render('%d FPS' % int(fps), True, c.WHITE, c.BLACK).convert()
    rec = fpslabel.get_rect(top=5, right=screen_w - 5 - spinner_size[0])
    window.blit(fpslabel, rec)

    spinner_angle -= math.pi / 4
    spinner_angle %= math.pi * 2
    surf = pygame.Surface(spinner_size)
    pygame.draw.arc(surf, c.WHITE, surf.get_rect(), spinner_angle, spinner_angle + math.pi / 4, 2)
    window.blit(surf, surf.get_rect(top=5, right=screen_w - 5))


def tick(_fps=None) -> None:
    """
    Wait to reach target fps.
    :param _fps: target fps
    """
    if _fps is None:
        return clock.tick(fps)
    return clock.tick(_fps)


def flip() -> None:
    """
    Equivalent to pygame.display.flip()
    """
    pygame.display.flip()


def get_rect(**kwargs) -> pygame.Rect:
    """
    Returns window's rect.
    :param kwargs: same as pygame.Surface.get_rect()
    """
    return window.get_rect(**kwargs)


def get_size() -> Tuple[int, int]:
    """
    Returns window size.
    :return: size as (width, height).
    """
    return window.get_size()


def get_width() -> int:
    """
    Same as get_size()[0].
    :return: window width.
    """
    return window.get_width()


def get_height() -> int:
    """
    Same as get_size()[1].
    :return: window height
    """
    return window.get_height()


def darken(alpha) -> None:
    """
    Makes the whole window darker depending on alpha factor.
    :param alpha: int from 0 to 255 representing how much darker to make the window. 0 means no darkening. 255 means go
    dark abruptly.
    """
    s = pygame.Surface(window.get_size())
    s.fill((0, 0, 0))
    s.set_alpha(alpha)
    window.blit(s, (0, 0))
