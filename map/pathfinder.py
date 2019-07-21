"""

"""


import heapq


class Terrain(object):
    def __init__(self, tile, unit):
        self.name = tile.properties.get('name', 'Unknown')
        self.moves = float(tile.properties.get('moves', 1))  # how many moves are required to move a unit through
        self.defense = int(tile.properties.get('defense', 0))  # bonus defense
        self.avoid = int(tile.properties.get('avoid', 0))  # bonus avoid
        self.allowed = tile.properties.get('allowed', 'earth').split(',')
        self.surface = tile.surface
        self.unit = unit


class Pathfinder(object):
    """Cached pathfinder"""
    def __init__(self, _map):
        self.map = _map
        self.w, self.h = self.map.w, self.map.h
        self.reset()

    def reset(self):
        self.source = None  # int tuple: dijkstra executed with this node as source
        self.target = None  # int tuple: shortest path target
        self.shortest = None  # list: shortest path output
        self.max_distance = None  # float
        self.dist = None  # dict: results of dijkstra
        self.prev = None
        self.enemies = None  # bool: treat enemies as obstacles

    def __set_source(self, source, enemies=True):
        """
        Implementation of Dijkstra's Algorithm.
        See https://en.wikipedia.org/wiki/Dijkstra%27s_algorithm for
        reference.
        This method computes the distance of every node of the map from
        a given source node.
        """
        self.shortest = None
        self.source = source
        self.enemies = enemies

        # Unknown distance function from source to v
        self.dist = {(x, y): float('inf') for y in range(self.h) for x in range(self.w)}
        # Previous node in optimal path from source initialization
        self.prev = {(x, y): None for y in range(self.h) for x in range(self.w)}

        self.dist[source] = 0  # Distance from source to source

        # All nodes initially in Q (unvisited nodes)
        Q = [v for v in self.dist]

        source_unit = self.map[source].unit if enemies else None

        while Q:
            min_dist = self.dist[Q[0]]
            u = Q[0]

            for el in Q:
                if self.dist[el] < min_dist:
                    min_dist = self.dist[el]
                    u = el  # Source node in first case

            Q.remove(u)

            # where v has not yet been removed from Q.
            for v in self.map.neighbors(u):
                alt = self.dist[u] + self.map[v].moves
                if alt < self.dist[v]:
                    # A shorter path to v has been found
                    if self.map.is_obstacle(v, source_unit):
                        # v is an obstacle set infinite distance (unreachable)
                        self.dist[v] = float('inf')
                        # we still want to be able to find a path
                        if not self.prev[v]:
                            self.prev[v] = [(alt, u)]
                        else:  # keep the shortest first
                            heapq.heappush(self.prev[v], (alt, u))
                    else:
                        self.dist[v] = alt
                        self.prev[v] = u

    def __set_target(self, target, max_distance=float('inf'), enemies=True):
        """
        This method sets the target node and the maximum distance. The
        computed path total cost will not exceed the maximim distance.
        The shortest path between target and source previously specified
        with __set_source is returned as a list.
        """
        self.max_distance = max_distance
        S = []
        u = self.target = target
        self.enemies = enemies

        # Construct the shortest path with a stack S
        while self.prev[u] is not None:
            if self.dist[u] <= max_distance:
                S.insert(0, u)  # Push the vertex onto the stack
            try:
                u = self.prev[u][0][1]  # get the shorter path
            except TypeError:
                u = self.prev[u]  # Traverse from target to source

        s_unit = self.map[self.source].unit if enemies else None
        for coord in reversed(S):
            unit = self.map[coord].unit
            if unit or self.map.is_obstacle(coord, s_unit):
                del S[-1]
            else:
                break

        self.shortest = S
        return S

    def shortest_path(self, source, target, max_distance=float('inf'), enemies=True):
        if self.source != source or self.enemies != enemies:
            self.__set_source(source, enemies)
            self.__set_target(target, max_distance, enemies)
        elif self.target != target or self.max_distance != max_distance or self.enemies != enemies:
            self.__set_target(target, max_distance, enemies)
        return self.shortest

    def area(self, source, max_distance, enemies=True):
        """
        Returns a list of coords
        """
        if self.source != source or self.enemies != enemies:
            self.__set_source(source, enemies)
            self.target = None
            self.shortest = None
        h, w = range(self.h), range(self.w)
        return [(i, j) for j in h for i in w if self.dist[(i, j)] <= max_distance]


def manhattan_path(source, target):
    yield source
    if source[0] < target[0]:
        yield from manhattan_path((source[0] + 1, source[1]), target)
    elif source[0] > target[0]:
        yield from manhattan_path((source[0] - 1, source[1]), target)
    elif source[1] < target[1]:
        yield from manhattan_path((source[0], source[1] + 1), target)
    elif source[1] > target[1]:
        yield from manhattan_path((source[0], source[1] - 1), target)
