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
        if isinstance(other, int):
            return Point(int(x + other) for x in self)
        return Point(int(x + y) for x, y in zip(self, other))

    def __sub__(self, other):
        return self.__add__(int(-i) for i in other)

    def __neg__(self):
        return Point(int(-x) for x in self)

    def __abs__(self):
        return Point(abs(int(x)) for x in self)

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
        return self / self.norm() if self.norm() > 0 else self

    def __getattr__(self, attr):
        try:
            return self[['x', 'y', 'z', 'w'].index(attr)]
        except (IndexError, ValueError):
            raise AttributeError('%s is not an attribute of this Point' % attr)


class NESW(object):
    """
    North East South West. Used to specify padding, border and margin like HTML.
    """
    def __init__(self, *args):
        if len(args) == 1:
            args = args[0]
        if isinstance(args, int):
            self.n = self.e = self.s = self.w = args
        elif len(args) == 2:
            self.n = self.s = args[0]
            self.e = self.w = args[1]
        elif len(args) == 4:
            self.n: int = args[0]
            self.e: int = args[1]
            self.s: int = args[2]
            self.w: int = args[3]
        else:
            raise ValueError("'padding' should be either 1, 2 or 4 ints")

    def __repr__(self):
        return "(%d, %d, %d, %d)" % (self.n, self.e, self.s, self.w)

    @property
    def ns(self) -> int:
        return self.n + self.s

    @property
    def ew(self) -> int:
        return self.e + self.w

    @property
    def we(self) -> int:
        return self.ew

    @property
    def sn(self) -> int:
        return self.ns

    def __getitem__(self, index) -> int:
        return getattr(self, ['n', 'e', 's', 'w'][index])

    def grow(self, rect) -> pygame.Rect:
        rect = rect.move(-self.w, -self.n)
        rect.w += self.w + self.e
        rect.h += self.n + self.s
        return rect

    def shrink(self, rect) -> pygame.Rect:
        rect = rect.move(self.w, self.n)
        rect.w -= self.w + self.e
        rect.h += self.n + self.s
        return rect


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
