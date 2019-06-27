from mixin_base import MixinBase
from event import Event
import random

class Infectable(MixinBase):
    """
    Mixin that keeps track of an actor's infection status,
    and allows other actors to infect the actor.
    """
    def __init__(self, sim, config, *args, **kwargs):
        self.infected = False
        self.infection_count = 0
        self.infection_time = 0
        self.immune = False
        self.vaccinated = False
        self.use_net = False
        
    def infect(self):
        if self.vaccinated:
            return
        if not self.infected:
            self.infection_time = self.sim.t
        self.infected = True
        self.infection_count += 1

class Death(MixinBase):
    """
    Mixin that keeps track of an actor's death status. Also contains
    an event allowing other objects to hook the actor's death.
    """
    def __init__(self, *a, **kwa):
        self.age = 0
        self._dead = False
        self.on_death = Event('on_death')
        self.on_death.hook(self.sim.handle_death)
        
    def end_step(self):
        if self._dead:
            self.on_death.fire(self)

class NaturalDeath(Death):
    """
    """
    def step(self):
        die_chance = self.age * self.config.age_death_factor + self.config.death_base
        
        if random.random() < die_chance:
            self._dead = True
            
        self.age += 1


class SimpleDeath(Death):
    """
    Mixin that represents 'simple' death, i.e. a single chance
    which is checked every timestep that determines whether an actor dies.
    """
    def step(self):
        if random.random() < self.config.simple_death_chance:
            self._dead = True


class MalariaDeath(Death):
    """
    Mixin that represents death by malaria.
    """
    def __init__(self, *a, **kwa):
        pass
    
    def step(self):
        if not self.infected or self.immune:
            return
        
        dur_fac = (self.sim.t - self.infection_time) / 10000
        if not self.immune and random.random() < self.config.malaria_death_chance + dur_fac:
            self._dead = True
            
class Hunger(MixinBase):
    """ Mixin that keeps track of an actor's hunger. """
    def __init__(self, sim, config, *args, **kwargs):
        T = type(self)
        self.hunger = self.config.fed_hunger
        
    def step(self):
        self.hunger += 1
