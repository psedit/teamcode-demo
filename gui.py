import curses
from simulate import Simulation, Human, Mosquito
import config
import importlib
import os
import time
import random
import sys
import pickle

class ResetException(Exception):
    pass



class Gui:
    def __init__(self, config):
        self.config = config
        self.stdscr = curses.initscr()
        if not curses.has_colors():
            raise RuntimeError("Your terminal must support colors!")
        curses.start_color()

        self.verify_screen_size()
        
        required_colors = [
            0,      #1
            46,    #2   (vaccinated, green)
            148,    #3
            142,    #4
            136,    #5
            130,    #6
            202,    #7 (infected - orange)
            196,     #8  (resistant, but infected - red)
            
            226,    #9 
            220,    #10
            214,    #11
            208,    #12
            202,    #13
            
            196,    #14
            51,    #15 light blue (netted)
            ]
        
        for i in range(1, len(required_colors)+1):
            curses.init_pair(i, required_colors[i-1], 0)
            curses.init_pair(i + 128, required_colors[i-1], 236)
            
        curses.init_pair(128, 250, 236)
        
        curses.noecho()
        curses.cbreak()
        self.stdscr.keypad(True)
        
        self.running = True
        self.n = 0
        self.step_delay = 0.0025
        self.frameskip = 0
        
    def verify_screen_size(self):
        """ Verifies that the terminal we are running in is large enough. """
        height, width = self.stdscr.getmaxyx()
        
        grid_x, grid_y = self.config.Grid.size
    
        required_x = 2*grid_x + 24 # sidebar
        required_y = grid_y + 2
        
        if (required_x > width or required_y > height):
            self.cleanup()
        
            print("Your terminal is too small.")
            print("The required terminal size for this configuration is: "
                  f"{required_x} columns, {required_y} lines.")
            print(f"Your current terminal size is: {width} columns, "
                  f"{height} lines.")
              
            raise SystemExit
        
    def init_sim(self):
        self.stdscr.addstr(0, 0, "Initialising simulation...")
        self.stdscr.noutrefresh(); curses.doupdate()
        
        self.sim = Simulation(config)
        
        self.stats = {
            "Time": self.get_info(self.sim, "t"),
            "Step delay": self.get_info(self, "step_delay"),
            "Frameskip": self.get_info(self, "frameskip"),
            "Actors": self.get_info(self.sim, "num_actors", func=True,),
            "Human inf.rate": self.get_info(self.sim.stats, "infected_percentage", ['h'], True, True),
            "Acquired resistance": self.get_info(self.sim.stats, "resistance_percentage", ['h'], True, True),
            "Human vax.rate": self.get_info(self.sim.stats, "vaccinated_percentage", ['h'], True, True)
        }
        
    def get_info(self, obj, name, args=[], func=False, trunc=False,):
        if func:
            return getattr(obj, name), args, trunc
        else:
            def info():
                return getattr(obj, name)
            return info, args, trunc
        
    def run(self):
        self.init_sim()
        try:
            self.draw_border()
            self.draw()
            while self.running:
                self.handle_input()
        except curses.error:
            self.verify_screen_size()
        finally:
            self.cleanup()
        
    def cleanup(self):
        curses.nocbreak()
        curses.echo()
        self.stdscr.keypad(False)
        curses.endwin()
            
    def handle_input(self):
        c = self.stdscr.getch()
        
        if c == ord('n'):
            self.sim.step()
            self.draw()
            
        if c == ord('c'):
            self.stdscr.nodelay(True)
            
            mod = 1
            
            while True:
                time.sleep(self.step_delay)
                ch = self.stdscr.getch()
                if (ch == ord('c')):
                    break
                elif (ch == ord('+')):
                    self.step_delay /= 2
                elif (ch == ord('-')):
                    self.step_delay *= 2
                elif (ch == ord(',')):
                    self.frameskip = max(0, self.frameskip - 1)
                elif (ch == ord('.')):
                    self.frameskip += 1
                elif (ch == ord('v')):
                    self.sim.vax_mosquitos = True
                elif (ch == ord('k')):
                    self.sim.use_net = True
                    
                self.sim.step()
                if (self.sim.t % (1 + self.frameskip) == 0):
                    self.draw()
                self.stdscr.refresh()
            self.stdscr.nodelay(False)
            
        if c == ord('q'):
            self.running = False
            
        if c == ord('r'):
            raise ResetException()
            
        if c == ord('v'):
            self.sim.vax_mosquitos = True
            
        if c == ord('p'):
            self.plot_plots()
    
    def plot_plots(self):
        self.sim.stats.plot("population", "mh", save_fig=True)
        self.sim.stats.plot("infected_percentage", "mh", save_fig=True)
        self.sim.stats.plot("resistance_percentage", "h", save_fig=True)
        self.sim.stats.plot("vaccinated_percentage", "h", save_fig=True)
    
    def draw_border(self):
        for x in range(2*self.sim.grid.x_max + 21):
            if x == 2*self.sim.grid.x_max:
                continue
            self.put(0, x + 1, "═")
            self.put(self.sim.grid.y_max + 1, x + 1, "═")
        for y in range(self.sim.grid.y_max):
            self.put(y + 1, 0, "║")
            self.put(y + 1, 2*self.sim.grid.x_max + 1, "║")
            self.put(y + 1, 2*self.sim.grid.x_max + 22, "║")
        self.put(0, 0, "╔")
        self.put(0, 2*self.sim.grid.x_max + 1, "╦")
        self.put(self.sim.grid.y_max + 1, 0, "╚")
        self.put(self.sim.grid.y_max + 1, 2*self.sim.grid.x_max + 1, "╩")
        self.put(0, 2*self.sim.grid.x_max + 22, "╗")
        self.put(self.sim.grid.y_max + 1, 2*self.sim.grid.x_max + 22, "╝")
        self.put(0, 2, "Simulation:")
        self.put(0, 2*self.sim.grid.x_max + 3, "Statistics:")
        
    def draw_stats(self):
        x_off = 2*self.sim.grid.x_max + 2
        for i, (k, (f, args, trunc)) in enumerate(self.stats.items()):
            self.put(1 + i*3, x_off, f"{k}:")
            if args:
                val = f(*args)
            else:
                val = f()
            if trunc:
                self.put(2 + i*3, x_off, f"{val:.2f}")
            else:
                self.put(2 + i*3, x_off, f"{val}")
            self.stdscr.clrtoeol()
            self.put(3 + i*3, x_off - 1, "╠════════════════════╣")
        
    def put(self, y, x, str, *args):
        self.stdscr.addstr(y, x, str.encode('utf-8'), *args)
        
    def redefine_colors(self, bgcolor):
        for i in range(1, curses.COLORS):
            curses.init_pair(i, i, bgcolor)
        
    def draw(self):
        self.draw_stats()
        
        x_max, y_max = self.sim.grid.x_max, self.sim.grid.y_max
        for x in range(x_max):
            for y in range(y_max):
                COLOR_BASE = 0
                if (x % 2 == y % 2):
                    COLOR_BASE = 128
                    
                square = self.sim.grid[x, y]
                
                has_human = False
                has_mosquitos = False
                mosquito_infected = 0
                human_infected = False
                human_immune = False
                human_vaccinated = False
                human_use_net = False
                mosquito_vaccinated = False

                for actor in square:
                    if actor.is_mosquito():
                        has_mosquitos = True
                        if actor.infected:
                            mosquito_infected += 1
                        if actor.vaccinated:
                            mosquito_vaccinated = True
                    if actor.is_human():
                        has_human = True
                        if actor.infected:
                            human_infected = True
                        if actor.immune:
                            human_immune = True
                        if actor.vaccinated:
                            human_vaccinated = True
                        if actor.use_net:
                            human_use_net = True
                        
                color = curses.color_pair(COLOR_BASE)
                        
                if human_infected:
                    color = curses.color_pair(COLOR_BASE + 7)
                    
                if human_vaccinated:
                    color = curses.color_pair(COLOR_BASE + 2)
                    
                if human_immune:
                    color = curses.color_pair(COLOR_BASE + 8)
                    
                if human_use_net:
                    color = curses.color_pair(COLOR_BASE + 15)
                    
                self.put(y + 1, x*2 + 1, "H" if has_human else " ", color)
                
                args = [y + 1, x*2 + 2, "•" if has_mosquitos else " "]
                
                colors = [0, 9, 10, 11, 12, 13, 14]
                
                if mosquito_infected > 6:
                    mosquito_infected = 6
                    
                
                    
                color_pair = curses.color_pair(COLOR_BASE + colors[mosquito_infected])
                
                if mosquito_vaccinated:
                    color_pair = curses.color_pair(COLOR_BASE + 2)
                args.append(color_pair)
                
                self.put(*args)
                

def print_required_terminal_size(gui):
    grid_x, grid_y = gui.sim.config.Grid.size
    
    current_y, current_x = gui.stdscr.getmaxyx()
    
    required_x = 2*grid_x + 24 # sidebar
    required_y = 2*grid_y + 2
    
    print("Curses threw an error. Most likely, your terminal is too small.")
    print("The required terminal size for this configuration is: "
          f"{required_x} columns, {required_y} lines.")
    print(f"Your current terminal size is: {current_x} columns, "
          f"{current_y} lines.")
    
def gui_loop():
    global config
    while True:
        try:
            g = Gui(config)
            g.run()
        except ResetException:
            config = importlib.reload(config)
        except curses.error:
            print_required_terminal_size(g)
            break
        else:
            break

if __name__ == '__main__':
    args = sys.argv
    # Save/load the random state to generate deterministic runs.
    state = None
    for n, i in enumerate(sys.argv):
        if i == '--set-state':
            fname = sys.argv[n+1]
            with open(fname, 'rb') as f:
                state = pickle.load(f)
                random.setstate(state)
    if not state:
        # Only save the random state if we haven't just loaded one,
        # as we don't really need to duplicate it.
        state = random.getstate()
        with open(time.strftime("%d%m-%H%M%S.randomstate"), 'wb') as f:
            pickle.dump(state, f)
    gui_loop()
    
    