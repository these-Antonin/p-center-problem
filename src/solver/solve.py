from gurobipy import GRB
from ..models.classical import classical_model
from ..models.capacitated import capacitated_model
from ..models.failure import failure_model
from ..models.stratified import stratified_model, variables_unmapping, compute_objective

def solve(instance_data, model_class):
    """Solve the p-center problem using the specified model class.
    Args:
        instance_data (dict): The instance data containing distances, number of nodes, etc.
        model_class (str): The model class to use : 
            'classical' for the classical p-center problem.
    Returns:
        dict: A dictionary containing the solution with objective value, gurobi status, centers, and assignments.
    Raises:
        ValueError: If the model_class is not recognized.
    """
    try:
        # Extract data from instance_data
        num_nodes = instance_data['num_nodes']
        solution = None  # Initialize solution to ensure it's always defined
        
        if model_class == 'classical': # Classical p-center problem
            model, x, y = classical_model(instance_data)
        elif model_class == 'capacitated': # Capacitated p-center problem
            model, x, y = capacitated_model(instance_data)
        elif model_class == 'failure':
            model, x, w, y = failure_model(instance_data)
        elif model_class == 'stratified':
            model, x, w, y, A, B = stratified_model(instance_data)
            num_strata = instance_data['num_strata']
        else:
            raise ValueError(f"Unknown model_class: {model_class}")

        # Optimize the model
        model.optimize()

        if (model.Status == GRB.OPTIMAL or model.Status == GRB.SUBOPTIMAL or model.Status == GRB.TIME_LIMIT) and model.SolCount > 0:
            # Extract the solution
            if model_class == 'classical' or model_class == 'capacitated':
                solution = {
                    'objective_value': model.ObjVal,
                    'gurobi_status': model.status,
                    'centers': [j for j in range(num_nodes) if y[j].x > 0.5],
                    'assignments': {i: j for i in range(num_nodes) for j in range(num_nodes) if x[i, j].X > 0.5}
                }
            elif model_class == 'failure':
                solution = {
                    'objective_value': model.ObjVal,
                    'gurobi_status': model.status,
                    'centers': [j for j in range(num_nodes) if y[j].x > 0.5],
                    'primary_assignments': {i: j for i in range(num_nodes) for j in range(num_nodes) if x[i, j].X > 0.5},
                    'backup_assignments': {i: j for i in range(num_nodes) for j in range(num_nodes) if w[i, j].X > 0.5}
                }
            elif model_class == 'stratified':
                unmapped_x, unmapped_w = variables_unmapping(instance_data, x, w)
                solution = {
                    'objective_value': compute_objective(instance_data['fonction'], A, B, num_strata),
                    'gurobi_status': model.status,
                    'centers': [j for j in range(num_nodes) if y[j].x > 0.5],
                    'primary_assignments': {(s,i) : j for s in range(num_strata) for j in range(num_nodes) for i in range(num_nodes) if unmapped_x[s,j,i] > 0.5},
                    'backup_assignments': {(s,i) : j for s in range(num_strata) for j in range(num_nodes) for i in range(num_nodes) if unmapped_w[s,j,i] > 0.5}
                }
        else:
            solution = {
                'objective_value': None,
                'gurobi_status': model.status,
                'centers': [],
                'assignments': {}
            }
        return solution
    except Exception as e:
        raise ValueError(f"An error occurred while solving the model: {e}")

    