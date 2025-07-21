import gurobipy as gp
from gurobipy import Model, GRB, quicksum
import numpy as np


def stratified_model(instance_data):

    # Extract data
    distances = instance_data['distances']
    num_nodes = instance_data['num_nodes']
    num_centers = instance_data['num_centers']
    demands = instance_data['demands']
    capacities = instance_data['capacities']
    alpha = instance_data['alpha']
    stratum = instance_data['stratum']
    stratum_center = instance_data['stratum_center']
    fonction = instance_data['fonction']
    num_strata = instance_data['num_strata']

    modele = gp.Model("pcentre strates,pannes,capacités")

    # Nombre de variables prises en compte
    nbVariables = 0
    mapping = np.zeros((num_strata, num_nodes, num_nodes))
    for s in range(num_strata): # pour chaque strate
        for i in range(num_nodes): # pour chaque centre
            for j in range(num_nodes): # pour chaque client
                if stratum[j, s] == 1 and stratum_center[i, s] == 1:
                    mapping[s, i, j] = nbVariables
                    nbVariables += 1
                else:
                    mapping[s, i, j] = -1

    # pprint.pprint(mapping)

    x = modele.addVars(nbVariables, vtype=GRB.BINARY, name="x") # premier niveau
    w = modele.addVars(nbVariables, vtype=GRB.BINARY, name="w") # second niveau
    y = modele.addVars(num_nodes, vtype=GRB.BINARY, name="y")      # assignation des centres

    
    maxDist = np.max(distances)

    A = modele.addVars(num_strata, lb=0.0, ub=maxDist, vtype=GRB.CONTINUOUS, name="A")
    B = modele.addVars(num_strata, lb=0.0, ub=maxDist, vtype=GRB.CONTINUOUS, name="B")

    # Fonction objectif

    if fonction == "AB":
        modele.setObjective(gp.quicksum(A[s] + B[s] for s in range(num_strata)), GRB.MINIMIZE)
    elif fonction == "B":
        modele.setObjective(gp.quicksum(B[s] for s in range(num_strata)), GRB.MINIMIZE)
    elif fonction == "A":
        modele.setObjective(gp.quicksum(A[s] for s in range(num_strata)), GRB.MINIMIZE)

    # Constraints
    # There is exactly p centers
    modele.addConstr(y.sum() == num_centers, "nbCentres")

    
    # Each client must be assigned to exactly one center (primary)
    for s in range(num_strata):
        for i in range(num_nodes):
            if stratum[i,s] == 1:
                expr = gp.LinExpr()
                for j in range(num_nodes):
                    if stratum_center[j,s] == 1:
                        expr += x[mapping[s,j,i]]
                modele.addConstr(expr == 1, f"assignationCentre1_{s}_{i}")

    # Each client must be assigned to exactly one backup center
    for s in range(num_strata):
        for i in range(num_nodes):
            if stratum[i,s] == 1:
                expr = gp.LinExpr()
                for j in range(num_nodes):
                    if stratum_center[j,s] == 1:
                        expr += w[mapping[s,j,i]]
                modele.addConstr(expr == 1, f"assignationCentre2_{s}_{i}")

    # Each client must be assigned to an open center (primary)
    # Each client must be assigned to an open backup center
    # Main and backup centers must be different
    for s in range(num_strata):
        for i in range(num_nodes):
            for j in range(num_nodes):
                if stratum[i,s] == 1 and stratum_center[j,s] == 1:
                    modele.addConstr(x[mapping[s,j,i]] <= y[j], f"assignationCentre1_{s}_{i}_{j}")
                    modele.addConstr(w[mapping[s,j,i]] <= y[j], f"assignationCentre2_{s}_{i}_{j}")
                    modele.addConstr(x[mapping[s,j,i]] + w[mapping[s,j,i]]<= 1, f"assignationCentre2_{s}_{i}_{j}")

    # Maximum distance constraints
    for s in range(num_strata):
        for i in range(num_nodes):
            if stratum[i,s] == 1:
                expr = gp.LinExpr()
                for j in range(num_nodes):
                    if stratum_center[j,s] == 1:
                        expr += distances[i][j] * x[mapping[s,j,i]]
                modele.addConstr(expr <= A[s])

    for s in range(num_strata):
        for i in range(num_nodes):
            if stratum[i,s] == 1:
                expr = gp.LinExpr()
                for j in range(num_nodes):
                    if stratum_center[j,s] == 1:
                        expr += distances[i][j] * w[mapping[s,j,i]]
                modele.addConstr(expr <= B[s])


    # The distance to the backup center must be at least superior or equal to the primary center distance
    for s in range(num_strata):
        for i in range(num_nodes):
            if stratum[i,s] == 1:
                expr = gp.LinExpr()
                for j in range(num_nodes):
                    if stratum_center[j,s] == 1:
                        expr += distances[i][j] * x[mapping[s,j,i]] - distances[i][j] * w[mapping[s,j,i]]
                modele.addConstr(expr <= 0)

    # Respect capacity constraints
    for s in range(num_strata):
        for j in range(num_nodes):
            if stratum_center[j,s] == 1:
                expr = gp.LinExpr()
                for i in range(num_nodes):
                    if stratum[i,s] == 1:
                        expr += demands[i][s] * (x[mapping[s,j,i]])
                modele.addConstr( expr <= capacities[j][s] *y[j])

    for s in range(num_strata):
        for j in range(num_nodes):
            if stratum_center[j,s] == 1:
                expr = gp.LinExpr()
                for i in range(num_nodes):
                    if stratum[i,s] == 1:
                        expr += demands[i][s] * (x[mapping[s,j,i]]+w[mapping[s,j,i]])
                modele.addConstr( expr <= (1+alpha[s]) * capacities[j][s] *y[j])

    return modele, x, w, y, A, B




# This function creates a model for the stratified p-center problem with known centers.
# Thus, this model do only the assignment of clients to centers.
def stratified_with_p_knowing_center_model(instance_data, centers):
    """
    Create a model for the stratified p-center problem with known centers.
    Thus we only do the assignment of clients to centers.
    Args:
        instance_data (dict): The instance data containing distances, number of nodes, etc.
        centers (boolean list): The list of known centers of size num_nodes. With True if the node is a center, False otherwise.
    Returns:
        tuple: A tuple containing the model, decision variables x, w, y, and the decision variables A, B.
    """
    # Extract data
    distances = instance_data['distances']
    num_nodes = instance_data['num_nodes']
    num_centers = instance_data['num_centers']
    demands = instance_data['demands']
    capacities = instance_data['capacities']
    alpha = instance_data['alpha']
    stratum = instance_data['stratum']
    stratum_center = instance_data['stratum_center']
    fonction = instance_data['fonction']
    num_strata = instance_data['num_strata']

    modele = gp.Model("pcentre strates,pannes,capacités")

    # Nombre de variables prises en compte
    nbVariables = 0
    mapping = np.zeros((num_strata, num_nodes, num_nodes))
    for s in range(num_strata): # pour chaque strate
        for i in range(num_nodes): # pour chaque centre
            for j in range(num_nodes): # pour chaque client
                if stratum[j, s] == 1 and stratum_center[i, s] == 1:
                    mapping[s, i, j] = nbVariables
                    nbVariables += 1
                else:
                    mapping[s, i, j] = -1

    # pprint.pprint(mapping)

    x = modele.addVars(nbVariables, vtype=GRB.BINARY, name="x") # premier niveau
    w = modele.addVars(nbVariables, vtype=GRB.BINARY, name="w") # second niveau
    y = modele.addVars(num_nodes, vtype=GRB.BINARY, name="y")      # assignation des centres

    
    maxDist = np.max(distances)

    A = modele.addVars(num_strata, lb=0.0, ub=maxDist, vtype=GRB.CONTINUOUS, name="A")
    B = modele.addVars(num_strata, lb=0.0, ub=maxDist, vtype=GRB.CONTINUOUS, name="B")

    # Fonction objectif

    if fonction == "AB":
        modele.setObjective(gp.quicksum(A[s] + B[s] for s in range(num_strata)), GRB.MINIMIZE)
    elif fonction == "B":
        modele.setObjective(gp.quicksum(B[s] for s in range(num_strata)), GRB.MINIMIZE)
    elif fonction == "A":
        modele.setObjective(gp.quicksum(A[s] for s in range(num_strata)), GRB.MINIMIZE)

    # Constraints

    # The centers are known
    for j in range(num_nodes):
        if centers[j]:
            modele.addConstr(y[j] == 1, f"centreKnown_{j}")
        else:
            modele.addConstr(y[j] == 0, f"centreKnown_{j}")

    # There is exactly p centers
    modele.addConstr(y.sum() == num_centers, "nbCentres")

    
    # Each client must be assigned to exactly one center (primary)
    for s in range(num_strata):
        for i in range(num_nodes):
            if stratum[i,s] == 1:
                expr = gp.LinExpr()
                for j in range(num_nodes):
                    if stratum_center[j,s] == 1:
                        expr += x[mapping[s,j,i]]
                modele.addConstr(expr == 1, f"assignationCentre1_{s}_{i}")

    # Each client must be assigned to exactly one backup center
    for s in range(num_strata):
        for i in range(num_nodes):
            if stratum[i,s] == 1:
                expr = gp.LinExpr()
                for j in range(num_nodes):
                    if stratum_center[j,s] == 1:
                        expr += w[mapping[s,j,i]]
                modele.addConstr(expr == 1, f"assignationCentre2_{s}_{i}")

    # Each client must be assigned to an open center (primary)
    # Each client must be assigned to an open backup center
    # Main and backup centers must be different
    for s in range(num_strata):
        for i in range(num_nodes):
            for j in range(num_nodes):
                if stratum[i,s] == 1 and stratum_center[j,s] == 1:
                    modele.addConstr(x[mapping[s,j,i]] <= y[j], f"assignationCentre1_{s}_{i}_{j}")
                    modele.addConstr(w[mapping[s,j,i]] <= y[j], f"assignationCentre2_{s}_{i}_{j}")
                    modele.addConstr(x[mapping[s,j,i]] + w[mapping[s,j,i]]<= 1, f"assignationCentre2_{s}_{i}_{j}")

    # Maximum distance constraints
    for s in range(num_strata):
        for i in range(num_nodes):
            if stratum[i,s] == 1:
                expr = gp.LinExpr()
                for j in range(num_nodes):
                    if stratum_center[j,s] == 1:
                        expr += distances[i][j] * x[mapping[s,j,i]]
                modele.addConstr(expr <= A[s])

    for s in range(num_strata):
        for i in range(num_nodes):
            if stratum[i,s] == 1:
                expr = gp.LinExpr()
                for j in range(num_nodes):
                    if stratum_center[j,s] == 1:
                        expr += distances[i][j] * w[mapping[s,j,i]]
                modele.addConstr(expr <= B[s])


    # The distance to the backup center must be at least superior or equal to the primary center distance
    for s in range(num_strata):
        for i in range(num_nodes):
            if stratum[i,s] == 1:
                expr = gp.LinExpr()
                for j in range(num_nodes):
                    if stratum_center[j,s] == 1:
                        expr += distances[i][j] * x[mapping[s,j,i]] - distances[i][j] * w[mapping[s,j,i]]
                modele.addConstr(expr <= 0)

    # Respect capacity constraints
    for s in range(num_strata):
        for j in range(num_nodes):
            if stratum_center[j,s] == 1:
                expr = gp.LinExpr()
                for i in range(num_nodes):
                    if stratum[i,s] == 1:
                        expr += demands[i][s] * (x[mapping[s,j,i]])
                modele.addConstr( expr <= capacities[j][s] *y[j])

    for s in range(num_strata):
        for j in range(num_nodes):
            if stratum_center[j,s] == 1:
                expr = gp.LinExpr()
                for i in range(num_nodes):
                    if stratum[i,s] == 1:
                        expr += demands[i][s] * (x[mapping[s,j,i]]+w[mapping[s,j,i]])
                modele.addConstr( expr <= (1+alpha[s]) * capacities[j][s] *y[j])

    return modele, x, w, y, A, B