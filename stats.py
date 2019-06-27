import inspect
import matplotlib.pyplot as plt


def stat_fn(m):
    def decorator(fn):
        fn._modes = m
        fn._is_stat_fn = True
        return fn
    return decorator

def is_stat_fn(fn):
    return hasattr(fn, "_is_stat_fn")

class SimStats():
    """
    Keeps stats for all actors in the current simulation
    """
    def __init__(self, sim):
        self.stat_fns = inspect.getmembers(self, predicate=is_stat_fn)
        
        self.data = {}
        self.init_data()
        self.sim = sim

    def init_data(self):
        for f_name, f in self.stat_fns:
            self.data[f_name] = {}
            for m in f._modes:
                self.data[f_name][m] = []
        
    @stat_fn("hm")
    def population(self, mode):
        f = "is_human" if mode == 'h' else "is_mosquito" if mode == 'm' else None
        if not f: return 0
        n = 0
        for a in self.sim.actors:
            if getattr(a, f)():
                n += 1
        return n
    
    @stat_fn("hm")
    def infected_absolute(self, mode):
        f = "is_human" if mode == 'h' else "is_mosquito" if mode == 'm' else None
        if not f: return 0
        n = 0
        for a in self.sim.actors:
            if getattr(a, f)() and a.infected:
                n += 1
        return n
    
    @stat_fn("hm")
    def infected_percentage(self, mode):
        return (self.infected_absolute(mode) / self.population(mode)) * 100
    
    @stat_fn("h")
    def resistance_percentage(self, mode):
        n = 0
        for a in self.sim.actors:
            if getattr(a, 'is_human')() and a.immune:
                n += 1
        return (n / self.population(mode)) * 100
        
    @stat_fn("hm")
    def vaccinated_percentage(self, mode):
        f = "is_human" if mode == 'h' else "is_mosquito" if mode == 'm' else None
        if not f: return 0
        n = 0
        for a in self.sim.actors:
            if getattr(a, f)() and a.vaccinated:
                n += 1
        return (n / self.population(mode)) * 100
        
    def step(self):
        for f_name, f in self.stat_fns:
            for m in f._modes:
                self.data[f_name][m].append(f(m))
        
    def plot(self, stat, mode, t_start=0, t_end=None, save_fig=False):
        t_end = t_end or self.sim.t
        plt.clf()
        for m in mode:
            plt.plot(range(t_start, t_end), self.data[stat][m])
        plt.xlabel('time')
        plt.ylabel(stat)
        plt.legend(mode)
        plt.show()
        if save_fig:
            plt.savefig(f"plots/plot_{stat}_{mode}_{t_start}-{t_end}.png")
            
    def dump(self, path):
        pass