import json
import random
import requests
import copy

# HILL CLIMBER ALGORITHM

# Generate and score initial solution

# Generate and score all neighbours

# If Neighbour > Current - Climb the hill

# Else terminate run

GAME = 'ExplodingKittens'
PORT= 5173
URL_BASE = f"http://localhost:{PORT}/api/"
RUN_TYPE = 'fast'

with open('valid_params.json', 'r') as file:
    params = json.load(file)
    game_params = params[GAME]

max_index = [len(game_params[param]) - 1 for param in game_params]

assert len(max_index) == len(game_params)

headers = ['score'] + list(game_params.keys())
random.seed(1)

def solution_to_params(solution: list[int]):
    
    chosen_params = {}

    for i, param_name in enumerate(game_params):
        parameter = game_params[param_name]
        value = parameter[solution[i]]

        chosen_params[param_name] = value

    return chosen_params

def run_game(solution: list[int], game: str = GAME, run_type: str = RUN_TYPE) -> tuple[list[int], dict, float]:

    params = solution_to_params(solution)
    url = f"{URL_BASE}run_game"
    headers = {'Content-Type': 'application/json'}
    body = {
        "game": game,
        "params": params,
        "run_type": run_type
    }
    response = requests.post(url, json=body, headers=headers)
    return solution, params, response.json()['score']

def generate_neighbours(solution) -> list[list[int]]:
    neighbours = []

    for i, value in enumerate(solution):
        if value > 0:
            neighbour = copy.deepcopy(solution)
            neighbour[i] = value - 1
            neighbours.append(neighbour)
        if value < max_index[i]:
            neighbour = copy.deepcopy(solution)
            neighbour[i] = value + 1
            neighbours.append(neighbour)
    
    return neighbours

def hill_climber():
    print(f'Starting Hill Climbing.')
    initial_solution = [random.randint(0, max_index[i]) for i in range(len(game_params))]
    _, params, score = run_game(initial_solution)
    print(f'Initial Parameters: {params}')
    print(f'Initial Score: {score}')

    terminate = False
    best_solution = {'solution': initial_solution, 'params': params, 'score': score}
    i = 1
    
    while not terminate:
        print(f'Iteration {i}')
        i += 1
        terminate = True

        neighbours = generate_neighbours(best_solution['solution'])
        print(f'Found {len(neighbours)} neighbours.')
        for neighbour in neighbours:
                
                sol, params, score = run_game(neighbour)
                params['score'] = score

                if score > best_solution['score']:
                    best_solution = {'solution': sol, 'params': params, 'score': score}
                    print(f'New best solution found:')
                    print(f'    Parameters: {best_solution["params"]}')
                    print(f'    Score: {best_solution["score"]}')
                    terminate = False
        
    print(f"Hill Climbing Finished")
    print(f'Best solution found:')
    print(f'    Parameters: {best_solution["params"]}')
    print(f'    Score: {best_solution["score"]}')

if __name__ == "__main__":
    hill_climber()


