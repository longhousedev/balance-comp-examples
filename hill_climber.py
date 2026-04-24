from tqdm import tqdm
import json
import random
import requests
import multiprocessing
import copy
import csv
import datetime 
from functools import partial

# HILL CLIMBER ALGORITHM

# Generate and score initial solution

# Generate and score all neighbours

# If Neighbour > Current - Climb the hill

# Else terminate run

# Save results to csv

# Speed up with multiprocessing


GAME = 'ExplodingKittens'
PORT= 5173
URL_BASE = f"http://localhost:{PORT}/api/"
RUN_TYPE = 'fast'
CONCURRENT_RUNS = 6
random.seed(1)

def solution_to_params(solution: list[int], game_params):
    
    chosen_params = {}

    for i, param_name in enumerate(game_params):
        parameter = game_params[param_name]
        value = parameter[solution[i]]

        chosen_params[param_name] = value

    return chosen_params

def run_game(solution: list[int], game_params, game: str = GAME, run_type: str = RUN_TYPE) -> tuple[list[int], dict, float]:

    params = solution_to_params(solution, game_params)
    url = f"{URL_BASE}run_game"
    headers = {'Content-Type': 'application/json'}
    body = {
        "game": game,
        "params": params,
        "run_type": run_type
    }
    response = requests.post(url, json=body, headers=headers)
    return solution, params, response.json()['score']

def generate_neighbours(solution, max_values) -> list[list[int]]:
    neighbours = []

    for i, value in enumerate(solution):
        if value > 0:
            neighbour = copy.deepcopy(solution)
            neighbour[i] = value - 1
            neighbours.append(neighbour)
        if value < max_values[i]:
            neighbour = copy.deepcopy(solution)
            neighbour[i] = value + 1
            neighbours.append(neighbour)
    
    return neighbours

def hill_climber():

    with open('valid_params.json', 'r') as file:
        params = json.load(file)
        game_params = params[GAME]

    max_index = [len(game_params[param]) - 1 for param in game_params]

    assert len(max_index) == len(game_params)

    headers = ['score'] + list(game_params.keys())

    now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    out_file = open(f'run_{now}.csv', 'w')
    writer = csv.DictWriter(out_file, fieldnames=headers)
    writer.writeheader()

    initial_solution = [random.randint(0, max_index[i]) for i in range(len(game_params))]
    _, params, score = run_game(initial_solution, game_params)
    print(f'Initial Score: {score}')

    params['score'] = score
    writer.writerow(params)

    terminate = False
    best_solution = {'solution': initial_solution, 'params': params, 'score': score}
    i = 1
    
    while not terminate:
        print(f'Iteration {i}')
        i += 1
        terminate = True

        with multiprocessing.Pool(CONCURRENT_RUNS) as p:
            neighbours = generate_neighbours(best_solution['solution'], max_index)

            score_neighbour = partial(run_game, game_params=game_params)
            for solution, params, score in tqdm(p.imap_unordered(score_neighbour, neighbours), total=len(neighbours)):
                params['score'] = score
                writer.writerow(params)

                if score > best_solution['score']:

                    best_solution = {'solution': solution, 'params': params, 'score': score}
                    print(f'New high score found: {best_solution["score"]}')
                    terminate = False
        
        
    print(f"Hill Climbing Finished")
    print(f'Highest score found: {best_solution["score"]}')
    out_file.close()

if __name__ == "__main__":
    hill_climber()


