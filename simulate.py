import config
import random
from mixins import *
from stats import SimStats
from collections import defaultdict
from event import Event
import itertools


class Human(Actor, Infectable, NaturalDeath, MalariaDeath):
    """ Represents a human. """
    def __init__(self, *a, use_net=False, **k):
        self.use_net = use_net

    def step(self):
        # Check if human will develop immunity
        if self.infected:
            resistance_chance = self.config.resistance_base + self.infection_count * self.config.infection_resistance_factor
            if random.random() < resistance_chance:
                self.immune = True

        self.all_super_step()

    def end_step(self):
        """ Runs end-of-step functions (such as death) """
        self.all_super_end_step()

    def get_bitten(self, mosquito):
        if mosquito.vaccinated:
            self.vaccinated = True
            self.infected = False
            self.immune = False

        if not mosquito.infected and not self.infected:
            return

        if self.vaccinated:
            return

        if self.use_net:
            return

        if (self.infected and random.random() <
            self.config.mosquito_infection_chance):
            mosquito.infect()

        if mosquito.infected and random.random() < mosquito.config.human_infection_chance:
            self.infect()


class Mosquito(Actor, Hunger, Infectable, SimpleDeath):
    """ Represents a mosquito. """
    possible_moves = [i for i in itertools.product((0, 1, -1), (0, 1, -1))
                      if i != (0, 0)]

    def __init__(self, *a, has_vaccine, **kwa):
        self.vaccinated = has_vaccine

    def will_bite(self):
        r = random.random()
        max_hunger = -self.config.fed_hunger
        chance = self.config.bite_chance
        if self.hunger < 0:
            return False
        else:
            return r < chance * (self.hunger / max_hunger)

    def step(self):
        if random.random() < self.config.move_chance:
            self.move()
        if self.will_bite():
            self.bite()
        if random.random() < self.config.reproduction_chance and False:
            # Yes, this never executes. We need to keep the if-statement in,
            # because the random.random() call influences the random state.
            self.sim.spawn_actor(Mosquito, self.sim.grid.get_square(self))

        self.all_super_step()

    def end_step(self):
        self.all_super_end_step()

    def move(self):
        """ Moves the mosquito to an adjacent grid square. """
        orig_sq = self.sim.grid.get_square(self)
        new_sq = orig_sq

        x_off, y_off = random.choice(self.possible_moves)

        x, y = orig_sq.pos

        try:
            new_sq  = self.sim.grid[x + x_off, y + y_off]
            orig_sq.remove(self)
            new_sq.add(self)
        except ValueError:
            pass

    def bite(self):
        """
        Bites a human, if the square containing the mosquito contains one.
        """
        if self.hunger < 0:
            return

        own_square = self.sim.grid.get_square(self)

        for actor in own_square:
            if actor.is_human():
                nut_value = random.random()*(self.config.fed_hunger - self.config.base_bite_nutrition)
                self.hunger -= self.config.base_bite_nutrition + nut_value
                actor.get_bitten(self)



class GridSquareProxy:
    """
    Represents a square in the grid. Actors can be added to or removed from the
    square, tested for membership, and the square can be iterated over.
    """
    def __init__(self, grid, *pos):
        self.grid = grid
        self.pos  = pos

    def add(self, obj):
        self.grid[obj] = self.pos
        self.grid[self.pos].add(obj)

    def remove(self, obj):
        del self.grid[obj]
        self.grid[self.pos].remove(obj)

    def __contains__(self, obj):
        return obj in self.grid[self.pos]

    def __iter__(self):
        return iter(self.grid[self.pos])

    def __bool__(self):
        return bool(self.grid[self.pos])

    def __repr__(self):
        return f"Grid square at {self.pos} containing ({self.grid[self.pos]})"


class Grid:
    """
    Represents an NxM grid that actors are placed in.
    """
    def __init__(self, x_max, y_max):
        self.x_max, self.y_max = x_max, y_max
        self._grid = defaultdict(set)
        self.indices = [*itertools.product(range(x_max), range(y_max))]

    def get_square(self, obj):
        if obj not in self._grid:
            raise ValueError(f"{obj} is not in the grid!")

        return GridSquareProxy(self._grid, *self._grid[obj])


    def __getitem__(self, index):
        x, y = index
        if (x < 0 or x >= self.x_max or y < 0 or y >= self.y_max):
            raise ValueError("Cannot get square outside of the grid.")
        return GridSquareProxy(self._grid, *index)

    def get_random_square(self, predicate=None):
        if not predicate:
            x, y = random.choice(self.indices)
            return GridSquareProxy(self._grid, x, y)

        squares_matching_predicate = [k for k in self.indices
                                      if predicate(self._grid[k])]
        return GridSquareProxy(self._grid, *random.choice(squares_matching_predicate))

def not_contains_class(cls):
    """
    Returns a function which checks whether an iterable contains a class.
    If so, returns False. Otherwise, returns True.
    """
    def fn(actors):
        return not any(isinstance(actor, cls) for actor in actors)
    return fn

class Simulation:
    """
    Represents a simulation with actors in a Cartesian grid.
    """
    def __init__(self, config):
        self.config = config
        self.grid = Grid(*config.Grid.size)
        self.stats = SimStats(self)
        self.t = 0
        self.spawned_mosquitos = False
        self.vax_mosquitos = False
        self.use_net = False

        self.actors = []

        self.populate_grid()


    def init_grid(self):
        for x in range(self.grid.x_max):
            for y in range(self.grid.y_max):
                if (x % 2 == 0):
                    obj = Mosquito(self, self.config)
                else:
                    obj = Human(self, self.config)
                self.grid[x, y].add(obj)

    def step(self):
        self.t += 1
        self.stats.step()

        # Shallow copy, dus gewoon 8*n byte copy
        current_actors = self.actors.copy()
        for actor in current_actors:
            actor.step()
            actor.end_step()

    def populate_grid(self):
        self.populate_human()
        self.populate_mosquito()

    def populate_human(self):
        first_human = True
        n = round(self.config.Human.dens * (self.grid.x_max * self.grid.y_max))
        for i in range(self.config.Human.n if self.config.Human.populate_absolute else n):
            obj = self.new_human()

            if first_human:
                obj.infect()
                first_human = False
            elif random.random() < self.config.Human.pre_infection_prob:
                obj.infect()

    def populate_mosquito(self):
        for i in range(self.config.Mosquito.n):
            obj = self.new_mosquito()

    def handle_death(self, obj):
        cur_square = self.grid.get_square(obj)
        self.actors.remove(obj)
        self.grid.get_square(obj).remove(obj)
        if obj.is_human():
            if random.random() < self.config.Human.resettle_chance:
                self.new_human()
            else:
                use_net = False

                if self.use_net and random.random() < self.config.Human.use_net_chance:
                    use_net = True

                self.spawn_actor(Human, cur_square, use_net=use_net)
        else:
            self.new_mosquito()

    def new_human(self):
        square = None
        if self.config.Human.cluster and random.random() < self.config.Human.cluster_chance:
            neigh_coords = [*itertools.product((-1, 0, 1), (-1, 0, 1))]
            neigh_coords.remove((0, 0))
            humans = [*filter(Actor.is_human, self.actors)]
            random.shuffle(humans)
            for h in humans:
                x_h, y_h = self.grid.get_square(h).pos
                for x_off, y_off in neigh_coords:
                    try:
                        t_square = self.grid[x_h + x_off, y_h + y_off]
                        if not_contains_class(Human)(t_square):
                            square = t_square
                            break
                    except ValueError:
                        pass
                if square:
                    break
        if square is None:
            if self.spawned_mosquitos:
                square = self.grid.get_random_square(predicate=not_contains_class(Human))
                pass
            else:
                while True:
                    index = random.randrange(self.grid.x_max), random.randrange(self.grid.y_max)
                    if not self.grid[index]:
                        square = self.grid[index]
                        break

        use_net = False

        if self.use_net and random.random() < self.config.Human.use_net_chance:
            use_net = True

        return self.spawn_actor(Human, square, use_net=use_net)

    def new_mosquito(self):
        if (self.spawned_mosquitos and self.config.Mosquito.cluster and
            random.random() < self.config.Mosquito.cluster_chance):
                square = self.grid.get_square(random.choice([*filter(Actor.is_mosquito, self.actors)]))
        else:
            self.spawned_mosquitos = True
            square = self.grid.get_random_square()
        vaccinated = self.vax_mosquitos and random.random() < self.config.Mosquito.vax_rate
        return self.spawn_actor(Mosquito, square, vaccinated)

    def spawn_actor(self, cls, square, vax=False, use_net=False):
        obj = cls(self, self.config, has_vaccine=vax, use_net=use_net)
        square.add(obj)
        self.actors.append(obj)
        return obj

    def num_actors(self):
        return len(self.actors)
