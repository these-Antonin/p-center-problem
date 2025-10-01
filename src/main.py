# p-center-problem/src/main.py

import argparse

from src.io_utils.read_instance import read_instance
from src.io_utils.display_instance import display_instance
from src.io_utils.display_solution import display_solution
from src.solver.solve import solve
import sys

from src.models.stratified import stratified_with_p_knowing_center_model
from src.models.stratified_utils import compute_objective, variables_unmapping
import numpy as np
from gurobipy import GRB

def main():

    # If there is an argument, use it as the instance file path
    parser = argparse.ArgumentParser(description='p-center problem and its variants solver')
    parser.add_argument('--file', nargs='?', default=None, help='Path to the instance file. If not provided, it will prompt for input.')
    
    # if it is the capacitated version, add the argument
    parser.add_argument('--capacitated', action='store_true', help='If set, the solver will handle capacitated p-center problem instances.')
    parser.add_argument('--failure', nargs='?', default=None, help='If set, the solver will handle p-center problem instances with failure foresight.')
    parser.add_argument('--stratified', nargs='?', default=None, help='If set, the solver will handle p-center problem instances with stratification.')
    args = parser.parse_args()
    
    if args.file:
        file_path = args.file
    else:
        # user input for instance file
        file_path = input("path to the instance file: ")

    alpha = 0.0  # Default value for failure foresight alpha
    if args.failure:
        alpha = float(args.failure)
        if alpha < 0 or alpha > 1:
            print("Error: alpha must be between 0 and 1.")
            sys.exit(1)

    fonction = None
    if args.stratified:
        fonction = args.stratified
        if fonction not in ["A", "B", "AB"]:
            print("Error: fonction must be 'A', 'B' or 'AB'.")
            sys.exit(1)

    # Instance reading
    is_capacitated = False
    is_failure = False
    is_stratified = False
    model_class = "classical"
    if args.failure:
        # If the instance is with failure foresight, read the failure foresight instance
        is_failure = True
        model_class = "failure"
    elif args.capacitated:
        # If the instance is capacitated, read the capacitated instance
        is_capacitated = True
        model_class = "capacitated"
    elif args.stratified:
        # If the instance is stratified, read the stratified instance
        is_stratified = True
        model_class = "stratified"
        print("Warning: Stratified model is experimental and may not work as expected.")
    
        
    instance_data = read_instance(file_path, capacitated=is_capacitated, failure=is_failure, alpha=alpha, stratified=is_stratified, fonction=fonction)

    # Problem solving
    solution = solve(instance_data, model_class=model_class)

    # Instance informations display
    # display_instance(instance_data)
    
    # Solution display
    display_solution(solution)

    if is_stratified and True:
        # take randomly p centers from the nnodes, return a list of booleans of length num_nodes

        num_centers = instance_data['num_centers']
        num_nodes = instance_data['num_nodes']
        centers = [False] * num_nodes

        # Randomly select p centers
        import random
        selected_centers = random.sample(range(num_nodes), num_centers)
        for center in selected_centers:
            centers[center] = True

        print(f"Selected centers: {selected_centers}")

        # Create the stratified model with the known centers
        model, x, w, y, A, B = stratified_with_p_knowing_center_model(instance_data, centers)
        
        model.optimize()

        if model.status == GRB.OPTIMAL or model.status == GRB.SUBOPTIMAL:
            unmapped_x, unmapped_w = variables_unmapping(instance_data, x, w)
            objective_value = compute_objective(instance_data['fonction'], A, B, instance_data['num_strata'])
            print(f"Objective value: {objective_value}")
            print(f"Centers: {[j for j in range(num_nodes) if y[j].x > 0.5]}")
            print("Primary assignments:")
            for s in range(instance_data['num_strata']):
                for i in range(num_nodes):
                    for j in range(num_nodes):
                        if unmapped_x[s, i, j] > 0.5:
                            print(f"Stratum {s}, Center {i}, Client {j}")
            print("Backup assignments:")
            for s in range(instance_data['num_strata']):
                for i in range(num_nodes):
                    for j in range(num_nodes):
                        if unmapped_w[s, i, j] > 0.5:
                            print(f"Stratum {s}, Center {i}, Client {j}")
        
    
if __name__ == "__main__":
    main()