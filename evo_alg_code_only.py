import random
import requests
import json
from deap import base, creator, tools, algorithms

# Parameters
PORT= 3000
URL_BASE = f"http://localhost:{PORT}/api/"

# Load valid parameters
with open('valid_params.json', 'r') as f:
    VALID_PARAMS = json.load(f)

# Choose which game to optimize (change this as needed)
chosen_game = "Dominion"  # or "ExplodingKittens", "Wonders7", "CantStop"
game_params = VALID_PARAMS[chosen_game]


def run_game(game: str, params: dict, run_type: str) -> float:
    """
    Execute a game simulation by sending a POST request to the game server.

    Args:
        game (str): The name or identifier of the game to run.
        params (dict): Dictionary containing game parameters.
        run_type (str): The type of game run (e.g., 'fast').

    Returns:
        float: The score obtained from the game run.

    Raises:
        requests.exceptions.RequestException: If the HTTP request fails.
        ValueError: If the response cannot be parsed as JSON.
    """
    
    url = f"{URL_BASE}run_game"
    headers = {'Content-Type': 'application/json'}
    body = {
        "game": game,
        "params": params,
        "run_type": run_type
    }
    response = requests.post(url, json=body, headers=headers)
    return response.json()['score']

# Define the problem as a maximization problem
creator.create("FitnessMax", base.Fitness, weights=(1.0,))
creator.create("Individual", list, fitness=creator.FitnessMax)

def create_individual():
    """Create an individual representing indices into valid parameter options."""
    individual = []
    for param_name in game_params.keys():
        if param_name == "CARDS":
            # CARDS expects exactly 10 cards selected from available options
            card_indices = random.sample(range(len(game_params[param_name])), 10)
            individual.extend(card_indices)
        elif param_name == "wonders":
            # wonders expects 3-7 wonders selected from available options
            num_wonders = random.randint(3, 7)
            wonder_indices = random.sample(range(len(game_params[param_name])), num_wonders)
            # Pad with -1 to make fixed length (7), -1 means not selected
            wonder_indices.extend([-1] * (7 - num_wonders))
            individual.extend(wonder_indices)
        else:
            # Regular parameter - single index
            max_index = len(game_params[param_name]) - 1
            individual.append(random.randint(0, max_index))
    return creator.Individual(individual)

def individual_to_params(individual):
    """Convert an individual (list of indices) to a parameter dictionary."""
    params = {}
    param_names = list(game_params.keys())
    gene_index = 0
    
    for param_name in param_names:
        if param_name == "CARDS":
            # Extract 10 card indices and convert to card names
            card_indices = individual[gene_index:gene_index + 10]
            params[param_name] = [game_params[param_name][idx] for idx in card_indices]
            gene_index += 10
        elif param_name == "wonders":
            # Extract 7 wonder indices (some may be -1)
            wonder_indices = individual[gene_index:gene_index + 7]
            selected_wonders = [game_params[param_name][idx] for idx in wonder_indices if idx != -1]
            params[param_name] = selected_wonders
            gene_index += 7
        else:
            # Regular parameter - single index
            params[param_name] = game_params[param_name][individual[gene_index]]
            gene_index += 1
    
    return params

def fitness_function(individual):
    """Evaluate the fitness of an individual."""
    params = individual_to_params(individual)
    try:
        score = run_game(chosen_game, params, "fast")
        return (score,)  # DEAP expects a tuple
    except Exception as e:
        print(f"Error evaluating individual: {e}")
        return (0.0,)  # Return poor fitness on error

def mutate_individual(individual, indpb=0.1):
    """Mutate an individual by changing some indices to random valid values."""
    param_names = list(game_params.keys())
    gene_index = 0
    
    for param_name in param_names:
        if param_name == "CARDS":
            # Handle CARDS mutation - mutate individual card selections
            for i in range(10):
                if random.random() < indpb:
                    # Select a new random card that's not already selected
                    available_cards = list(range(len(game_params[param_name])))
                    current_cards = individual[gene_index:gene_index + 10]
                    current_cards_set = set(current_cards)
                    current_cards_set.discard(individual[gene_index + i])  # Remove current card
                    available_cards = [idx for idx in available_cards if idx not in current_cards_set]
                    if available_cards:
                        individual[gene_index + i] = random.choice(available_cards)
            gene_index += 10
        elif param_name == "wonders":
            # Handle wonders mutation
            for i in range(7):
                if random.random() < indpb:
                    if individual[gene_index + i] == -1:
                        # Currently not selected, maybe add one
                        if random.random() < 0.5:  # 50% chance to add
                            available_wonders = list(range(len(game_params[param_name])))
                            current_wonders = [idx for idx in individual[gene_index:gene_index + 7] if idx != -1]
                            available_wonders = [idx for idx in available_wonders if idx not in current_wonders]
                            if available_wonders:
                                individual[gene_index + i] = random.choice(available_wonders)
                    else:
                        # Currently selected, maybe remove or change
                        if random.random() < 0.3:  # 30% chance to remove
                            individual[gene_index + i] = -1
                        else:  # 70% chance to change to different wonder
                            available_wonders = list(range(len(game_params[param_name])))
                            current_wonders = [idx for idx in individual[gene_index:gene_index + 7] if idx != -1]
                            current_wonders_set = set(current_wonders)
                            current_wonders_set.discard(individual[gene_index + i])
                            available_wonders = [idx for idx in available_wonders if idx not in current_wonders_set]
                            if available_wonders:
                                individual[gene_index + i] = random.choice(available_wonders)
            gene_index += 7
        else:
            # Regular parameter mutation
            if random.random() < indpb:
                max_index = len(game_params[param_name]) - 1
                individual[gene_index] = random.randint(0, max_index)
            gene_index += 1
    
    return (individual,)

def crossover_structured(ind1, ind2, indpb=0.5):
    """Perform structured crossover that respects parameter boundaries."""
    param_names = list(game_params.keys())
    gene_index = 0
    
    for param_name in param_names:
        if param_name == "CARDS":
            # For CARDS, swap entire card sets or do partial swap
            if random.random() < indpb:
                # Swap some cards between parents while maintaining uniqueness
                cards1 = ind1[gene_index:gene_index + 10]
                cards2 = ind2[gene_index:gene_index + 10]
                
                # Randomly select positions to swap
                swap_positions = random.sample(range(10), random.randint(1, 5))
                for pos in swap_positions:
                    # Only swap if it doesn't create duplicates
                    if cards2[pos] not in [cards1[i] for i in range(10) if i != pos]:
                        if cards1[pos] not in [cards2[i] for i in range(10) if i != pos]:
                            cards1[pos], cards2[pos] = cards2[pos], cards1[pos]
                
                # Update individuals
                ind1[gene_index:gene_index + 10] = cards1
                ind2[gene_index:gene_index + 10] = cards2
            gene_index += 10
            
        elif param_name == "wonders":
            # For wonders, swap wonder selections
            if random.random() < indpb:
                wonders1 = ind1[gene_index:gene_index + 7][:]
                wonders2 = ind2[gene_index:gene_index + 7][:]
                
                # Simple swap of wonder arrays
                ind1[gene_index:gene_index + 7] = wonders2
                ind2[gene_index:gene_index + 7] = wonders1
            gene_index += 7
            
        else:
            # Regular parameter - simple swap
            if random.random() < indpb:
                ind1[gene_index], ind2[gene_index] = ind2[gene_index], ind1[gene_index]
            gene_index += 1
    
    return ind1, ind2

def crossover_parameter_block(ind1, ind2):
    """Crossover that swaps entire parameter blocks."""
    param_names = list(game_params.keys())
    gene_index = 0
    
    for param_name in param_names:
        if random.random() < 0.3:  # 30% chance to swap each parameter
            if param_name == "CARDS":
                # Swap entire card selections
                cards1 = ind1[gene_index:gene_index + 10]
                cards2 = ind2[gene_index:gene_index + 10]
                ind1[gene_index:gene_index + 10] = cards2
                ind2[gene_index:gene_index + 10] = cards1
                gene_index += 10
            elif param_name == "wonders":
                # Swap entire wonder selections
                wonders1 = ind1[gene_index:gene_index + 7]
                wonders2 = ind2[gene_index:gene_index + 7]
                ind1[gene_index:gene_index + 7] = wonders2
                ind2[gene_index:gene_index + 7] = wonders1
                gene_index += 7
            else:
                # Swap single parameter
                ind1[gene_index], ind2[gene_index] = ind2[gene_index], ind1[gene_index]
                gene_index += 1
        else:
            # Skip this parameter
            if param_name == "CARDS":
                gene_index += 10
            elif param_name == "wonders":
                gene_index += 7
            else:
                gene_index += 1
    
    return ind1, ind2

# Register functions with DEAP
toolbox = base.Toolbox()
toolbox.register("individual", create_individual)
toolbox.register("population", tools.initRepeat, list, toolbox.individual)
toolbox.register("evaluate", fitness_function)
toolbox.register("mate", crossover_parameter_block)  # Better for structured parameters
toolbox.register("mutate", mutate_individual)
toolbox.register("select", tools.selTournament, tournsize=3)

# Additional evolutionary algorithm functions
def run_optimization(population_size=50, generations=100, cx_prob=0.6, mut_prob=0.2):
    """Run the genetic algorithm optimization."""
    # Create initial population
    population = toolbox.population(n=population_size)
    
    # Evaluate initial population
    fitnesses = list(map(toolbox.evaluate, population))
    for ind, fit in zip(population, fitnesses):
        ind.fitness.values = fit
    
    # Evolution loop
    for gen in range(generations):
        print(f"Generation {gen + 1}/{generations}")
        
        # Select parents for reproduction
        offspring = toolbox.select(population, len(population))
        offspring = list(map(toolbox.clone, offspring))
        
        # Apply crossover
        for child1, child2 in zip(offspring[::2], offspring[1::2]):
            if random.random() < cx_prob:
                toolbox.mate(child1, child2)
                del child1.fitness.values
                del child2.fitness.values
        
        # Apply mutation
        for mutant in offspring:
            if random.random() < mut_prob:
                toolbox.mutate(mutant)
                del mutant.fitness.values
        
        # Evaluate offspring with invalid fitness
        invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
        fitnesses = map(toolbox.evaluate, invalid_ind)
        for ind, fit in zip(invalid_ind, fitnesses):
            ind.fitness.values = fit
        
        # Replace population
        population[:] = offspring
        
        # Print statistics
        fits = [ind.fitness.values[0] for ind in population]
        print(f"  Best: {max(fits):.3f}, Avg: {sum(fits)/len(fits):.3f}")
    
    # Return best individual
    best_ind = max(population, key=lambda x: x.fitness.values[0])
    return best_ind, individual_to_params(best_ind)

