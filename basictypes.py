"""
Basic types definitions used all over Ice Emblem's code base
"""


import pygame


class Point(tuple):
    """
    A tuple with more convenient operators to use for points
    """
    def __new__(cls, *args):
        return tuple.__new__(cls, *args)
    def __add__(self, other):
        return Point(int(x + y) for x, y in zip(self, other))
    def __sub__(self, other):
        return self.__add__(int(-i) for i in other)
    def __neg__(self):
        return Point(int(-x) for x in self)
    def __mul__(self, other):
        return Point(int(x * other) for x in self)
    def __truediv__(self, other):
        return Point(int(x / other) for x in self)
    def __floordiv__(self, other):
        return Point(int(x // other) for x in self)
    def __repr__(self):
        return f'({"; ".join(str(x) for x in self)})'
    def norm(self):
        return sum(abs(x) for x in self)

    def normalized(self):
        return self / self.norm()

    def __getattr__(self, attr):
        try:
            return self[['x', 'y', 'z', 'w'].index(attr)]
        except (IndexError, ValueError):
            raise AttributeError('%s is not an attribute of this Point' % attr)


class Rect(pygame.Rect):
    """
    Improved pygame's Rect
    """
    def __init__(self, **kwargs):
        if 'rect' in kwargs:
            super().__init__(kwargs['rect'])
        else:
            super().__init__(0, 0, 0, 0)
        self.settings = {k: v for k, v in kwargs.items() if not k.startswith('_') and k in dir(self)}
        self.apply()

    def apply(self):
        for attr in self.settings:
            setattr(self, attr, self.settings[attr])


if __name__ == '__main__':
    p = Point((10, 0)).normalized()
    q = Point((1, 0, 2, 3))
    def test_getattr(point):
        for attr in ['x', 'y', 'z', 'w', 'a']:
            try:
                print(getattr(point, attr))
            except AttributeError as e:
                print(e)
    test_getattr(p)
    test_getattr(q)
    print(p, q)
    print("END")
