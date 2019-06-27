class Mosquito:
    n = 3*750
    
    cluster = True
    cluster_chance = 0.6
    
    move_chance = 0.05
    bite_chance = 0.35
    
    # https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5230737/; http://www.njmonline.nl/getpdf.php?id=285
    human_infection_chance = 0.68 
    fed_hunger = -10
    base_bite_nutrition = 5
    
    age_death_factor = 0.0008
    death_base = 0.003
    
    simple_death_chance = 0.01
    
    reproduction_chance = 0.015
    
    vax_rate = 0.05
    
    
class Human:
    n = 4*200
    dens = 0.15
    populate_absolute = False
    cluster = True
    cluster_chance = 0.8
    resettle_chance = 0.3
    
    mosquito_infection_chance = 0.55
    pre_infection_prob = 0.1
    
    age_death_factor = 0.000001
    death_base = 0.00001
    
    resistance_base = 0.00001
    infection_resistance_factor = 0.000005
    
    malaria_death_chance = 0.0008
    
    use_net_chance = 0.1
    
class Grid:
    size = (60, 60)
