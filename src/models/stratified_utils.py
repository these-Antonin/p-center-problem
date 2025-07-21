from gurobipy import Model, GRB, quicksum
import numpy as np

def compute_objective(fonction, A, B, num_strata):
    """
    Compute the objective value based on the function type.
    """
    if fonction == "A":
        return quicksum(A[s].X for s in range(num_strata))
    elif fonction == "B":
        return quicksum(B[s].X for s in range(num_strata))
    elif fonction == "AB":
        return quicksum(A[s].X + B[s].X for s in range(num_strata))
    else:
        raise ValueError(f"Unknown function type: {fonction}")


# This function creates a mapping of the decision variables for the stratified p-center problem.
# It is very useful, because it reduces considerably the number of variables in the model.
def variables_mapping(instance_data):
    """
    Create a mapping of the decision variables for the stratified p-center problem.
    """
    num_nodes = instance_data['num_nodes']
    num_strata = instance_data['num_strata']
    stratum = instance_data['stratum']
    stratum_center = instance_data['stratum_center']
    
    mapping = np.zeros((num_strata, num_nodes, num_nodes))
    nb_variables = 0
    
    for s in range(num_strata):  # For each stratum
        for i in range(num_nodes):  # For each center
            for j in range(num_nodes):  # For each client
                if stratum[j, s] == 1 and stratum_center[i, s] == 1:
                    mapping[s, i, j] = nb_variables
                    nb_variables += 1
                else:
                    mapping[s, i, j] = -1
                    
    return mapping, nb_variables

def variables_unmapping(instance_data, x, w):
    """
    Unmap the decision variables for the stratified p-center problem.
    """



    num_nodes = instance_data['num_nodes']
    num_strata = instance_data['num_strata']
    stratum = instance_data['stratum']
    stratum_center = instance_data['stratum_center']
    
    mapping, _ = variables_mapping(instance_data)

    x_unmapped = np.zeros((num_strata, num_nodes, num_nodes))
    w_unmapped = np.zeros((num_strata, num_nodes, num_nodes))
    
    for s in range(num_strata):
        for i in range(num_nodes):
            for j in range(num_nodes):
                if stratum[j, s] == 1 and stratum_center[i, s] == 1:
                    index = mapping[s, i, j]
                    if index != -1:
                        x_unmapped[s, i, j] = x[index].X
                        w_unmapped[s, i, j] = w[index].X
                    # x_unmapped[s, i, j] = x[mapping[s, i, j]]
                    # w_unmapped[s, i, j] = w[mapping[s, i, j]]
                    
    return x_unmapped, w_unmapped
